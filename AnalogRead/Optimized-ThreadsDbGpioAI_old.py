"""
    Setup the Home Hub for use in the Powernet system

    Implementation of multi threading based of:
    https://www.troyfawkes.com/learn-python-multithreading-queues-basics/

    OBS: Yuting's load model: real power at <=1min
"""
__author__ = 'Gustavo Cezar'
__copyright__ = 'Stanford University'
__version__ = '0.1'
__email__ = 'gcezar@stanford.edu'
__status__ = 'Prototype'

import beaglebone_pru_adc as adc
import Adafruit_BBIO.GPIO as GPIO
import math
import time
import copy
import requests
import logging

from Queue import Queue
from raven import Client
from threading import Thread
from datetime import datetime
from firebase import Firebase as fb
from logging.handlers import RotatingFileHandler

# Global variables
N_SAMPLES = 100
CONVERTION = 1.8/4095.0
REQUEST_TIMEOUT = 10
FB_API_BASE_URL = 'https://fb-powernet.firebaseio.com/'
PWRNET_API_BASE_URL = 'http://pwrnet-158117.appspot.com/api/v1/'
SENTRY_DSN = 'https://e3b3b7139bc64177b9694b836c1c5bd6:fbd8d4def9db41d0abe885a35f034118@sentry.io/230474'

# Logger setup for a rotating file handler
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('my_log.log', maxBytes=2000, backupCount=10)
logger.addHandler(handler)

# Sentry setup for additional error reporting via 3rd party cloud service
client = Client(SENTRY_DSN)

# Initializing Firebase
pwr_firebase = fb(FB_API_BASE_URL + 'ApplianceTest09')

# Initializing GPIOs:
appliance_lst = ["PW1", "RA1", "AC1", "DR1", "RF1", "SE1"]
gpio_map = {"PW1": "P8_9", "RA1": "P8_10", "AC1": "P8_15",
            "DR1": "P8_12", "RF1": "P8_14", "SE1": "P8_11"}

for key in gpio_map:
    GPIO.setup(gpio_map[key], GPIO.OUT)
    GPIO.output(gpio_map[key], GPIO.HIGH)


def analog_read(off_value):
    """
        Analog Reading
    """
    # logger('Analog read called')
    capture = adc.Capture()
    capture.cap_delay = 50000
    capture.oscilloscope_init(adc.OFF_VALUES + off_value, N_SAMPLES)
    capture.start()

    while not capture.oscilloscope_is_complete():
        False  # This is a dumb condition just to keep the loop running

    capture.stop()
    capture.wait()
    capture.close()
    return capture.oscilloscope_data(N_SAMPLES)


def producer_ai(format_ai, q_ai):
    """
        Producer AI
    """
    logger.info('Producer AI called')
    while(True):
        dts = []  # date/time stamp for each start of analog read

        dts.append(str(datetime.now()))
        ai0 = analog_read(format_ai[0])

        dts.append(str(datetime.now()))
        ai1 = analog_read(format_ai[1])

        dts.append(str(datetime.now()))
        ai2 = analog_read(format_ai[2])

        temp_ai = zip(ai0, ai1, ai2)
        temp_queue = [temp_ai, dts]

        # logger('Adding AI to the queue')

        try:
            q_ai.put(temp_queue, True, 2)

        except Exception as exc:
            logger.exception(exc)
            client.captureException()

        time.sleep(2)


def RMS(data):
    """
        Current RMS calculation for consumer_ai
    """
    # The size of sum_i is the size of the AIN ports
    sum_i = [0, 0, 0]
    for val in data:
        sum_i[0] += math.pow((val[0] * CONVERTION - 0.89), 2)
        sum_i[1] += math.pow((val[1] * CONVERTION - 0.89), 2)
        sum_i[2] += math.pow((val[2] * CONVERTION - 0.89), 2)

    rms_a0 = math.sqrt(sum_i[0] / N_SAMPLES)
    rms_a1 = math.sqrt(sum_i[1] / N_SAMPLES)
    rms_a2 = math.sqrt(sum_i[2] / N_SAMPLES)

    return [rms_a0, rms_a1, rms_a2]


