# SMBMounter
This program scan shares on a SMB server and can mount checked ones

# Interface
The programme ask for a name server

![image](https://github.com/user-attachments/assets/21ca765e-ca88-48fb-9f49-bd91331314fa)

Then it shows all shares: you can check them and ask it to mount them for you, in ~/SMBLinks

![image](https://github.com/user-attachments/assets/544e5b09-8e7e-4bb5-a098-944aeea6238e)

# Usage
I'm using Linux and few programs are snap images: snap is limited with filesystem, but I don't want to create permanent share in /mnt (and they're lot of chances that snap program's aren't able to access them). So I ask help on manjaro's forum and linux-aarhus answered me with a shell example, using GVfs.
I've adapted my program to use same functions and it works like a charmed, then I've decided to... *share* it :)

# Where it started
On Manjaro forum, but should works on any linux system having Python3, tkinter, GVsf
https://forum.manjaro.org/t/need-help-for-mounting-smb-share-with-python/172431/1
