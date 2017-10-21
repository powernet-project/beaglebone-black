# Beaglebone Black - HH - prototype - v1.0
We are finally standardizing this.

WIP

When running code from ssh run (this code will make sure when you terminate the ssh session the code still runs on BBB):
nohup python <filename> & exit

Connecting to Wifi:
run: wicd-curses
(skip next step if BBB is already "basic configured")
press: Shift-p; (go to preferences and put wlan0 - or whatever port your dongle was detected)
press: F10; to save and exit
press: shift-R; to refresh all networks
Select wifi (right arrow) and insert password

Creating virtual environment and cloning repo:
run: pip install virtualenv
run: virtualenv --no-site-packages <venv_NAME>
With venv active:
run: pip install -r requirements.txt
run: pip install requests --upgrade


When hooking up a new BBB to your computer and trying to ssh you might get an error like this:
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
Someone could be eavesdropping on you right now (man-in-the-middle attack)!
It is also possible that a host key has just been changed.

Enter this command to solve the problem (my user path is: Users/mycomputername):
ssh-keygen -f "/YOUR_USER_PATH/.ssh/known_hosts" -R 192.168.7.2




--------- OLD NOTES ---------
Note:
Be sure to create a virtual environment before copying the repo.
In a brand new BBB:
run: pip install virtualenv
run: virtualenv <venv_NAME> (for the name we are using venv_BBB)
