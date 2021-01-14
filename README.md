# poulatof

This project will be an automatic door open/close for chicken. It is based on Raspberry Pi Zero WH, Raspberry Pi OS and Python. The goal of this project is to have an electronic system power on by battery and solar panel. The door will be open at sunrise, and close at sunset. By default, HDMI, sound and Wifi are deactivated for low consumption. This system use UTC time, so no need to use any timezone.

functionalities :
- if the wifi button is set, long press start Wifi, short press stop Wifi. When Wifi is ON, a security set it OFF after 15 minutes. To connect to a Wifi network, the configuration must be set (describe in this document)
- if the wifi LED is set, blink during looking for Wifi network, ON when Wifi connected, OFF when Wifi stopped
- if the motor button is set, long press stops engine, short press reverses engine
- if the sensor up and down are set, the motor is automatically stopped when they are reached. In any case, the motor is stopped after a period of time
- When WIFI is on, a http server is started to answer to some API requests :
  * http://<ip_of_your_raspberry>:54321/UP
  * http://<ip_of_your_raspberry>:54321/DOWN
  * http://<ip_of_your_raspberry>:54321/STOP

When the program start, it check door state according to hour. And open or close door in this case. Usable when reboot.
Because most of time, this Raspberry hasn't network, a RTC (Real Time Clock) chip is added to keep date and time. Without, there is a big derivation time.
Because Wifi on Raspberry Pi Zero fall down sometimes, there is an automatic reboot if it can set ON or OFF
An optional watchdog can be set to reboot system if program is locked
A configuration describe which GPIO to use, you can update it like you want. BUT, select GPIO with pull down at startup to command the motor, otherwise your motor is turn on during boot process. See https://elinux.org/RPi_BCM2835_GPIOs to use the good GPIO. The default used is correct.

All actions describe here were done on a Linux computer, so adjust some of them for a Windows environment.

You can test it on a standard Linux computer, there is a tkinter simulator to check functionalities

## 1. Pre-requisite

If you just want to test it, there is only one need : python3

Otherwise, you'll need a Raspberry Pi and some electronics components.

## 2. Computer Linux Environment to check program

### 2.1. Python

You will use a virtual environment to not overload your system. So, you need to launch some commands before starting

```linux environment
sudo apt install python3-pip python3-venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install wheel
pip install pyephem
```

launch the command :

```start script
./door_management.sh
```

It use default chicken.json configuration file. See chapter 3.8 for explanation.


## 3. Raspberry Environment

### 3.1. Linux installation

get Raspberry Pi OS from official site : https://www.raspberrypi.org/downloads/raspberry-pi-os/
You'll use the Raspberry Pi OS (32-bit) Lite, to have minimum environment and reduce battery consumption

Insert SD card into your computer. find the SD card by the command :

```disk list
lsblk -p
NAME             MAJ:MIN RM   SIZE RO TYPE MOUNTPOINT
/dev/sda           8:0    0 298,1G  0 disk
├─/dev/sda1        8:1    0     1K  0 part
└─/dev/sda6        8:6    0 201,2G  0 part /opt
/dev/mmcblk0     179:0    0  29,5G  1 disk
└─/dev/mmcblk0p1 179:1    0  29,5G  1 part /media/antoinette/CAFE-D0D0
```

The SD card can appears in /dev/mmcblkx or /dev/sdx. install the downloaded image. In this example, you use the disk name mmcblk0

```disk size
sudo dd bs=4M if=2020-08-20-raspios-buster-armhf-lite.img of=/dev/mmcblk0 conv=fsync
```

it takes around 5 minutes

remove and install the SDcard in your computer a new time. You can now see it with 2 partitions

```look for sdcard
lsblk -p
NAME             MAJ:MIN RM   SIZE RO TYPE MOUNTPOINT
/dev/mmcblk0     179:0    0  29,5G  0 disk 
├─/dev/mmcblk0p1 179:1    0   256M  0 part /media/antoinette/boot
└─/dev/mmcblk0p2 179:2    0   1,5G  0 part /media/antoinette/rootfs
```

You have to set a minimum of parameters before inserting it in a Raspberry Pi Zero, because it has only WIFI connection. This action must be done with sudo

```activate ssh wifi
cd /media/antoinette/boot
sudo printf "" > ssh

sudo vi wpa_supplicant.conf
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=FR

network={
    ssid="Poupoule38"
    psk="essai9876543210"
}
```

The first command create an empty file with name ssh. The second command vi create a file wpa_supplicant.conf. Both files will be used at startup to configure the Raspberry

now, you are ready to insert this SD card into Raspberry Pi, and continue to configure it. Don't forget to umount it before extract it.

