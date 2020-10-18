# poulatof

This project will be an automatic door open/close for chicken. It is based on Raspberry Pi Zero W, Raspberry Pi OS and Python. The goal of this project is to have an electronic system power on by battery and solar panel. And the door will be open at sunrise, and close at sunset.

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

You now set somes configuration to improve security

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

You can now update the file /etc/wpa_supplicant/wpa_supplicant.conf and change the previous chapter network by those generated. And remove the comment line starting by #. Thus, your password is not included in the sdcard.

#### 3.3.2. ssh security

You are now generate certificates, to allow only some computer to connect to it.
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

disconnect all pi user, and connect to root

```yaml
ssh root@192.168.20.100
usermod --login totof --home /home/totof --move-home pi
```

once done, disconnect an connect to your new user

```yaml
ssh totof@192.168.20.100
```

remove root password in /etc/shadow. Change the root line, set * between the first two :

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

### 3.4. Python

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

### 3.5. commands with root privilege

The current program is able to activate/deactivate Wifi. So, it needs to use the ifconfig command with root privilege.

To run some sudo command from your python script, create a file in the directory /etc/sudoers.d to describe allowed admin commands without password

For example, /etc/sudoers.d/011_totof-nopasswd . This example describes admin user (ADMIN), admin commands (ADMIN_CMDS) and all the admin user to run admin commands without passwd

```yaml
# User alias specification
User_Alias ADMIN = totof

# Cmnd alias specification
Cmnd_Alias ADMIN_CMDS = /sbin/ifconfig

# Allow members of group sudo to execute any command
ADMIN   ALL=(root) NOPASSWD: ADMIN_CMDS
```

### 3.6. program configuration

This program use default configuration file chicken.json. You can change it with option -c.



