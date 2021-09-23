
!!!!!!!!!!!!! YOU NEED TO CONFIGURE xled.map !!!!!!!!!!!!!

RENAME THIS TO XLED.CSV AND OPEN IN GOOGLE SHEETS OR EXCEL
THIS IS THE LED MAP OF YOUR SIGN.
THE SPREADSHEET CELLS REPRESENT THE SIGN ITSELF, THE NUMBERS ARE THE LED NUMBER
RENAME TO xled.map WHEN DONE.

!!!!!!!!!!!!! YOU NEED TO CONFIGURE XLED.MAP !!!!!!!!!!!!!


I use the xled.exe to display like this
Open a cmd window or powershell: (https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell-core-on-windows?view=powershell-7.1)


Drag the xled.exe into the window hit enter.
You should get a help display for the appplication that looks like this:

---------------------------------------------------------------------------
PS C:\Users\E\test\xled_sign> L:\xled.exe
Usage: xled [OPTIONS] COMMAND [ARGS]...

Options:
  --version                 Show the version and exit.
  --name DEVICE_NAME        Name of the device to operate on. Mutually
                            exclusive with --hostname.

  --hostname ADDRESS        Address of the device to operate on. Mutually
                            exclusive with --name.

  --verbosity-cli LVL       Sets verbosity of main CLI. Either CRITICAL,
                            ERROR, WARNING, INFO or DEBUG

  --verbosity-discover LVL  Sets verbosity of discover module. Either
                            CRITICAL, ERROR, WARNING, INFO or DEBUG

  --verbosity-control LVL   Sets verbosity of control module. Either CRITICAL,
                            ERROR, WARNING, INFO or DEBUG

  --verbosity-auth LVL      Sets verbosity of auth module. Either CRITICAL,
                            ERROR, WARNING, INFO or DEBUG

  --help                    Show this message and exit.

Commands:
  disable-timer    Disables timer.
  get-device-name  Gets current device name.
  get-mode         Gets current device mode.
  get-timer        Gets current timer settings.
  off              Turns device off.
  on               Turns device on and starts last used movie.
  realtime         Turns realtime on.
  set-color        Sets static color.
  set-device-name  Sets device name.
  set-timer        Sets timer.
  update-firmware  Updates firmware.
  upload-movie     Uploads movie.
---------------------------------------------------------------------------


Push your up arrow on the keyboard to bring the same command up again. 
Now we will add the mode and image we want to send to the sign.

Add the option "realtime" "-g" and then drag in the gif or png image you want to display on the sign.

Example
-------------------------------------------------------------------
L:\xled.exe realtime  -g .\pixelart\pokeball.png
Looking for any device...
-------------------------------------------------------------------