```umount sdcard
cd
sudo umount /dev/mmcblk0p2 /dev/mmcblk0p1
```

### 3.2. Linux configuration

start your Raspberry Pi. Normally, it will connect to your Wifi network. You can now connect to it with the default user pi. Example with address 192.168.20.100

```connect to
ssh pi@192.168.20.100
```

The default password is raspberry. If it doesn't work, you are probably in english language, so password will be : rqspberry

configure the system by using command

```config raspberry
sudo raspi-config
```

set French keyboard
```keyboard
-> Localisation options
  -> change keyboard layout
```
set local
```localization
-> Localisation options
  -> change Locale
```
set TZ
```timezone
-> Localisation options
  -> change Time Zone
```
change hostname
```hostname
-> Network Options
  -> Hostname
```

To preserve your SD card, you set somes directories in tmpfs (it use memory). It is important to set /tmp in tmpfs because all temporary files doesn't use SD card !

you add these lines into /etc/fstab
```fstab
tmpfs   /tmp            tmpfs   defaults 0      0
tmpfs   /var/log        tmpfs   defaults 0      0
```

### 3.3. Linux security

#### 3.3.1. Wifi security

You now set some configurations to improve security

update the Wifi password by encrypted string, by using the command : wpa_passphrase

You use the same information like previously to configure your network
```network
wpa_passphrase Poupoule38 essai9876543210
network={
    ssid="Poupoule38"
    #psk="essai9876543210"
    psk=42e0cbad9fbf93502493dc6c51f951b621f5131906162238e140fa44839b7798
}
```

You can now update the file /etc/wpa_supplicant/wpa_supplicant.conf and change the previous chapter network by this generated. And remove the comment line starting by #. Thus, your password is not included in the sdcard.

<b>Note, that if you change password or SSID</b> in this file with a new one, you have to launch next command to reconfigure the WIFI:

```reconfigure
sudo wpa_cli -i wlan0 reconfigure
```

#### 3.3.2. ssh security

You will now generate certificates, to allow only some computer to connect to it.
The next command generates in $HOME/.ssh directory the files : id_rsa (private key), id_rsa.pub (public key). Keep default option.

```ssh key
ssh-keygen -b 4096
```

You'll see in the next chapter how to improve security with certificates

#### 3.3.3. user security

You'll now change the default user name : pi

Activate the root account by setting a password

```root user
sudo passwd root
```

allow ssh root connection. Update file /etc/ssh_config/sshd_config, and add or update line:
```allow root
PermitRootLogin yes
```

Then, restart ssh services

```restart service
sudo /etc/init.d/ssh restart
[ ok ] Restarting ssh (via systemctl): ssh.service.
```

disconnect all pi user, and connect to root

```change user
ssh root@192.168.20.100
usermod --login antoinette --home /home/antoinette --move-home pi
```

In this example, the pi user is changed by antoinette. Once done, disconnect an connect to your new user

```connect to new user
ssh antoinette@192.168.20.100
```

remove root password in /etc/shadow. Change the root line, set star (*) between the first two colons (:)

```remove root password
root:*:18545:0:99999:7:::
```

change default user password

```default user
passwd antoinette
```

change default port for SSH. Edit file /etc/ssh/sshd_config and uncomment line port to set your port. Example :

```ssh port
Port 10022
```

If you want to add more security, you can add the certificate of your Linux machine, and set a very difficult password for your default user.

Your Linux machine contains a public key into $HOME/.ssh (if you generate it by ssh-keygen). You just have to put this public key of your machine to the raspberry. Example with SSH port 10022, user antoinette, and IP address 192.168.20.100 of your Raspberry

```send public key
scp -P 10022 -p $HOME/.ssh/id_rsa.pub antoinette@192.168.20.100:~/.ssh/authorized_keys
```

After that, your computer is allowed to connect to your Raspberry without passwd. 

You can add another computer, in this case, you have to edit the Raspberry file ~/.ssh/authorized_keys and add manually the public key.

### 3.4. Linux optimization

In this chapter, you'll disable some services to consume less and less energy

disable sound equipment

```disable equipment
echo "blacklist snd_bcm2835" |sudo tee /etc/modprobe.d/blacklist-sound.conf
```

disable ACT led and HDMI. You'll have to update file /etc/rc.local. Add the lines (in this example with vi) just before the exit command

```disable LED HDMI
sudo vi /etc/rc.local

echo none | tee /sys/class/leds/led0/trigger
echo 1 | tee /sys/class/leds/led0/brightness

tvservice -o
```

### 3.5. RTC module

Because the Raspberry Pi clock is bad, and we want a system which works without network connection, we add the RTC module DS3231. You can select a model with simple battery or rechargeable battery 2032

Once installed, activate I2C port

