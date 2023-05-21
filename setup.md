# Setting up Microsoft Rewards Bot
## Installing Python
Firstly install the latest version of [Python](https://www.python.org/downloads/). Make sure to download the specified version for your operating system. 
## Installing the Bot
To download the bot go to [@farshadz1997's github page](https://github.com/farshadz1997/Microsoft-Rewards-bot), click the green **code** button, and then click **Download ZIP**. Once it is installed onto your machine, extract the .zip file and move it to a memorable place such as **Documents**.
## Installing Chrome
If you already have Google Chrome installed, skip this step. Otherwise download the latest version of [Google Chrome](https://www.google.com/intl/en_au/chrome/thank-you.html?statcb=0&installdataindex=empty&defaultbrowser=0).
## Initalizing the bot
On Windows, in file explorer click on the address bar, type "**wt**" into the field, then hit enter. In terminal run the following commands.
**Windows:**
```
pip install -r requirements.txt
ren accounts.json.sample accounts.json
echo "py .\ms_rewards_farmer.py --redeem --session" > manual_run.bat
echo "py .\ms_rewards_farmer.py --start-at 06:30 --everyday --redeem --session" > run_at_6.30am_daily.bat
echo "py .\ms_rewards_farmer.py --redeem --session --edge" > manual_run_edge.bat
echo "py .\ms_rewards_farmer.py --start-at 06:30 --everyday --redeem --session --edge" > run_at_6.30am_daily_edge.bat
echo "py .\ms_rewards_farmer.py --calculator" > calculator.bat
```
**Linux:**
```
pip install -r requirements.txt
sudo apt-get install python3-tk
mv accounts.json.sample accounts.json
echo "py .\ms_rewards_farmer.py --redeem --session" > manual_run.sh
echo "py .\ms_rewards_farmer.py --start-at 06:30 --everyday --redeem --session" > run_at_6.30am_daily.sh
echo "py .\ms_rewards_farmer.py --redeem --session --edge" > manual_run_edge.sh
echo "py .\ms_rewards_farmer.py --start-at 06:30 --everyday --redeem --session --edge" > run_at_6.30am_daily_edge.sh
echo "py .\ms_rewards_farmer.py --calculator" > calculator.sh
```
## Adding Accounts
To add/edit accounts open **accounts.json** and change the sample email and password to add more accounts simply follow the following:
```
[
  {
    "username": "email1@gmail.com",
    "password": "password1",
    "goal": ""
  },
  {
    "username": "email2@gmail.com",
    "password": "password2",
    "goal": ""
  }
 ]
 ```
**Make sure when adding more accounts you add a comma after the curly bracket.**
## Running the script
Finally! You've reached the point where we are ready to run the script. Simply in the folder where your bot is located, double click **manual_run.bat**. To keep it running daily just double click **run_at_6.30am_daily.bat** and make sure not to close terminal. To use microsoft rewards calculator open **calculator.bat** Enjoy!

## Running script in Linux
```bash
./run.sh
```
> This will execute the default command **python3 ms_rewards_farmer.py**, if you want to add more options, you can add them in the run.sh file. For example, if you want to run the script with --redeem option, you can open run.sh file and add --redeem option at the end of the command like this:
```bash
python3 ms_rewards_farmer.py --redeem
```

# Setting up Microsoft Rewards Bot for Arm Processors using Linux

> All steps have been tested on Ubuntu 22.04. If you use another distribution, you will need to find command equivalents for your distribution. It is also expected that you have previously installed Python, cloned the bot,added accounts, and installed bot dependencies.

## Installing Supported Browser
Because Chrome does not provide an arm version for Linux, you will need to install the chromium browser in order to run this script.
```
sudo apt install chromium-browser
```
Use the command above to install the chromium browser on your arm device.

## Installing Supported Webdriver
Run the command below to install a compatible chromedriver.
```
sudo apt install chromium-chromedriver
```

## Running the Bot

You may run the bot in the same way you would on any other linux device; simply add `--no-webdriver-manager` to the options. for example `python ms_rewards_farmer.py --start-at 14:30 --everyday --fast --session --no-webdriver-manager`

# Setup Microsoft-Rewards-bot in termux

## Install required packages

Chromium and chromedriver is there in tur repo and x11 repo contains some dependencies of chromium

Run these commands

```
pkg install -y tur-repo x11-repo python python-tkinter
pkg install -y chromium xorg-server-xvfb
```

- Clone the repo
 
- Setup the repo like how you would do normally

- In the command, `--virtual-display --no-webdriver-manager` must be added and do not add `--headless` ( otherwise it will throw an error ).

Example:
```
python3 ms_rewards_farmer.py --no-images --session --superfast --no-webdriver-manager --virtual-display 
```
