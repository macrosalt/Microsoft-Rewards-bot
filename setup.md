# Setting up Microsoft Rewards Bot
Note: This guide will only show you how to how to run the bot using Google Chrome NOT Edge.
## Installing Python
Firstly install the latest version of [Python](https://www.python.org/downloads/). Make sure to download the specified version for your operating system. 
## Installing the Bot
To download the bot go to [@farshadz1997's github page](https://github.com/farshadz1997/Microsoft-Rewards-bot), click the green **code** button, and then click **Download ZIP**. Once it is installed onto your machine, extract the .zip file and move it to a memorable place such as **Documents**.
## Installing Chrome
If you already have Google Chrome installed, skip this step. Otherwise download the latest version of [Google Chrome](https://www.google.com/intl/en_au/chrome/thank-you.html?statcb=0&installdataindex=empty&defaultbrowser=0).
## Downloading Chrome Webdriver
Open chrome and type in [chrome://version/](chrome://version/). Then at the very top it will say **Google Chrome:** and a lot of numbers. (eg. 111.0.5563.65). Now open the [Chrome Webdriver download page](https://chromedriver.chromium.org/downloads) and find the version which closest represents your chrome version (in my case it was **ChromeDriver 111.0.5563.64**). Download and extract this compressed ZIP. From there take the .exe and move it into the folder where your Microsoft Rewards Bot is located. 
## Initalising the bot
On Windows, in file explorer click on the address bar, type "**wt**" into the field, then hit enter. In terminal run the following commands (LINUX/MACOS USERS CAN NOT USE RENAME, THE HAVE TO USE MV (move))
```
pip install -r requirements.txt
ren accounts.json.sample accounts.json
echo "py .\ms_rewards_farmer.py" > manual_run.bat
echo "py .\ms_rewards_farmer.py --start-at 06:30 --everyday" > run_at_6.30am_daily.bat
```
## Adding Accounts
To add/edit accounts open **accounts.json** and change the sample email and password to add more accounts simply follow the following:
```
[
  {
    "username": "email1@gmail.com",
    "password": "password1"
  },
  {
    "username": "email2@gmail.com",
    "password": "password2"
  }
 ]
 ```
**Make sure when adding more accounts you add a comma after the curly bracket.**
## Running the script
Finally! You've reached the point where we are ready to run the script. Simply in the folder where your bot is located, double click **manual_run.bat**. To keep it running daily just double click **run_at_6.30am_daily.bat** and make sure not to close terminal. Enjoy!
