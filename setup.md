# Setting up Microsoft Rewards Bot
## Installing Python
Firstly install the latest version of [Python](https://www.python.org/downloads/). Make sure to download the specified version for your operating system. 
## Installing the Bot
To download the bot go to [@farshadz1997's github page](https://github.com/farshadz1997/Microsoft-Rewards-bot), click the green **code** button, and then click **Download ZIP**. Once it is installed onto your machine, extract the .zip file and move it to a memorable place such as **Documents**.
## Installing Chrome
If you already have Google Chrome installed, skip this step. Otherwise download the latest version of [Google Chrome](https://www.google.com/intl/en_au/chrome/thank-you.html?statcb=0&installdataindex=empty&defaultbrowser=0).
## Initalising the bot
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
