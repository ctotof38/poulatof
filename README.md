# poulatof

This project will be an automatic door open/close for chicken. It is based on Raspberry Pi Zero WH, Raspberry Pi OS and Python. The goal of this project is to have an electronic system power on by battery and solar panel. The door will be open at sunrise, and close at sunset. By default, HDMI, sound and Wifi are deactivated for low consumption. This system use UTC time according to GNSS position, so no need to use any timezone.

functionalities :
- if the wifi button is set, long press start Wifi, short press stop Wifi. When Wifi is on, a security set it off after 15 minutes. To connect to a Wifi network, the configuration must be set (describe in this document)
- if the wifi LED is set, blink during looking for Wifi network, on when Wifi connected, off when Wifi stopped
- if the motor button is set, three quickly press stops engine, short press reverses engine, and long press ready for a specific action (not defined currently)
- if the sensor up and down are set, the motor is automatically stopped when it is reached. In any case, the motor is stopped after a period of time
- When WIFI is on, a http server is started to answer to some API requests :
  * http://<ip_of_your_raspberry>:54321/UP
  * http://<ip_of_your_raspberry>:54321/DOWN
  * http://<ip_of_your_raspberry>:54321/STOP

Because most of time, this Raspberry hasn't network, a RTC (Real Time Clock) chip is added to keep date and time.

All actions describe here were done on a Linux computer, so adjust some of them for a Windows environment.

You can test it on a standard Linux computer, there is a tkinter simulator to check functionalities

## 1. Pre-requisite

If you just want to test it, there is only one need : python3

Otherwise, you'll need a Raspberry Pi and some electronics components.

## 2. standard Linux Environment

### 2.1. Python

You will use a virtual environment to not overload your system. So, you need to launch some commands before starting

```yaml
sudo apt install python3-pip python3-venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install wheel
pip install pyephem
```

launch the command :

```yaml
./door_management.sh
```

It use default chicken.json configuration file. See chapter 3.8 for explanation.


## 3. Raspberry Environment

### 3.1. Linux installation

get Raspberry Pi OS from official site : https://www.raspberrypi.org/downloads/raspberry-pi-os/
You'll use the Raspberry Pi OS (32-bit) Lite, to have minimum environment and reduce battery consumption

Insert SD card into your computer. find the SD card by the command :

```yaml
lsblk -p
NAME             MAJ:MIN RM   SIZE RO TYPE MOUNTPOINT
/dev/sda           8:0    0 298,1G  0 disk
├─/dev/sda1        8:1    0     1K  0 part
└─/dev/sda6        8:6    0 201,2G  0 part /opt
/dev/mmcblk0     179:0    0  29,5G  1 disk
└─/dev/mmcblk0p1 179:1    0  29,5G  1 part /media/totof/CAFE-D0D0
```

The SD card can appears in /dev/mmcblkx or /dev/sdx. install the downloaded image. In this example, you use the disk name mmcblk0

```yaml
sudo dd bs=4M if=2020-08-20-raspios-buster-armhf-lite.img of=/dev/mmcblk0 conv=fsync
```

it takes around 5 minutes

remove and install the SDcard in your computer a new time. You can now see it with 2 partitions

```yaml
lsblk -p
NAME             MAJ:MIN RM   SIZE RO TYPE MOUNTPOINT
/dev/mmcblk0     179:0    0  29,5G  0 disk 
├─/dev/mmcblk0p1 179:1    0   256M  0 part /media/totof/boot
└─/dev/mmcblk0p2 179:2    0   1,5G  0 part /media/totof/rootfs
```

You have to set a minimum of parameters before inserting it in a Raspberry Pi Zero, because it has only WIFI connection. This action must be done with sudo

```yaml
cd /media/totof/boot
sudo printf "" > ssh

sudo vi wpa_supplicant.conf
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=FR

network={
     ssid="gandalf"
     psk="it's the wizard!"
}
```

The first command create an empty file with name ssh. The second command vi create a file wpa_supplicant.conf. Both files will be used at startup to configure the Raspberry

now, you are ready to insert this SD card into Raspberry Pi, and continue to configure it. Don't forget to umount it before extract it.