```i2c config
sudo raspi-config
5 - interfacing option
P5 - I2C
```

Install next packages

```RTC package
sudo apt-get install python-smbus
sudo apt-get install i2c-tools
```

And check port
```check hardware
sudo i2cdetect -y 1

     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
50: -- -- -- -- -- -- -- 57 -- -- -- -- -- -- -- --
60: -- -- -- -- -- -- -- -- 68 -- -- -- -- -- -- --
70: -- -- -- -- -- -- -- --
```

the port 68 must appear

configure system to use it

```configure RTC
echo ds3231 0x68 | sudo tee /sys/class/i2c-adapter/i2c-1/new_device
ds3231 0x68
```

check RTC module value

```get RTC clock
sudo hwclock
2000-01-01 01:16:32.951079+01:00
```

write current date and check it

```set RTC clock
date
Mon Dec 25 00:00:07 CET 2020

sudo hwclock -w

sudo hwclock
2020-12-25 00:00:07.732169+01:00
```

update /etc/rc.local to configure RTC at startup. Don't forget a sudo before hwclock, otherwise it doesn't work, but I don't know why !
```get RTC at startup
vi /etc/rc.local

echo ds3231 0x68 > /sys/class/i2c-adapter/i2c-1/new_device
sudo hwclock -s
```

deactivate fake service which simulate clock

```deactivate fake rtc
sudo update-rc.d fake-hwclock disable
sudo update-rc.d ntp disable
```

### 3.6. Software installation

In the current directory, you'll find a script named : save.sh

launch it, it generate a file : ../door_management.tgz

You just have to send it to your Raspberry, and extract it where you want, for example:

send it to /tmp with previous configuration to the Raspberry

```package transfer
scp -P 10022 ../door_management.tgz antoinette@my_chicken_raspberry:/tmp
```

and in Raspberry, extract it in HOME directory :

```package install
cd
tar xf /tmp/door_management.tgz
```

### 3.7. Python

You will use a virtual environment to not overload your system. So, you need to launch some commands before starting

```python config
sudo apt install python3-pip python3-venv python3-gpiozero
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install wheel
pip install gpiozero
pip install RPi.GPIO
pip install pyephem
```

### 3.8. commands with root privilege

Because we have change default user, the sudo command without password is deactivated. To restore it, go to /etc/sudoers.d, and edit the file 010_pi-nopasswd.

It contains only one line:

```look for root privilege
pi ALL=(ALL) NOPASSWD: ALL
```

change the name pi by your new user name, in our example antoinette. The content become:

```set root privilege
antoinette ALL=(ALL) NOPASSWD: ALL
```

### 3.9. program configuration

This program uses default configuration file chicken.json. You can change it with option -c.

the configuration file looks like:

```package configuration
{
  "wifi_button_gpio": 23,
  "motor_button_gpio": 24,
  "motor_forward_gpio": 9,
  "motor_backward_gpio": 25,
  "door_closed_gpio": 6,
  "door_opened_gpio": 5,
  "wifi_led_gpio": 21,
  "motor_timeout": 25,
  "wifi_timeout": 20,
  "wifi_at_startup": false,
  "longitude": "2.294270",
  "latitude": "48.858823",
  "log_level": "debug",
  "log_file": "/tmp/automatic_door.log",
  "security_time": 2700,
  "wifi_script": "./wifi_control.sh",
  "wifi_interface": "wlp1s0",
  "user_mail": "poulatof@gmail.com",
  "destination_mail": "red.fox@gmail.com",
  "password_mail": "machine_password",
  "csv_report": false
}
```

mandatory parameters are :
- <b>motor_forward_gpio</b>
- <b>motor_backward_gpio</b>

The minimum action is to commmand the motor :)

if <b>wifi_button_gpio</b> is present, it needs <b>wifi_script</b>. if <b>wifi_interface</b> doesn't exist, it use wlan0. When activate Wifi by button, the program wait <b>wifi_timeout</b> to check if it is connected. If not, it stop it. if <b>wifi_led_gpio</b> exists, the Led blink during startup, is on when Wifi is connected, and off when Wifi disconnected.

if <b>wifi_at_startup</b> exists, it stop Wifi at startup if value is false

if <b>door_closed_gpio</b> and/or <b>door_open_gpio</b> exist, it corresponds to sensor which detect door at the top or bottom. In this case, the motor is stopped. Otherwise, a timeout is used <b>motor_timeout</b>. Default value is 20 seconds. According to your installation, you'll be able to swap GPIO value closed and opened. Select GPIO with pull up at startup.

if <b>motor_button_gpio</b> exists, you can start/stop the door manually

if <b>security_time</b> exists, it add these seconds to the sunset time. To be sur our chicken are in home. Default value is 1800 seconds

