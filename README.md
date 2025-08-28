[README НА РУССКОМ](./READMERUS.md)
# RealityConnect
## Managed by [Zernov](https://www.youtube.com/@zernovtech)

## About
Python (especially Windows) application that streaming Desktop over the MJPEG protocol. 
Used [Tkinter](https://docs.python.org/3/library/tkinter.html) for easy control, [DXCam](https://github.com/ra1nty/DXcam) for screenshots and [QRCode](https://pypi.org/project/qrcode/) for easy connection.

## How it works?!

Simple. For using on a Windows/in a "Release mode" you can just run .exe file. There are some controls in the Window:

![RFConnect control panel](https://github.com/user-attachments/assets/b5c59837-13c6-4216-ace1-280b9056b6a4)
1. IP adress of your PC (Sets automaticly)
2. Start/stop streaming
3. Preview (Using standart browser)
4. Monitor number (Like in Windows Preferences)
5. Show/hide calculated FPS
6. High Resolution checkbox (Basically, divides resolution twice for higher FPS)
7. Generated QR Code with link to MJPEG stream

## Basicly it working with my [Unity MR app for Android](https://github.com/ZernovTechno/AR)

### Known Isues

Issue: Black screen
Solution: Set scale for monitor to 100% in Windows Preferences
