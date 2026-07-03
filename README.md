# Samsung Galaxy Young 2 postmarketOS development

postmarketOS port for the Samsung Galaxy Young 2

> Device page: [Samsung Galaxy Young 2 (samsung-young23g)](https://wiki.postmarketos.org/wiki/Samsung_Galaxy_Young_2_(samsung-young23g))

<p align="center">
<img width="300" src="https://github.com/user-attachments/assets/90c813bc-6898-4942-94a1-c5b54f512f05"/>
</p>

<p align="center">
  <em>Hey, look, there's me!</em>
</p>

## Device

Tested device:

- **Device:** Samsung Galaxy Young 2
- **Model:** SM-G130HN
- **Codename:** samsung-young23g
- **Architecture:** ARMv7
- **Kernel:** downstream Samsung/Spreadtrum 3.10.17
- **Userspace:** postmarketOS / Alpine Linux

This is definitely more a "proof-of-concept" than a daily driver.

## Current status

The device currently boots into a headless postmarketOS/Alpine userspace and can be accessed over USB networking with SSH.

### Working

- Kernel boots
- postmarketOS/Alpine root filesystem mounts
- OpenRC starts
- USB RNDIS networking works
- SSH over USB works
- PTY allocation works
- Root shell is available over SSH
- The setup survives reboot and becomes reachable again over USB (however you have to re-configure windows shared wifi settings everytime)

### Not working yet

- Graphical UI is not finished
- Wi-Fi is not configured
- NetworkManager is not working correctly yet
- Sound is not tested
- Camera is not tested
- Modem, calls, SMS, and mobile data are not working/tested
- This is not ready for normal phone use, but it sure is interesting to watch!