```yaml
cd
sudo umount /dev/mmcblk0p2 /dev/mmcblk0p1
```

### 3.2. Linux configuration

start your Raspberry Pi. Normally, it will connect to your Wifi network. You can now connect to it with the default user pi. Example with address 192.168.20.100

```yaml
ssh pi@192.168.20.100
```

The default password is raspberry. If it doesn't work, you are probably in english language, so password will be : rqspberry

configure the system by using command

```yaml
sudo raspi-config
```

set French keyboard
```yaml
-> Localisation options
  -> change keyboard layout
```
set local
```yaml
-> Localisation options
  -> change Locale
```
set TZ
```yaml
-> Localisation options
  -> change Time Zone
```
change hostname
```yaml
-> Network Options
  -> Hostname
```

To preserve your SD card, you set somes directories in tmpfs (it use memory)

you add these lines into /etc/fstab
```yaml
tmpfs   /tmp            tmpfs   defaults 0      0
tmpfs   /var/log        tmpfs   defaults 0      0
```

### 3.3. Linux security

#### 3.3.1. Wifi security

You now set some configurations to improve security

update the Wifi password by encrypted string, by using the command : wpa_passphrase

You use the same information like previously to configure your network
```yaml
wpa_passphrase gandalf "it's the wizard!"

network={
   ssid="gandalf"
   #psk="it's the wizard!"
   psk=0f6df8f157cb65a171d2769d9d4961bfe2756d561983dd12bc04563977ba690d
}
```

You can now update the file /etc/wpa_supplicant/wpa_supplicant.conf and change the previous chapter network by this generated. And remove the comment line starting by #. Thus, your password is not included in the sdcard.

<b>Note, that if you change password or SSID</b> in this file with a new one, you have to launch next command to reconfigure the WIFI:

```yaml
sudo wpa_cli -i wlan0 reconfigure
```yaml

#### 3.3.2. ssh security

You will now generate certificates, to allow only some computer to connect to it.
The next command generates in $HOME/.ssh directory the files : id_rsa (private key), id_rsa.pub (public key). Keep default option.

```yaml
ssh-keygen -b 4096
```

You'll see in the next chapter how to improve security with certificates

#### 3.3.3. user security

You'll now change the default user name : pi

Activate the root account by setting a password

```yaml
sudo passwd root
```

allow ssh root connection. Update file /etc/ssh_config/sshd_config, and add or update line:
```yaml
PermitRootLogin yes
```

Then, restart ssh services

```yaml
sudo /etc/init.d/ssh restart
[ ok ] Restarting ssh (via systemctl): ssh.service.
```

disconnect all pi user, and connect to root

```yaml
ssh root@192.168.20.100
usermod --login totof --home /home/totof --move-home pi
```

In this example, the pi user is changed by totof. Once done, disconnect an connect to your new user

```yaml
ssh totof@192.168.20.100
```

remove root password in /etc/shadow. Change the root line, set star (*) between the first two colons (:)

```yaml
root:*:18545:0:99999:7:::
```

change default user password

```yaml
passwd totof
```

change default port for SSH. Edit file /etc/ssh/sshd_config and uncomment line port to set your port. Example :

```yaml
Port 10022
```

If you want to add more security, you can add the certificate of your Linux machine, and set a very difficult password for your default user.

Your Linux machine contains a public key into $HOME/.ssh (if you generate it by ssh-keygen). You just have to put this public key of your machine to the raspberry. Example with SSH port 10022, user totof, and IP address 192.168.20.100 of your Raspberry

```yaml
scp -P 10022 -p $HOME/.ssh/id_rsa.pub totof@192.168.20.100:~/.ssh/authorized_keys
```

After that, your computer is allowed to connect to your Raspberry without passwd. 

You can add another computer, in this case, you have to edit the Raspberry file ~/.ssh/authorized_keys and add manually the public key.

### 3.4. Linux optimization

In this chapter, you'll disable some services to consume less and less energy

disable sound equipment

```yaml
echo "blacklist snd_bcm2835" |sudo tee /etc/modprobe.d/blacklist-sound.conf
```

disable ACT led and HDMI. You'll have to update file /etc/rc.local

