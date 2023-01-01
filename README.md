[[GUI-Farmer-Repository]](https://github.com/farshadz1997/Microsoft-Rewards-bot-GUI)
<p align="center">
  <img src="https://forthebadge.com/images/badges/made-with-python.svg"/>
  <img src="http://ForTheBadge.com/images/badges/built-by-developers.svg"/>
  <img src="http://ForTheBadge.com/images/badges/uses-git.svg"/>
  <img src="http://ForTheBadge.com/images/badges/built-with-love.svg"/>
</p>

<pre align="center">
███╗   ███╗███████╗    ███████╗ █████╗ ██████╗ ███╗   ███╗███████╗██████╗ 
████╗ ████║██╔════╝    ██╔════╝██╔══██╗██╔══██╗████╗ ████║██╔════╝██╔══██╗
██╔████╔██║███████╗    █████╗  ███████║██████╔╝██╔████╔██║█████╗  ██████╔╝
██║╚██╔╝██║╚════██║    ██╔══╝  ██╔══██║██╔══██╗██║╚██╔╝██║██╔══╝  ██╔══██╗
██║ ╚═╝ ██║███████║    ██║     ██║  ██║██║  ██║██║ ╚═╝ ██║███████╗██║  ██║
╚═╝     ╚═╝╚══════╝    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝
        built by @charlesbel upgraded by @farshadz1997      version 2.0
</pre>

<p align="center">
  <img src="https://img.shields.io/badge/Maintained%3F-yes-green.svg?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge"/>
</p>

<h2 align="center">👋 Welcome to the future of automation</h2>
<h3 align="center">A simple bot that uses selenium to farm Microsoft Rewards written in Python.</h3>

<h2 align="center">Installation</h2>
<p allign="center">You can also find this repository on <a href="https://gitlab.com/farshadzargary1997/Microsoft-Rewards-bot">Gitlab</a>.</p>
<p align="center">
  <ul>
    <li>Install requirements with the following command : <pre>pip install -r requirements.txt</pre></li>
    <li>Make sure you have Chrome installed</li>
    <li>Install ChromeDriver :<ul>
      <li>Windows :<ul>
        <li>Download Chrome WebDriver as same as your Google Chrome version : https://chromedriver.chromium.org/downloads</li>
        <li>Place the file in X:\Windows (X as your Windows disk letter)</li>
      </ul>
      <li>MacOS or Linux :<ul>
        <li><pre>apt install chromium-chromedriver</pre></li>
        <li>or if you have brew : <pre>brew cask install chromedriver</pre></li>
      </ul>
    </ul></li>
    <li>Edit the accounts.json.sample with your accounts credentials and rename it by removing .sample at the end<br/>
    If you want to add more than one account, the syntax is the following (<code>mobile_user_agent</code> is optional): <pre>[{
        "username": "Your Email",
        "password": "Your Password",
        "mobile_user_agent": "your preferred mobile user agent"
    },
    {
        "username": "Your Email 2",
        "password": "Your Password 2",
        "mobile_user_agent": "your preferred mobile user agent"
}]</pre></li>
    <li>Due to limits of Ipapi sometimes it returns error and it causes bot stops. So you can define default language and location to prevent it from 
      <a href="https://github.com/farshadz1997/Microsoft-Rewards-bot/blob/479b2d4b25761d245dc6b3519627162a44d8f85b/ms_rewards_farmer.py#L367">here</a>.</li>
    <li>Run the script</li>
      <ul>
        <li>Use optinal arguments</li>
          <ul>
            <li><code>--headless</code> You can use this argument to run the script in headless mode.</li>
            <li><code>--session</code> Use this argument to create session for each account.</li>
            <li><code>--everyday TIME</code> This argument takes time in 24h format (HH:MM) to run it everyday at the given time by leaving the program open.</li>
            <li><code>--fast</code> This argument reduces delays of script and make it faster (use this if you have high speed connection).</li>
            <li><code>--error</code> When you use this argument, app displays crash error in terminal when it fails.</li>
            <li><code>--telegram TOKEN CHAT_ID</code> Use this argument to send logs to your telegram through your bot.</li>
            <li><code>--discord WEBHOOK_URL</code> Use this argument to send logs to your Discord server through webhook.</li>
            <li><code>--edge</code> Use Microsoft Edge webdriver instead of Chrome.<a href="https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/"> Download Microsoft Edge web driver.</a></li>
            <li><code>--shutdown</code> Shutdown computer after farm.</li>
            <li>For example type in your terminal <code>python ms_rewards_farmer.py --everyday 14:30 --fast --session</code> You don't need to use all of arguments.</li>
          </ul>
        <li>Run the script normally that session and headless disabled and it asks you to input a time if you want to run it at a specific time.</li>
      </ul>
   </ul>
</p>

<h2 align="center">Features</h2>
<p align="center">
<ul>
  <li>Bing searches (Desktop, Mobile and Edge) with User-Agents</li>
  <li>Complete automatically the daily set</li>
  <li>Complete automatically punch cards</li>
  <li>Complete automatically the others promotions</li>
  <li>Headless Mode</li>
  <li>Multi-Account Management</li>
  <li>Modified to be undetectable as bot</li>
  <li>If it faces to an unexpected error then try the account from first</li>  
  <li>Save progress of bot in a log file and use it to pass completed account on the next start at the same day</li>
  <li>Detect suspended accounts</li>
  <li>Detect locked accounts</li>
  <li>Detect unusual activites</li>
  <li>Uses time out to prevent infinite loop</li>
  <li>You can assign custom user-agent for mobile like above example</li>
  <li>Set clock to start it at specific time</li>
  <li>For Bing search it uses random word at first try and if api failed then it uses google trends</li>
</ul>
</p>
<h2 align="center">⚠️CAUTION!⚠️</h2>
<p align="center">
  <h4 align="center">Do not use headless mode, it can cause your account to be suspended from Microsoft Rewards.</h4>