<b>longitude</b> and <b>latitude</b> are used to calculate sunset and sunrise. If absent, use default Eiffel tower position.

if <b>log_level</b> exists, it configure the log level : debug, info, warning, error. Default is warning.

if <b>log_file</b> exists, it generates 5 rolling files of 100ko.

if <b>user_mail</b> and <b>destination_mail</b> exist, the software is ready to send email each time the Wifi is activated. In this case, you can set the user_mail password by using two options:
- set it into <b>password_mail</b> key in the configuration file
- update in the source elements/email_sender.py the line:

```gmail password
password = "gmail_appli_passwd"
```
Thus, it's a little bit more complicated to find it ;)

if <b>csv_report</b> is true, the report has comma separator. Otherwise, it seems a text table

So, when email is activated, each time you activate Wifi, you receive a report. And the log rotates, so you don't receive it twice. Here is a text example:
```report
+---------------------+-------+
| 2020-10-23 19:23:32 | close |
| 2020-10-24 08:04:59 | open  |
| 2020-10-24 19:21:56 | close |
| 2020-10-25 07:06:20 | open  |
| 2020-10-25 18:20:22 | close |
| 2020-10-26 07:07:41 | open  |
+---------------------+-------+
```
This case shows the time change the 2020-10-25 :)


### 3.10. email configuration

To use the email mechanism, you have to create a google account with an application password:
https://support.google.com/accounts/answer/185833?hl=en

```email configuration
create google account
activate 2 step verification
   go to manage you google account
   Security
   Signing in to Google
   2-Step verification
      Add your phone number

Once done, return to this menu, you have a new option
   go to manage you google account
   Security
   Signing in to Google
   Add passwords
      You have to set a machine type, a name, and it generate a long password
```

You can now use it in your python mail script to connect to the gmail account to send email

### 3.11. automatic start

Now, all is fine. You just have to launch the program at startup. You have to simply add a new line in /etc/rc.local. Add the line (in this example with vi) just before the exit command


```automatic start
sudo vi /etc/rc.local
su antoinette -c /home/antoinette/door_daemon.sh
```

In this example, antoinette is the user, don't forget to use the name you set.

### 3.12. watchdog

The program writes every 5 minutes the file /tmp/watchdog_hen.txt, which contains the time in second
This package is provided with the file : watchdog.sh

You just have to configure the root crontab each 5 minutes with this script, which checks the value of /tmp/watchdog_hen.txt with the current time. If there is more than 15 minutes, it considers the program is out. And reboot the system

```watchdog
crontab -l 2>/dev/null > /tmp/current_cron
echo "5 * * * * $HOME/watchdog.sh" >> /tmp/current_cron
crontab /tmp/current_cron

crontab -l
5 * * * * /home/antoinette/watchdog.sh
```

You can check the configuration by this command 

```check watchdog
crontab -l
5 * * * * /home/antoinette/watchdog.sh
```

## 4. The ultimate configuration

When all is ready, you just have to configure the Wifi network of your Raspberry with the shared Wifi of your smartphone. Then, system is working on its own. And when you want to have a resume, you just have to activate your shared Wifi, press Wifi button of this system, and you'll receive the last actions.

## 5. The complete configuration files

### 5.1. /etc/rc.local

```rc.local
#!/bin/sh -e

echo none | tee /sys/class/leds/led0/trigger
echo 0 | tee /sys/class/leds/led0/brightness

tvservice -o

# activation du RTC
echo ds3231 0x68 > /sys/class/i2c-adapter/i2c-1/new_device
sudo hwclock -s

# create watch dog time file, if program abort
date -u '+%s' > /tmp/watchdog_hen.txt
chown antoinette:pi /tmp/watchdog_hen.txt

su antoinette -c /home/antoinette/door_daemon.sh

exit 0
```

### 5.2. /etc/sudoers.d/010_antoinette-nopasswd

```sudoers
antoinette ALL=(ALL) NOPASSWD: ALL
```

### 5.3. /etc/wpa_supplicant/wpa_supplicant.conf

```wifi config
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=FR

network={
    ssid="Poupoule38"
    psk=0f6df8f157cb65a171d2769d9d4961bfe2756d561983dd12bc04563977ba690d
}
```

### 5.4. /etc/fstab

```fstab
proc            /proc           proc    defaults          0       0
PARTUUID=1c481aad-01  /boot           vfat    defaults          0       2
PARTUUID=1c481aad-02  /               ext4    defaults,noatime  0       1

tmpfs	/tmp		tmpfs	defaults 0	0
tmpfs	/var/log	tmpfs	defaults 0	0
```

### 5.5. /etc/modprobe.d/blacklist-sound.conf

```sound
blacklist snd_bcm2835
```








