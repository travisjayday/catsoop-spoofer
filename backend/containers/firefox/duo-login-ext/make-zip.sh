# makes a deployable zip file of this firefox extension
rm -rf duo.zip && zip duo.zip background.js duo-login.js manifest.json popup.html icon32.png popup.js