def consumer_ai(q_ai):
    """
        Consumer AI
    """
    logger.info('Consumer AI called')
    template = [
        {
            "sensor_id": 1,
            "samples": []
        }, {
            "sensor_id": 2,
            "samples": []
        }, {
            "sensor_id": 3,
            "samples": []
        }
    ]

    d_fb = copy.deepcopy(template)

    while(True):
        if not q_ai.empty():
            try:
                temp_cons = q_ai.get(True,2)
                temp_ai = temp_cons[0]
                temp_date = temp_cons[1]

                i_rms = RMS(temp_ai[1:])

                # Adding analog reads, sID and Date to lists for db upload
                d_fb[0].get("samples").append({"RMS": i_rms[0], "date_time": temp_date[0]})
                d_fb[1].get("samples").append({"RMS": i_rms[1], "date_time": temp_date[1]})
                d_fb[2].get("samples").append({"RMS": i_rms[2], "date_time": temp_date[2]})

                # Queue is done processing the element
                q_ai.task_done()

                if len(d_fb[1]["samples"]) == 10:
                    try:
                        # send the request to the powernet site instead of firebase
                        r_post_rms = requests.post(PWRNET_API_BASE_URL + "rms/", json={'devices_json': d_fb}, timeout=REQUEST_TIMEOUT)

                        if r_post_rms.status_code == 201:
                            # logger.info("Request was successful")
                            pass
                        else:
                            logger.exception("Request failed")
                            r_post_rms.raise_for_status()

                        d_fb[:]=[]
                        d_fb = None
                        d_fb = copy.deepcopy(template)

                    except Exception as exc:
                        logger.exception(exc)
                        client.captureException()

                        d_fb[:]=[]
                        d_fb = None
                        d_fb = copy.deepcopy(template)

            except Exception as exc:
                logger.exception(exc)
                client.captureException()


def relay_act(device, state):
    """
        Reading if there is any input for the relay
    """
    GPIO.output(gpio_map[device], GPIO.LOW if state == 'ON' else GPIO.HIGH)


def relay_th():
    """
        Relay Status
    """

    logger.info('Relay Thread called')

    # Appliances ID:
    #     id:1 ; Powerwall_1
    #     id:2 ; Powerwall_2
    #     id:3 ; Range_1
    #     id:4 ; Range_2
    #     id:5 ; AC_1
    #     id:6 ; AC_2

    app_orig_states = ["OFF", "OFF", "OFF", "OFF", "OFF", "OFF"]
    app_new_status = ["OFF", "OFF", "OFF", "OFF", "OFF", "OFF"]

    while(True):
        try:
            AC_1 = requests.get(PWRNET_API_BASE_URL + "device/5", timeout=REQUEST_TIMEOUT)
            status_AC1 = AC_1.json()["status"]

        except Exception as exc:
            logger.exception(exc)
            client.captureException()
            status_AC1 = app_new_status[2]

        try:
            SE_1 = requests.get(PWRNET_API_BASE_URL + "device/12", timeout=REQUEST_TIMEOUT)
            status_SE1 = SE_1.json()["status"]

        except Exception as exc:
            logger.exception(exc)
            client.captureException()
            status_SE1 = app_new_status[5]

        app_new_status = ["OFF", "OFF", status_AC1, "OFF", "OFF", status_SE1]
        for index, (first, second) in enumerate(zip(app_orig_states, app_new_status)):
            if first != second:
                relay_act(appliance_lst[index], second)
                app_orig_states = copy.deepcopy(app_new_status)

        time.sleep(2)


def main():
    """
        Main entry point into the Home Hub system operation

        Detailed description:

    """
    # Initializing variables for queue and threads
    buffer_size = 7
    q_ai = Queue(buffer_size)

    # FIXME: Number of analog inputs -> Needs to be automated
    n_ai = 3
    format_ai = [i * 4 for i in range(n_ai)]

    # Initialize threads
    producer_ai_thread = Thread(name='Producer',target=producer_ai, args=(format_ai, q_ai))
    producer_ai_thread.start()

    consumer_ai_thread = Thread(name='Consumer',target=consumer_ai, args=(q_ai,))
    consumer_ai_thread.start()

    relay_thread = Thread(name='Relay',target=relay_th)
    relay_thread.start()


if __name__ == '__main__':
    try:
        logger.info("Starting main program")
        main()
    except Exception as exc:
        logger.exception(exc)
        client.captureException()
        logger.info("Re-starting main program")
        main()