```yaml
sudo vi /etc/rc.local

echo none | tee /sys/class/leds/led0/trigger
echo 1 | tee /sys/class/leds/led0/brightness

tvservice -o
```

### 3.5. Software installation

In the current directory, you'll find a script named : save.sh

launch it, it generate a file : ../door_management.tgz

You just have to send it to your Raspberry, and extract it where you want, for example:

send it to /tmp with previous configuration to the Raspberry

```yaml
scp -P 10022 ../door_management.tgz totof@my_chicken_raspberry:/tmp
```

and in Raspberry, extract it in HOME directory :

```yaml
cd
tar xf /tmp/door_management.tgz
```

### 3.6. Python

You will use a virtual environment to not overload your system. So, you need to launch some commands before starting

```yaml
sudo apt install python3-pip python3-venv python3-gpiozero
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install wheel
pip install gpiozero
pip install RPi.GPIO
pip install pyephem
```

### 3.7. commands with root privilege

The current program is able to activate/deactivate Wifi. So, it needs to use the ifconfig command with root privilege.

To run some sudo command from your python script without password, create a file in the directory /etc/sudoers.d to describe allowed admin commands without password

For example, /etc/sudoers.d/011_totof-nopasswd . This example describes admin user (ADMIN), admin commands (ADMIN_CMDS) and all the admin user to run admin commands without passwd

```yaml
# User alias specification
User_Alias ADMIN = totof

# Cmnd alias specification
Cmnd_Alias ADMIN_CMDS = /sbin/ifconfig

# Allow members of group sudo to execute any command
ADMIN   ALL=(root) NOPASSWD: ADMIN_CMDS
```

### 3.8. program configuration

This program uses default configuration file chicken.json. You can change it with option -c.

the configuration file looks like:

```yaml
{
  "wifi_button_gpio": 23,
  "motor_button_gpio": 24,
  "motor_forward_gpio": 4,
  "motor_backward_gpio": 14,
  "door_closed_gpio": 5,
  "door_opened_gpio": 6,
  "wifi_led_gpio": 10,
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

if <b>door_closed_gpio</b> and/or <b>door_open_gpio</b> exist, it corresponds to sensor which detect door at the top or bottom. In this case, the motor is stopped. Otherwise, a timeout is used <b>motor_timeout</b>. Default value is 20 seconds

if <b>motor_button_gpio</b> exists, you can start/stop the door manually

if <b>security_time</b> exists, it add these seconds to the sunset time. To be sur our chicken are in home. Default value is 1800 seconds

<b>longitude</b> and <b>latitude</b> are used to calculate sunset and sunrise. If absent, use default Eiffel tower position.

if <b>log_level</b> exists, it configure the log level : debug, info, warning, error. Default is warning.

if <b>log_file</b> exists, it generates 5 rolling files of 100ko.

if <b>user_mail</b> and <b>destination_mail</b> exist, the software is ready to send email each time the Wifi is activated. In this case, you can set the user_mail password by using two options:
- set it into <b>password_mail</b> key in the configuration file
- update in the source elements/email_sender.py the line:

```yaml
password = "gmail_appli_passwd"
```
Thus, it's a little bit more complicated to find it ;)

if <b>csv_report</b> is true, the report has comma separator. Otherwise, it seems a text table

So, when email is activated, each time you activate Wifi, you receive a report. And the log rotates, so you don't receive it twice. Here is a text example:
```yaml
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


### 3.9. email configuration

To use the email mechanism, you have to create a google account with an application password:
https://support.google.com/accounts/answer/185833?hl=en

```yaml
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

### 3.10. automatic start

Now, all is fine. You just have to launch the program at startup. You have to simply add a new line in /etc/rc.local


```yaml
sudo vi /etc/rc.local
su totof -c /home/totof/door_daemon.sh
```

In this example, totof is the user, don't forget to use the name you set.

## 4. The ultimate configuration

When all is ready, you just have to configure the Wifi network of your Raspberry with the shared Wifi of your smartphone. Then, system is working on its own. And when you want to have a resume, you just have to active your shared Wifi, press Wifi button of this system, and you'll receive the last actions.

If you are a little nervous with autonomous system, you can add in the root crontab a reboot machine each X days. But you lose your report.





