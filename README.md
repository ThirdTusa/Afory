# Afory
This is a python music player that allows you to download music from web into your playlists

Newest versions see here: https://github.com/ThirdTusa/Afory/releases

For older versions go to repository instead of realeses

# INSTALL GUIDE (HARD):

Windows:

1) Open zip folder and move .exe to desktop
2) Open .exe
3) If security window opened, click "more" then open "anyway"
4) After installer window opened, click "yes" then "install"
5) Wait for instalation to finish, and click "finish"
   
By default, .exe location will be here: Appdata/Local/AforyApp/Afory.exe

MacOS: (10.13+)

1) Open zip folder
2) Open .dmg file (Will appear after opening zip folder)
3) If you get message like "This app cant be verified" follow next steps
4) After opening go to setting
5) Search for privacy & security
6) Scroll down (if needed) and click "open anyway"
7) Again click "open anyway"
8) Then dmg window will open
9) Move Afory.app (That in dmg window) to /Applications folder (Can be found in finder)
10) Open Afory.app (Can be located in /Applications or in launchpad)
11) If app crashed follow next steps
12) Open terminal
13) In terminal write: codesign --remove-signature /Apptications/Afory.app
14) Open Afory.app again
15) If you again get message like "This app cant be verified" follow next steps
16) Go to settings then privary & security then click "open anyway"
17) Again click "open anyway"

MacOS protection is stupidly strong

By default, .app location will be here: /Apptications/Afory.app
By default, unix file location will be here: /Apptications/Afory.app/Contents/MacOS/Afory

If you wanna open any unsigned programms 
on your mac without 15+ steps write in terminal:

sudo spctl --master-disable

This command will disable protection when opening unsigned .app
Warning: Be careful because disabling protection may result bad conditions!
