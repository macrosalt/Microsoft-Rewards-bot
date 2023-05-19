import json
import os
import traceback
import builtins
import platform
import random
import subprocess
import sys
import time
import urllib.parse
from argparse import ArgumentParser
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Union, List, Literal
import copy
import ipapi
import requests
import pyotp
from functools import wraps
from func_timeout import FunctionTimedOut, func_set_timeout
from notifiers import get_notifier
from selenium import webdriver
from selenium.common.exceptions import (ElementNotInteractableException, NoAlertPresentException,
                                        NoSuchElementException, SessionNotCreatedException, TimeoutException,
                                        UnexpectedAlertPresentException, JavascriptException,
                                        ElementNotVisibleException, ElementClickInterceptedException)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth
from pyvirtualdisplay import Display
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import tkinter as tk
from tkinter import messagebox, ttk
from math import ceil
from exceptions import *


# Define user-agents
PC_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.58'
MOBILE_USER_AGENT = 'Mozilla/5.0 (Linux; Android 12; SM-N9750) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36 EdgA/112.0.1722.46'

POINTS_COUNTER = 0

# Global variables
# added accounts when finished or those have same date as today date in LOGS at beginning.
FINISHED_ACCOUNTS = []
ERROR = True  # A flag for when error occurred.
# A flag for when the account has mobile bing search, it is useful for accounts level 1 to pass mobile.
MOBILE = True
CURRENT_ACCOUNT = None  # save current account into this variable when farming.
LOGS = {}  # Dictionary of accounts to write in 'logs_accounts.txt'.
FAST = False  # When this variable set True then all possible delays reduced.
SUPER_FAST = False  # fast but super
BASE_URL = "https://rewards.bing.com/"

# Auto Redeem - Define max amount of auto-redeems per run and counter
MAX_REDEEMS = 1
auto_redeem_counter = 0


def isProxyWorking(proxy: str) -> bool:
    """Check if proxy is working or not"""
    try:
        requests.get("https://www.google.com/",
                     proxies={"https": proxy}, timeout=5)
        return True
    except:
        return False


def createDisplay():
    """Create Display"""
    try:
        display = Display(visible=False, size=(1920, 1080))
        display.start()
    except Exception as exc:  # skipcq
        prYellow("Virtual Display Failed!")
        prRed(exc if ERROR else "")


def retry_on_500_errors(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        driver: WebDriver = args[0]
        error_codes = ["HTTP ERROR 500", "HTTP ERROR 502",
                       "HTTP ERROR 503", "HTTP ERROR 504", "HTTP ERROR 505"]
        status_code = "-"
        result = function(*args, **kwargs)
        while True:
            try:
                status_code = driver.execute_script(
                    "return document.readyState;")
                if status_code == "complete" and not any(error_code in driver.page_source for error_code in error_codes):
                    return result
                elif status_code == "loading":
                    return result
                else:
                    raise Exception("Page not loaded")
            except Exception as e:
                # Check if the page contains 500 errors
                if any(error_code in driver.page_source for error_code in error_codes):
                    driver.refresh()  # Recursively refresh
                else:
                    raise Exception(
                        f"another exception occurred during handling 500 errors with status '{status_code}': {e}")
    return wrapper


def browserSetup(isMobile: bool, user_agent: str = PC_USER_AGENT, proxy: str = None) -> WebDriver:
    """Create Chrome browser"""
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.edge.options import Options as EdgeOptions
    if ARGS.edge:
        options = EdgeOptions()
    else:
        options = ChromeOptions()
    if ARGS.session or ARGS.account_browser:
        if not isMobile:
            options.add_argument(
                f'--user-data-dir={Path(__file__).parent}/Profiles/{CURRENT_ACCOUNT}/PC')
        else:
            options.add_argument(
                f'--user-data-dir={Path(__file__).parent}/Profiles/{CURRENT_ACCOUNT}/Mobile')
    options.add_argument("user-agent=" + user_agent)
    options.add_argument('lang=' + LANG.split("-")[0])
    options.add_argument('--disable-blink-features=AutomationControlled')
    prefs = {"profile.default_content_setting_values.geolocation": 2,
             "credentials_enable_service": False,
             "profile.password_manager_enabled": False,
             "webrtc.ip_handling_policy": "disable_non_proxied_udp",
             "webrtc.multiple_routes_enabled": False,
             "webrtc.nonproxied_udp_enabled": False}
    if ARGS.no_images:
        prefs["profile.managed_default_content_settings.images"] = 2
    if ARGS.account_browser:
        prefs["detach"] = True
    if proxy is not None:
        if isProxyWorking(proxy):
            options.add_argument(f'--proxy-server={proxy}')
            prBlue(f"Using proxy: {proxy}")
        else:
            if ARGS.recheck_proxy:
                prYellow(
                    "[PROXY] Your entered proxy is not working, rechecking the provided proxy.")
                time.sleep(5)
                if isProxyWorking(proxy):
                    options.add_argument(f'--proxy-server={proxy}')
                    prBlue(f"Using proxy: {proxy}")
                elif ARGS.skip_if_proxy_dead:
                    raise ProxyIsDeadException
                else:
                    prYellow(
                        "[PROXY] Your entered proxy is not working, continuing without proxy.")
            elif ARGS.skip_if_proxy_dead:
                raise ProxyIsDeadException
            else:
                prYellow(
                    "[PROXY] Your entered proxy is not working, continuing without proxy.")
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    if ARGS.headless and ARGS.account_browser is None:
        options.add_argument("--headless=new")
    options.add_argument('log-level=3')
    options.add_argument("--start-maximized")
    if platform.system() == 'Linux':
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
    if ARGS.edge:
        browser = webdriver.Edge(options=options) if ARGS.no_webdriver_manager else webdriver.Edge(
            service=Service(EdgeChromiumDriverManager().install()), options=options)
    else:
        browser = webdriver.Chrome(options=options) if ARGS.no_webdriver_manager else webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options)
        stealth(browser,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                )
    return browser


@retry_on_500_errors
def goToURL(browser: WebDriver, url: str):
    browser.get(url)


def displayError(exc: Exception):
    """Display error message with traceback"""
    if ERROR:
        tb = exc.__traceback__
        tb_str = traceback.format_tb(tb)
        error = "\n".join(tb_str).strip() + f"\n{exc}"
        prRed(error)


# Define login function
def login(browser: WebDriver, email: str, pwd: str, totpSecret: str, isMobile: bool = False):

    def answerToBreakFreeFromPassword():
        # Click No thanks on break free from password question
        time.sleep(2)
        browser.find_element(By.ID, "iCancel").click()
        time.sleep(5)

    def answerToSecurityQuestion():
        # Click Looks good on security question
        time.sleep(2)
        browser.find_element(By.ID, 'iLooksGood').click()
        time.sleep(5)

    def answerUpdatingTerms():
        # Accept updated terms
        time.sleep(2)
        browser.find_element(By.ID, 'iNext').click()
        time.sleep(5)

    def waitToLoadBlankPage():
        time.sleep(calculateSleep(10))
        wait = WebDriverWait(browser, 10)
        wait.until(ec.presence_of_element_located((By.TAG_NAME, "body")))
        wait.until(ec.presence_of_all_elements_located)
        wait.until(ec.title_contains(""))
        wait.until(ec.presence_of_element_located(
            (By.CSS_SELECTOR, "html[lang]")))
        wait.until(lambda driver: driver.execute_script(
            "return document.readyState") == "complete")

    def acceptNewPrivacy():
        time.sleep(3)
        waitUntilVisible(browser, By.ID, "id__0", 15)
        browser.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        waitUntilClickable(browser, By.ID, "id__0", 15)
        browser.find_element(By.ID, "id__0").click()
        WebDriverWait(browser, 25).until_not(
            ec.visibility_of_element_located((By.ID, "id__0")))
        time.sleep(5)

    def answerTOTP(totpSecret):
        """Enter TOTP code and submit"""
        if isElementExists(browser, By.ID, 'idTxtBx_SAOTCC_OTC'):
            if totpSecret is not None:
                # Enter TOTP code
                totpCode = pyotp.TOTP(totpSecret).now()
                browser.find_element(
                    By.ID, "idTxtBx_SAOTCC_OTC").send_keys(totpCode)
                print('[LOGIN]', 'Writing TOTP code...')
                # Click submit
                browser.find_element(By.ID, 'idSubmit_SAOTCC_Continue').click()
            else:
                print('[LOGIN]', 'TOTP code required but no secret was provided.')
            # Wait 5 seconds
            time.sleep(5)
            if isElementExists(browser, By.ID, 'idTxtBx_SAOTCC_OTC'):
                raise TOTPInvalidException

    # Close welcome tab for new sessions
    if ARGS.session:
        time.sleep(2)
        if len(browser.window_handles) > 1:
            current_window = browser.current_window_handle
            for handler in browser.window_handles:
                if handler != current_window:
                    browser.switch_to.window(handler)
                    time.sleep(0.5)
                    browser.close()
            browser.switch_to.window(current_window)
    time.sleep(1)
    # Access to bing.com
    goToURL(browser, 'https://login.live.com/')
    # Check if account is already logged in
    if ARGS.session:
        if browser.title == "":
            waitToLoadBlankPage()
        if browser.title == "Microsoft account privacy notice" or isElementExists(browser, By.XPATH, '//*[@id="interruptContainer"]/div[3]/div[3]/img'):
            acceptNewPrivacy()
        if browser.title == "We're updating our terms" or isElementExists(browser, By.ID, 'iAccrualForm'):
            answerUpdatingTerms()
        if browser.title == 'Is your security info still accurate?' or isElementExists(browser, By.ID, 'iLooksGood'):
            answerToSecurityQuestion()
        # Click No thanks on break free from password question
        if isElementExists(browser, By.ID, "setupAppDesc") or browser.title == "Break free from your passwords":
            answerToBreakFreeFromPassword()
        if browser.title == 'Microsoft account | Home' or isElementExists(browser, By.ID, 'navs_container'):
            prGreen('[LOGIN] Account already logged in !')
            RewardsLogin(browser)
            print('[LOGIN]', 'Ensuring login on Bing...')
            checkBingLogin(browser, isMobile)
            return
        elif browser.title == 'Your account has been temporarily suspended' or browser.current_url.startswith("https://account.live.com/Abuse"):
            raise AccountLockedException
        elif browser.title == "Help us protect your account" or browser.current_url.startswith(
                "https://account.live.com/proofs/Add"):
            handleUnusualActivity(browser, isMobile)
            return
        elif browser.title == "Help us secure your account" or browser.current_url.startswith("https://account.live.com/recover"):
            raise UnusualActivityException
        elif isElementExists(browser, By.ID, 'mectrl_headerPicture') or 'Sign In or Create' in browser.title:
            browser.find_element(By.ID, 'mectrl_headerPicture').click()
            waitUntilVisible(browser, By.ID, 'i0118', 15)
            if isElementExists(browser, By.ID, 'i0118'):
                browser.find_element(By.ID, "i0118").send_keys(pwd)
                time.sleep(2)
                browser.find_element(By.ID, 'idSIButton9').click()
                time.sleep(5)
                answerTOTP(totpSecret)
                prGreen('[LOGIN] Account logged in again !')
                RewardsLogin(browser)
                print('[LOGIN]', 'Ensuring login on Bing...')
                checkBingLogin(browser, isMobile)
                return
    # Wait complete loading
    waitUntilVisible(browser, By.ID, 'loginHeader', 10)
    # Enter email
    print('[LOGIN]', 'Writing email...')
    browser.find_element(By.NAME, "loginfmt").send_keys(email)
    # Click next
    browser.find_element(By.ID, 'idSIButton9').click()
    # Wait 2 seconds
    time.sleep(calculateSleep(5))
    if isElementExists(browser, By.ID, "usernameError"):
        raise InvalidCredentialsException
    # Wait complete loading
    waitUntilVisible(browser, By.ID, 'i0118', 10)
    # Enter password
    time.sleep(3)
    browser.find_element(By.ID, "i0118").send_keys(pwd)
    # browser.execute_script("document.getElementById('i0118').value = '" + pwd + "';")
    print('[LOGIN]', 'Writing password...')
    # Click next
    browser.find_element(By.ID, 'idSIButton9').click()
    # Wait 5 seconds
    time.sleep(5)
    if isElementExists(browser, By.ID, "passwordError"):
        raise InvalidCredentialsException
    answerTOTP(totpSecret)
    try:
        if ARGS.session:
            # Click Yes to stay signed in.
            browser.find_element(By.ID, 'idSIButton9').click()
        else:
            # Click No.
            browser.find_element(By.ID, 'idBtn_Back').click()
        if browser.title == "":
            waitToLoadBlankPage()
        if browser.title == "Microsoft account privacy notice" or isElementExists(browser, By.XPATH, '//*[@id="interruptContainer"]/div[3]/div[3]/img'):
            acceptNewPrivacy()
        if browser.title == "We're updating our terms" or isElementExists(browser, By.ID, 'iAccrualForm'):
            answerUpdatingTerms()
        if browser.title == 'Is your security info still accurate?' or isElementExists(browser, By.ID, 'iLooksGood'):
            answerToSecurityQuestion()
        # Click No thanks on break free from password question
        if isElementExists(browser, By.ID, "setupAppDesc") or browser.title == "Break free from your passwords":
            answerToBreakFreeFromPassword()
    except NoSuchElementException:
        # Check for if account has been locked.
        if (
            browser.title == "Your account has been temporarily suspended" or
            isElementExists(browser, By.CLASS_NAME, "serviceAbusePageContainer  PageContainer") or
            browser.current_url.startswith("https://account.live.com/Abuse")
        ):
            raise AccountLockedException
        elif browser.title == "Help us protect your account" or \
                browser.current_url.startswith("https://account.live.com/proofs/Add"):
            handleUnusualActivity(browser, isMobile)
            return
        elif browser.title == "Help us secure your account" or browser.current_url.startswith("https://account.live.com/recover"):
            raise UnusualActivityException
    # Wait 5 seconds
    time.sleep(5)
    # Click Security Check
    print('[LOGIN]', 'Passing security checks...')
    try:
        browser.find_element(By.ID, 'iLandingViewAction').click()
    except (NoSuchElementException, ElementNotInteractableException) as e:
        pass
    # Wait complete loading
    try:
        waitUntilVisible(browser, By.ID, 'KmsiCheckboxField', 10)
    except TimeoutException as e:
        pass
    # Click next
    try:
        browser.find_element(By.ID, 'idSIButton9').click()
        # Wait 5 seconds
        time.sleep(5)
    except (NoSuchElementException, ElementNotInteractableException) as e:
        pass
    print('[LOGIN]', 'Logged-in !')
    # Check Microsoft Rewards
    print('[LOGIN] Logging into Microsoft Rewards...')
    RewardsLogin(browser)
    # Check Login
    print('[LOGIN]', 'Ensuring login on Bing...')
    checkBingLogin(browser, isMobile)


def RewardsLogin(browser: WebDriver):
    """Login into Rewards"""
    goToURL(browser, BASE_URL)
    try:
        time.sleep(calculateSleep(10))
        # click on sign up button if needed
        if isElementExists(browser, By.ID, "start-earning-rewards-link"):
            browser.find_element(By.ID, "start-earning-rewards-link").click()
            time.sleep(5)
            browser.refresh()
            time.sleep(5)
    except:
        pass
    if browser.title == "Help us protect your account" or \
            browser.current_url.startswith("https://account.live.com/proofs/Add"):
        handleUnusualActivity(browser)
    time.sleep(calculateSleep(10))
    # Check for ErrorMessage
    try:
        browser.find_element(By.ID, 'error').is_displayed()
        # Check wheter account suspended or not
        if browser.find_element(By.XPATH, '//*[@id="error"]/h1').get_attribute(
                'innerHTML') == ' Uh oh, it appears your Microsoft Rewards account has been suspended.':
            raise AccountSuspendedException
        # Check whether Rewards is available in your region or not
        elif browser.find_element(By.XPATH, '//*[@id="error"]/h1').get_attribute(
                'innerHTML') == 'Microsoft Rewards is not available in this country or region.':
            raise RegionException
        else:
            error_text = browser.find_element(By.XPATH, '//*[@id="error"]/h1').get_attribute("innerHTML")
            prRed(f"[ERROR] {error_text}")
            raise DashboardException
    except NoSuchElementException:
        pass
    handleFirstVisit(browser)


@func_set_timeout(300)
def checkBingLogin(browser: WebDriver, isMobile: bool = False):
    """Check if logged in to Bing"""

    def getEmailPass():
        for account in ACCOUNTS:
            if account["username"] == CURRENT_ACCOUNT:
                return account["username"], account["password"], account.get("totpSecret", None)

    def loginAgain():
        waitUntilVisible(browser, By.ID, 'loginHeader', 10)
        print('[LOGIN]', 'Writing email...')
        email, pwd, totpSecret = getEmailPass()
        browser.find_element(By.NAME, "loginfmt").send_keys(email)
        browser.find_element(By.ID, 'idSIButton9').click()
        time.sleep(calculateSleep(5))
        waitUntilVisible(browser, By.ID, 'loginHeader', 10)
        browser.find_element(By.ID, "i0118").send_keys(pwd)
        print('[LOGIN]', 'Writing password...')
        browser.find_element(By.ID, 'idSIButton9').click()
        time.sleep(5)
        # Enter TOTP code if needed
        if isElementExists(browser, By.ID, 'idTxtBx_SAOTCC_OTC'):
            if totpSecret is not None:
                # Enter TOTP code
                totpCode = pyotp.TOTP(totpSecret).now()
                browser.find_element(
                    By.ID, "idTxtBx_SAOTCC_OTC").send_keys(totpCode)
                print('[LOGIN]', 'Writing TOTP code...')
                # Click submit
                browser.find_element(By.ID, 'idSubmit_SAOTCC_Continue').click()
            else:
                print('[LOGIN]', 'TOTP code required but no secret was provided.')
            # Wait 5 seconds
            time.sleep(5)
            if isElementExists(browser, By.ID, 'idTxtBx_SAOTCC_OTC'):
                raise TOTPInvalidException
        if isElementExists(browser, By.ID, "idSIButton9"):
            if ARGS.session:
                # Click Yes to stay signed in.
                browser.find_element(By.ID, 'idSIButton9').click()
            else:
                # Click No.
                browser.find_element(By.ID, 'idBtn_Back').click()
        goToURL(browser, "https://bing.com/")

    global POINTS_COUNTER  # pylint: disable=global-statement
    goToURL(browser, 'https://bing.com/')
    time.sleep(calculateSleep(15))
    # try to get points at first if account already logged in
    if ARGS.session:
        try:
            if not isMobile:
                try:
                    POINTS_COUNTER = int(browser.find_element(
                        By.ID, 'id_rc').get_attribute('innerHTML'))
                except ValueError:
                    if browser.find_element(By.ID, 'id_s').is_displayed():
                        browser.find_element(By.ID, 'id_s').click()
                        time.sleep(calculateSleep(15))
                        checkBingLogin(browser, isMobile)
                    time.sleep(2)
                    POINTS_COUNTER = int(
                        browser.find_element(By.ID, "id_rc").get_attribute("innerHTML").replace(",", ""))
            else:
                browser.find_element(By.ID, 'mHamburger').click()
                time.sleep(1)
                POINTS_COUNTER = int(browser.find_element(
                    By.ID, 'fly_id_rc').get_attribute('innerHTML'))
        except:
            pass
        else:
            return None
    # Accept Cookies
    try:
        browser.find_element(By.ID, 'bnp_btn_accept').click()
    except:
        pass
    if isMobile:
        # close bing app banner
        if isElementExists(browser, By.ID, 'bnp_rich_div'):
            try:
                browser.find_element(
                    By.XPATH, '//*[@id="bnp_bop_close_icon"]/img').click()
            except NoSuchElementException:
                pass
        try:
            time.sleep(1)
            browser.find_element(By.ID, 'mHamburger').click()
        except:
            try:
                browser.find_element(By.ID, 'bnp_btn_accept').click()
            except:
                pass
            time.sleep(1)
            if isElementExists(browser, By.XPATH, '//*[@id="bnp_ttc_div"]/div[1]/div[2]/span'):
                browser.execute_script("""var element = document.evaluate('/html/body/div[1]', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                                        element.remove();""")
                time.sleep(5)
            time.sleep(1)
            try:
                browser.find_element(By.ID, 'mHamburger').click()
            except:
                pass
        try:
            time.sleep(1)
            browser.find_element(By.ID, 'HBSignIn').click()
            if isElementExists(browser, By.NAME, "loginfmt"):
                loginAgain()
        except:
            pass
        try:
            time.sleep(2)
            browser.find_element(By.ID, 'iShowSkip').click()
            time.sleep(3)
        except:
            if browser.title == "Help us protect your account" or browser.current_url.startswith(
                    "https://account.live.com/proofs/Add"):
                handleUnusualActivity(browser, isMobile)
    # Wait 5 seconds
    time.sleep(5)
    # Refresh page
    goToURL(browser, 'https://bing.com/')
    # Wait 15 seconds
    time.sleep(calculateSleep(15))
    # Update Counter
    try:
        if not isMobile:
            try:
                POINTS_COUNTER = int(browser.find_element(
                    By.ID, 'id_rc').get_attribute('innerHTML'))
            except:
                if browser.find_element(By.ID, 'id_s').is_displayed():
                    browser.find_element(By.ID, 'id_s').click()
                    time.sleep(calculateSleep(15))

                    checkBingLogin(browser, isMobile)
                time.sleep(5)
                POINTS_COUNTER = int(browser.find_element(
                    By.ID, "id_rc").get_attribute("innerHTML").replace(",", ""))
        else:
            try:
                browser.find_element(By.ID, 'mHamburger').click()
            except:
                try:
                    browser.find_element(By.ID, 'bnp_close_link').click()
                    time.sleep(4)
                    browser.find_element(By.ID, 'bnp_btn_accept').click()
                except:
                    pass
                time.sleep(1)
                browser.find_element(By.ID, 'mHamburger').click()
            time.sleep(1)
            POINTS_COUNTER = int(browser.find_element(
                By.ID, 'fly_id_rc').get_attribute('innerHTML'))
    except:
        checkBingLogin(browser, isMobile)


def handleUnusualActivity(browser: WebDriver, isMobile: bool = False):
    prYellow('[ERROR] Unusual activity detected !')
    if isElementExists(browser, By.ID, "iShowSkip") and ARGS.skip_unusual:
        try:
            waitUntilClickable(browser, By.ID, "iShowSkip")
            browser.find_element(By.ID, "iShowSkip").click()
        except:
            raise UnusualActivityException
        else:
            prGreen('[LOGIN] Account already logged in !')
            RewardsLogin(browser)
            print('[LOGIN]', 'Ensuring login on Bing...')
            checkBingLogin(browser, isMobile)
            return
    else:
        LOGS[CURRENT_ACCOUNT]['Last check'] = 'Unusual activity detected !'
        FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
        updateLogs()
        cleanLogs()
        if ARGS.telegram or ARGS.discord:
            message = createMessage()
            sendReportToMessenger(message)
        input('Press any key to close...')
        os._exit(0)


def handleFirstVisit(browser: WebDriver):
    # Pass The Welcome Page.
    try:
        if isElementExists(browser, By.CLASS_NAME, "rewards-slide"):
            try:
                browser.find_element(
                    By.XPATH, "//div[@class='rewards-slide']//a").click()
                time.sleep(calculateSleep(5))
                progress, total = browser.find_element(
                    By.XPATH, "//div[@class='rewards-slide']//mee-rewards-counter-animation/span").get_attribute("innerHTML").split("/")
                progress = int(progress)
                total = int(total)
                if (progress < total):
                    browser.find_element(
                        By.XPATH, "//mee-rewards-welcome-tour//mee-rewards-slide[contains(@class, 'ng-scope') and not(contains(@class,'ng-hide'))]//mee-rewards-check-mark/../a").click()
                    time.sleep(calculateSleep(5))
            except:
                pass

            browser.find_element(
                By.XPATH, "//button[@data-modal-close-button]").click()
            time.sleep(calculateSleep(5))
    except:
        print('[LOGIN]', "Can't pass the first time quiz.")


def waitUntilVisible(browser: WebDriver, by_: By, selector: str, time_to_wait: int = 10):
    """Wait until visible"""
    WebDriverWait(browser, time_to_wait).until(
        ec.visibility_of_element_located((by_, selector)))


def waitUntilClickable(browser: WebDriver, by_: By, selector: str, time_to_wait: int = 10):
    """Wait until clickable"""
    WebDriverWait(browser, time_to_wait).until(
        ec.element_to_be_clickable((by_, selector)))


def waitUntilQuestionRefresh(browser: WebDriver):
    """Wait until question refresh"""
    tries = 0
    refreshCount = 0
    while True:
        try:
            browser.find_elements(By.CLASS_NAME, 'rqECredits')[0]
            return True
        except:
            if tries < 10:
                tries += 1
                time.sleep(0.5)
            else:
                if refreshCount < 5:
                    browser.refresh()
                    refreshCount += 1
                    tries = 0
                    time.sleep(5)
                else:
                    return False


def waitUntilQuizLoads(browser: WebDriver):
    """Wait until quiz loads"""
    tries = 0
    refreshCount = 0
    while True:
        try:
            browser.find_element(
                By.XPATH, '//*[@id="currentQuestionContainer"]')
            return True
        except:
            if tries < 10:
                tries += 1
                time.sleep(0.5)
            else:
                if refreshCount < 5:
                    browser.refresh()
                    refreshCount += 1
                    tries = 0
                    time.sleep(5)
                else:
                    return False


def findBetween(s: str, first: str, last: str) -> str:
    """Find between"""
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""


def getCCodeLangAndOffset() -> tuple:
    """Get lang, geo, time zone"""
    try:
        nfo = ipapi.location()
        lang = nfo['languages'].split(',')[0]
        geo = nfo['country']
        tz = str(round(int(nfo['utc_offset']) / 100 * 60))
        return lang, geo, tz
    # Due to ipapi limitations it will default to US
    except:
        return 'en-US', 'US', '-480'


def resetTabs(browser: WebDriver):
    """Reset tabs"""
    try:
        curr = browser.current_window_handle

        for handle in browser.window_handles:
            if handle != curr:
                browser.switch_to.window(handle)
                time.sleep(0.5)
                browser.close()
                time.sleep(0.5)

        browser.switch_to.window(curr)
        time.sleep(0.5)
        goToURL(browser, BASE_URL)
        waitUntilVisible(browser, By.ID, 'app-host', 30)
    except:
        goToURL(browser, BASE_URL)
        waitUntilVisible(browser, By.ID, 'app-host', 30)


def getAnswerCode(key: str, string: str) -> str:
    """Get answer code"""
    t = 0
    for i, _ in enumerate(string):
        t += ord(string[i])
    t += int(key[-2:], 16)
    return str(t)


def getDashboardData(browser: WebDriver) -> dict:
    """Get dashboard data"""
    tries = 0
    dashboard = None
    while not dashboard and tries <= 5:
        try:
            dashboard = findBetween(browser.find_element(By.XPATH, '/html/body').get_attribute('innerHTML'),
                                    "var dashboard = ",
                                    ";\n        appDataModule.constant(\"prefetchedDashboard\", dashboard);")
            dashboard = json.loads(dashboard)
        except json.decoder.JSONDecodeError:
            tries += 1
            if tries == 6:
                raise Exception("[ERROR] Could not get dashboard")
            browser.refresh()
            waitUntilVisible(browser, By.ID, 'app-host', 30)
    return dashboard


def getAccountPoints(browser: WebDriver) -> int:
    """Get account points"""
    return getDashboardData(browser)['userStatus']['availablePoints']


def bingSearches(browser: WebDriver, numberOfSearches: int, isMobile: bool = False):
    """Search Bing"""

    def getRelatedTerms(word: str) -> list:
        """Get related terms"""
        try:
            r = requests.get('https://api.bing.com/osjson.aspx?query=' +
                             word, headers={'User-agent': PC_USER_AGENT})
            return r.json()[1]
        except:
            return []

    def getGoogleTrends(numberOfwords: int) -> list:
        """Get trends"""
        search_terms = []
        i = 0
        while len(search_terms) < numberOfwords:
            i += 1
            r = requests.get('https://trends.google.com/trends/api/dailytrends?hl=' + LANG + '&ed=' + str(
                (date.today() - timedelta(days=i)).strftime('%Y%m%d')) + '&geo=' + GEO + '&ns=15')
            google_trends = json.loads(r.text[6:])
            for topic in google_trends['default']['trendingSearchesDays'][0]['trendingSearches']:
                search_terms.append(topic['title']['query'].lower())
                for related_topic in topic['relatedQueries']:
                    search_terms.append(related_topic['query'].lower())
            search_terms = list(set(search_terms))
        del search_terms[numberOfwords:(len(search_terms) + 1)]
        return search_terms

    def bingSearch(word: str, isMobile: bool):
        """Bing search"""
        try:
            if not isMobile:
                browser.find_element(By.ID, 'sb_form_q').clear()
                time.sleep(1)
            else:
                goToURL(browser, 'https://bing.com')
        except:
            goToURL(browser, 'https://bing.com')
        time.sleep(2)
        searchbar = browser.find_element(By.ID, 'sb_form_q')
        if FAST or SUPER_FAST:
            searchbar.send_keys(word)
            time.sleep(calculateSleep(1))
        else:
            for char in word:
                searchbar.send_keys(char)
                time.sleep(random.uniform(0.2, 0.45))
        searchbar.submit()
        time.sleep(calculateSleep(15))
        points = 0
        try:
            if not isMobile:
                try:
                    points = int(browser.find_element(
                        By.ID, 'id_rc').get_attribute('innerHTML'))
                except ValueError:
                    points = int(browser.find_element(
                        By.ID, 'id_rc').get_attribute('innerHTML').replace(",", ""))
            else:
                try:
                    browser.find_element(By.ID, 'mHamburger').click()
                except UnexpectedAlertPresentException:
                    try:
                        browser.switch_to.alert.accept()
                        time.sleep(1)
                        browser.find_element(By.ID, 'mHamburger').click()
                    except NoAlertPresentException:
                        pass
                time.sleep(1)
                points = int(browser.find_element(
                    By.ID, 'fly_id_rc').get_attribute('innerHTML'))
        except Exception as exc:  # skipcq
            if ERROR:
                prRed(str(exc))
            else:
                pass
        return points

    global POINTS_COUNTER  # pylint: disable=global-statement
    i = 0
    try:
        words = open("searchwords.txt", "r").read().splitlines()
        search_terms = random.sample(words, numberOfSearches)
        if search_terms is None:
            raise Exception
    except Exception:
        search_terms = getGoogleTrends(numberOfSearches)
        if len(search_terms) == 0:
            prRed('[ERROR] No search terms found, account skipped.')
            finishedAccount()
            cleanLogs()
            updateLogs()
            raise Exception()
    for word in search_terms:
        i += 1
        print(f'[BING] {i}/{numberOfSearches}', end="\r")
        points = bingSearch(word, isMobile)
        if points <= POINTS_COUNTER:
            relatedTerms = getRelatedTerms(word)
            for term in relatedTerms:
                points = bingSearch(term, isMobile)
                if points >= POINTS_COUNTER:
                    break
        if points > 0:
            POINTS_COUNTER = points
        else:
            break


def locateQuestCard(browser: WebDriver, activity: dict) -> WebElement:
    """Locate rewards card on the page"""
    time.sleep(5)
    all_cards = browser.find_elements(By.CLASS_NAME, "rewards-card-container")
    for card in all_cards:
        data_bi_id = card.get_attribute("data-bi-id")
        if activity["offerId"] == data_bi_id:
            return card
    else:
        raise NoSuchElementException(f"could not locate the provided card: {activity['name']}")


def completeDailySet(browser: WebDriver):
    """Complete daily set"""

    def completeDailySetSearch(_activity: dict):
        """Complete daily set search"""
        card = locateQuestCard(browser, _activity)
        card.click()
        time.sleep(1)
        browser.switch_to.window(window_name=browser.window_handles[1])
        time.sleep(calculateSleep(15))
        browser.close()
        time.sleep(2)
        browser.switch_to.window(window_name=browser.window_handles[0])
        time.sleep(2)

    def completeDailySetSurvey(_activity: dict):
        """Complete daily set survey"""
        card = locateQuestCard(browser, _activity)
        card.click()
        time.sleep(1)
        browser.switch_to.window(window_name=browser.window_handles[1])
        time.sleep(calculateSleep(8))
        # Accept cookie popup
        if isElementExists(browser, By.ID, 'bnp_container'):
            browser.find_element(By.ID, 'bnp_btn_accept').click()
            time.sleep(2)
        # Click on later on Bing wallpaper app popup
        if isElementExists(browser, By.ID, 'b_notificationContainer_bop'):
            browser.find_element(By.ID, 'bnp_hfly_cta2').click()
            time.sleep(2)
        waitUntilClickable(browser, By.ID, "btoption0", 15)
        time.sleep(1.5)
        browser.find_element(By.ID, "btoption" +
                             str(random.randint(0, 1))).click()
        time.sleep(calculateSleep(10))
        browser.close()
        time.sleep(2)
        browser.switch_to.window(window_name=browser.window_handles[0])
        time.sleep(2)

    def completeDailySetQuiz(_activity: dict):
        """Complete daily set quiz"""
        card = locateQuestCard(browser, _activity)
        card.click()
        time.sleep(3)
        browser.switch_to.window(window_name=browser.window_handles[1])
        time.sleep(calculateSleep(12))
        if not waitUntilQuizLoads(browser):
            resetTabs(browser)
            return
        # Accept cookie popup
        if isElementExists(browser, By.ID, 'bnp_container'):
            browser.find_element(By.ID, 'bnp_btn_accept').click()
            time.sleep(2)
        browser.find_element(By.XPATH, '//*[@id="rqStartQuiz"]').click()
        waitUntilVisible(browser, By.XPATH,
                         '//*[@id="currentQuestionContainer"]/div/div[1]', 10)
        time.sleep(3)
        numberOfQuestions = browser.execute_script(
            "return _w.rewardsQuizRenderInfo.maxQuestions")
        numberOfOptions = browser.execute_script(
            "return _w.rewardsQuizRenderInfo.numberOfOptions")
        for _ in range(numberOfQuestions):
            if numberOfOptions == 8:
                answers = []
                for i in range(8):
                    if browser.find_element(By.ID, "rqAnswerOption" + str(i)).get_attribute(
                            "iscorrectoption").lower() == "true":
                        answers.append("rqAnswerOption" + str(i))
                for answer in answers:
                    # Click on later on Bing wallpaper app popup
                    if isElementExists(browser, By.ID, 'b_notificationContainer_bop'):
                        browser.find_element(By.ID, 'bnp_hfly_cta2').click()
                        time.sleep(2)
                    waitUntilClickable(browser, By.ID, answer, 25)
                    browser.find_element(By.ID, answer).click()
                    time.sleep(calculateSleep(6))
                    if not waitUntilQuestionRefresh(browser):
                        return
                time.sleep(calculateSleep(6))
            elif numberOfOptions == 4:
                correctOption = browser.execute_script(
                    "return _w.rewardsQuizRenderInfo.correctAnswer")
                for i in range(4):
                    if browser.find_element(By.ID, "rqAnswerOption" + str(i)).get_attribute(
                            "data-option") == correctOption:
                        # Click on later on Bing wallpaper app popup
                        if isElementExists(browser, By.ID, 'b_notificationContainer_bop'):
                            browser.find_element(
                                By.ID, 'bnp_hfly_cta2').click()
                            time.sleep(2)
                        waitUntilClickable(
                            browser, By.ID, f"rqAnswerOption{str(i)}", 25)
                        browser.find_element(
                            By.ID, "rqAnswerOption" + str(i)).click()
                        time.sleep(calculateSleep(6))
                        if not waitUntilQuestionRefresh(browser):
                            return
                        break
                time.sleep(calculateSleep(6))
        time.sleep(calculateSleep(6))
        browser.close()
        time.sleep(2)
        browser.switch_to.window(window_name=browser.window_handles[0])
        time.sleep(2)

    def completeDailySetVariableActivity(_activity: dict):
        """Complete daily set variable activity"""
        card = locateQuestCard(browser, _activity)
        card.click()
        time.sleep(1)
        browser.switch_to.window(window_name=browser.window_handles[1])
        time.sleep(calculateSleep(10))
        # Accept cookie popup
        if isElementExists(browser, By.ID, 'bnp_container'):
            browser.find_element(By.ID, 'bnp_btn_accept').click()
            time.sleep(2)
        try:
            browser.find_element(By.XPATH, '//*[@id="rqStartQuiz"]').click()
            waitUntilVisible(
                browser, By.XPATH, '//*[@id="currentQuestionContainer"]/div/div[1]', 3)
        except (NoSuchElementException, TimeoutException):
            try:
                counter = str(
                    browser.find_element(By.XPATH, '//*[@id="QuestionPane0"]/div[2]').get_attribute('innerHTML'))[
                    :-1][1:]
                numberOfQuestions = max(
                    [int(s) for s in counter.split() if s.isdigit()])
                for question in range(numberOfQuestions):
                    # Click on later on Bing wallpaper app popup
                    if isElementExists(browser, By.ID, 'b_notificationContainer_bop'):
                        browser.find_element(By.ID, 'bnp_hfly_cta2').click()
                        time.sleep(2)

                    browser.execute_script(
                        f'document.evaluate("//*[@id=\'QuestionPane{str(question)}\']/div[1]/div[2]/a[{str(random.randint(1, 3))}]/div", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click()')
                    time.sleep(8)
                time.sleep(5)
                browser.close()
                time.sleep(2)
                browser.switch_to.window(window_name=browser.window_handles[0])
                time.sleep(2)
                return
            except NoSuchElementException:
                time.sleep(calculateSleep(random.randint(5, 9)))
                browser.close()
                time.sleep(2)
                browser.switch_to.window(window_name=browser.window_handles[0])
                time.sleep(2)
                return
        time.sleep(3)
        correctAnswer = browser.execute_script(
            "return _w.rewardsQuizRenderInfo.correctAnswer")
        if browser.find_element(By.ID, "rqAnswerOption0").get_attribute("data-option") == correctAnswer:
            browser.find_element(By.ID, "rqAnswerOption0").click()
        else:
            browser.find_element(By.ID, "rqAnswerOption1").click()
        time.sleep(10)
        browser.close()
        time.sleep(2)
        browser.switch_to.window(window_name=browser.window_handles[0])
        time.sleep(2)

    def completeDailySetThisOrThat(_activity: dict):
        """Complete daily set this or that"""
        card = locateQuestCard(browser, _activity)
        card.click()
        time.sleep(2)
        browser.switch_to.window(window_name=browser.window_handles[1])
        time.sleep(calculateSleep(25))
        # Accept cookie popup
        if isElementExists(browser, By.ID, 'bnp_container'):
            browser.find_element(By.ID, 'bnp_btn_accept').click()
            time.sleep(2)
        if not waitUntilQuizLoads(browser):
            resetTabs(browser)
            return
        browser.find_element(By.XPATH, '//*[@id="rqStartQuiz"]').click()
        waitUntilVisible(browser, By.XPATH,
                         '//*[@id="currentQuestionContainer"]/div/div[1]', 15)
        time.sleep(5)
        for _ in range(10):
            # Click on later on Bing wallpaper app popup
            if isElementExists(browser, By.ID, 'b_notificationContainer_bop'):
                browser.find_element(By.ID, 'bnp_hfly_cta2').click()
                time.sleep(2)

            answerEncodeKey = browser.execute_script("return _G.IG")
            waitUntilVisible(browser, By.ID, "rqAnswerOption0", 15)
            answer1 = browser.find_element(By.ID, "rqAnswerOption0")
            answer1Title = answer1.get_attribute('data-option')
            answer1Code = getAnswerCode(answerEncodeKey, answer1Title)

            answer2 = browser.find_element(By.ID, "rqAnswerOption1")
            answer2Title = answer2.get_attribute('data-option')
            answer2Code = getAnswerCode(answerEncodeKey, answer2Title)

            correctAnswerCode = browser.execute_script(
                "return _w.rewardsQuizRenderInfo.correctAnswer")

            waitUntilClickable(browser, By.ID, "rqAnswerOption0", 25)
            if answer1Code == correctAnswerCode:
                answer1.click()
                time.sleep(calculateSleep(25))
            elif answer2Code == correctAnswerCode:
                answer2.click()
                time.sleep(calculateSleep(25))

        time.sleep(calculateSleep(6))
        browser.close()
        time.sleep(2)
        browser.switch_to.window(window_name=browser.window_handles[0])
        time.sleep(2)

    print('[DAILY SET]', 'Trying to complete the Daily Set...')
    d = getDashboardData(browser)
    error = False
    todayDate = datetime.today().strftime('%m/%d/%Y')
    todayPack = []
    for date_, data in d['dailySetPromotions'].items():
        if date_ == todayDate:
            todayPack = data
    for activity in todayPack:
        try:
            if not activity['complete']:
                cardNumber = int(activity['offerId'][-1:])
                if activity['promotionType'] == "urlreward":
                    print('[DAILY SET]',
                          'Completing search of card ' + str(cardNumber))
                    completeDailySetSearch(activity)
                if activity['promotionType'] == "quiz":
                    if activity['pointProgressMax'] == 50 and activity['pointProgress'] == 0:
                        print(
                            '[DAILY SET]', 'Completing This or That of card ' + str(cardNumber))
                        completeDailySetThisOrThat(activity)
                    elif (activity['pointProgressMax'] == 40 or activity['pointProgressMax'] == 30) and activity['pointProgress'] == 0:
                        print('[DAILY SET]',
                              'Completing quiz of card ' + str(cardNumber))
                        completeDailySetQuiz(activity)
                    elif activity['pointProgressMax'] == 10 and activity['pointProgress'] == 0:
                        searchUrl = urllib.parse.unquote(
                            urllib.parse.parse_qs(urllib.parse.urlparse(activity['destinationUrl']).query)['ru'][0])
                        searchUrlQueries = urllib.parse.parse_qs(
                            urllib.parse.urlparse(searchUrl).query)
                        filters = {}
                        for filter in searchUrlQueries['filters'][0].split(" "):
                            filter = filter.split(':', 1)
                            filters[filter[0]] = filter[1]
                        if "PollScenarioId" in filters:
                            print(
                                '[DAILY SET]', 'Completing poll of card ' + str(cardNumber))
                            completeDailySetSurvey(activity)
                        else:
                            print(
                                '[DAILY SET]', 'Completing quiz of card ' + str(cardNumber))
                            completeDailySetVariableActivity(activity)
        except Exception as exc:
            displayError(exc)
            error = True
            resetTabs(browser)
    if not error:
        prGreen("[DAILY SET] Completed the Daily Set successfully !")
    else:
        prYellow(
            "[DAILY SET] Daily Set did not completed successfully ! Streak not increased")
    LOGS[CURRENT_ACCOUNT]['Daily'] = True
    updateLogs()


def completePunchCards(browser: WebDriver):
    """Complete punch cards"""

    def completePunchCard(url: str, childPromotions: dict):
        """complete punch card"""
        goToURL(browser, url)
        for child in childPromotions:
            if not child['complete']:
                if child['promotionType'] == "urlreward":
                    browser.execute_script(
                        "document.getElementsByClassName('offer-cta')[0].click()")
                    time.sleep(1)
                    browser.switch_to.window(
                        window_name=browser.window_handles[1])
                    time.sleep(calculateSleep(15))
                    browser.close()
                    time.sleep(2)
                    browser.switch_to.window(
                        window_name=browser.window_handles[0])
                    time.sleep(2)
                if child['promotionType'] == "quiz" and child['pointProgressMax'] >= 50:
                    browser.find_element(By.XPATH,
                                         '//*[@id="rewards-dashboard-punchcard-details"]/div[2]/div[2]/div[7]/div[3]/div[1]/a').click()
                    time.sleep(1)
                    browser.switch_to.window(
                        window_name=browser.window_handles[1])
                    time.sleep(calculateSleep(15))
                    try:
                        waitUntilVisible(browser, By.ID, "rqStartQuiz", 15)
                        browser.find_element(By.ID, "rqStartQuiz").click()
                    except:
                        pass
                    time.sleep(calculateSleep(6))
                    waitUntilVisible(
                        browser, By.ID, "currentQuestionContainer", 15)
                    numberOfQuestions = browser.execute_script(
                        "return _w.rewardsQuizRenderInfo.maxQuestions")
                    AnswerdQuestions = browser.execute_script(
                        "return _w.rewardsQuizRenderInfo.CorrectlyAnsweredQuestionCount")
                    numberOfQuestions -= AnswerdQuestions
                    for question in range(numberOfQuestions):
                        answer = browser.execute_script(
                            "return _w.rewardsQuizRenderInfo.correctAnswer")
                        waitUntilClickable(
                            browser, By.XPATH, f'//input[@value="{answer}"]', 25)
                        browser.find_element(
                            By.XPATH, f'//input[@value="{answer}"]').click()
                        time.sleep(calculateSleep(25))
                    time.sleep(5)
                    browser.close()
                    time.sleep(2)
                    browser.switch_to.window(
                        window_name=browser.window_handles[0])
                    time.sleep(2)
                    browser.refresh()
                    break
                elif child['promotionType'] == "quiz" and child['pointProgressMax'] < 50:
                    browser.execute_script(
                        "document.getElementsByClassName('offer-cta')[0].click()")
                    time.sleep(1)
                    browser.switch_to.window(
                        window_name=browser.window_handles[1])
                    time.sleep(calculateSleep(8))
                    waitUntilVisible(browser, By.XPATH,
                                     '//*[@id="QuestionPane0"]/div[2]', 15)
                    counter = str(
                        browser.find_element(By.XPATH, '//*[@id="QuestionPane0"]/div[2]').get_attribute('innerHTML'))[
                        :-1][1:]
                    numberOfQuestions = max(
                        [int(s) for s in counter.split() if s.isdigit()])
                    for question in range(numberOfQuestions):
                        browser.execute_script(
                            'document.evaluate("//*[@id=\'QuestionPane' +
                            str(question) + '\']/div[1]/div[2]/a['
                            + str(random.randint(1, 3)) +
                            ']/div", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click()')
                        time.sleep(calculateSleep(15))
                    time.sleep(5)
                    browser.close()
                    time.sleep(2)
                    browser.switch_to.window(
                        window_name=browser.window_handles[0])
                    time.sleep(2)
                    browser.refresh()
                    break

    print('[PUNCH CARDS]', 'Trying to complete the Punch Cards...')
    punchCards = getDashboardData(browser)['punchCards']
    for punchCard in punchCards:
        try:
            if (
                    punchCard['parentPromotion'] is not None and punchCard['childPromotions'] is not None and
                    punchCard['parentPromotion']['complete'] is False and
                    punchCard['parentPromotion']['pointProgressMax'] != 0
            ):
                url = punchCard['parentPromotion']['attributes']['destination']
                completePunchCard(url, punchCard['childPromotions'])
        except Exception as exc:
            displayError(exc)
            resetTabs(browser)
    time.sleep(2)
    goToURL(browser, BASE_URL)
    time.sleep(2)
    LOGS[CURRENT_ACCOUNT]['Punch cards'] = True
    updateLogs()
    prGreen('[PUNCH CARDS] Completed the Punch Cards successfully !')


def completeMorePromotions(browser: WebDriver):
    """Complete more promotions"""

    def completeMorePromotionSearch(_activity: dict):
        """Complete more promotion search"""
        card = locateQuestCard(browser, _activity)
        card.click()
        time.sleep(1)
        browser.switch_to.window(window_name=browser.window_handles[1])
        time.sleep(calculateSleep(15))
        browser.close()
        time.sleep(2)
        browser.switch_to.window(window_name=browser.window_handles[0])
        time.sleep(2)

    def completeMorePromotionQuiz(_activity: dict):
        """Complete more promotion quiz"""
        card = locateQuestCard(browser, _activity)
        card.click()
        time.sleep(1)
        browser.switch_to.window(window_name=browser.window_handles[1])
        time.sleep(calculateSleep(10))
        if not waitUntilQuizLoads(browser):
            resetTabs(browser)
            return
        CurrentQuestionNumber = browser.execute_script(
            "return _w.rewardsQuizRenderInfo.currentQuestionNumber")
        if CurrentQuestionNumber == 1 and isElementExists(browser, By.XPATH, '//*[@id="rqStartQuiz"]'):
            browser.find_element(By.XPATH, '//*[@id="rqStartQuiz"]').click()
        waitUntilVisible(browser, By.XPATH,
                         '//*[@id="currentQuestionContainer"]/div/div[1]', 15)
        time.sleep(3)
        numberOfQuestions = browser.execute_script(
            "return _w.rewardsQuizRenderInfo.maxQuestions")
        Questions = numberOfQuestions - CurrentQuestionNumber + 1
        numberOfOptions = browser.execute_script(
            "return _w.rewardsQuizRenderInfo.numberOfOptions")
        for _ in range(Questions):
            if numberOfOptions == 8:
                answers = []
                for i in range(8):
                    if browser.find_element(By.ID, "rqAnswerOption" + str(i)).get_attribute(
                            "iscorrectoption").lower() == "true":
                        answers.append("rqAnswerOption" + str(i))
                for answer in answers:
                    waitUntilClickable(browser, By.ID, answer, 25)
                    browser.find_element(By.ID, answer).click()
                    time.sleep(calculateSleep(6))
                    if not waitUntilQuestionRefresh(browser):
                        return
                time.sleep(calculateSleep(6))
            elif numberOfOptions == 4:
                correctOption = browser.execute_script(
                    "return _w.rewardsQuizRenderInfo.correctAnswer")
                for i in range(4):
                    if browser.find_element(By.ID, f"rqAnswerOption{str(i)}").get_attribute(
                            "data-option") == correctOption:
                        waitUntilClickable(
                            browser, By.ID, f"rqAnswerOption{str(i)}", 25)
                        browser.find_element(
                            By.ID, f"rqAnswerOption{str(i)}").click()
                        time.sleep(5)
                        if not waitUntilQuestionRefresh(browser):
                            return
                        break
                time.sleep(5)
        time.sleep(5)
        browser.close()
        time.sleep(2)
        browser.switch_to.window(window_name=browser.window_handles[0])
        time.sleep(2)

    def completeMorePromotionABC(_activity: dict):
        """Complete more promotion ABC"""
        card = locateQuestCard(browser, _activity)
        card.click()
        time.sleep(1)
        browser.switch_to.window(window_name=browser.window_handles[1])
        time.sleep(calculateSleep(10))
        waitUntilVisible(browser, By.XPATH,
                         '//*[@id="QuestionPane0"]/div[2]', 15)
        counter = str(browser.find_element(By.XPATH, '//*[@id="QuestionPane0"]/div[2]').get_attribute('innerHTML'))[
            :-1][1:]
        numberOfQuestions = max([int(s)
                                for s in counter.split() if s.isdigit()])
        for question in range(numberOfQuestions):
            browser.execute_script(
                f'document.evaluate("//*[@id=\'QuestionPane{str(question)}\']/div[1]/div[2]/a[{str(random.randint(1, 3))}]/div", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click()')
            time.sleep(calculateSleep(10) + 3)
        time.sleep(5)
        browser.close()
        time.sleep(2)
        browser.switch_to.window(window_name=browser.window_handles[0])
        time.sleep(2)

    def completeMorePromotionThisOrThat(_activity: dict):
        """Complete more promotion this or that"""
        card = locateQuestCard(browser, _activity)
        card.click()
        time.sleep(1)
        browser.switch_to.window(window_name=browser.window_handles[1])
        time.sleep(calculateSleep(8))
        if not waitUntilQuizLoads(browser):
            resetTabs(browser)
            return
        CrrentQuestionNumber = browser.execute_script(
            "return _w.rewardsQuizRenderInfo.currentQuestionNumber")
        NumberOfQuestionsLeft = 10 - CrrentQuestionNumber + 1
        if CrrentQuestionNumber == 1 and isElementExists(browser, By.XPATH, '//*[@id="rqStartQuiz"]'):
            browser.find_element(By.XPATH, '//*[@id="rqStartQuiz"]').click()
        waitUntilVisible(browser, By.XPATH,
                         '//*[@id="currentQuestionContainer"]/div/div[1]', 10)
        time.sleep(3)
        for _ in range(NumberOfQuestionsLeft):
            answerEncodeKey = browser.execute_script("return _G.IG")

            waitUntilVisible(browser, By.ID, "rqAnswerOption0", 15)
            answer1 = browser.find_element(By.ID, "rqAnswerOption0")
            answer1Title = answer1.get_attribute('data-option')
            answer1Code = getAnswerCode(answerEncodeKey, answer1Title)

            answer2 = browser.find_element(By.ID, "rqAnswerOption1")
            answer2Title = answer2.get_attribute('data-option')
            answer2Code = getAnswerCode(answerEncodeKey, answer2Title)

            correctAnswerCode = browser.execute_script(
                "return _w.rewardsQuizRenderInfo.correctAnswer")

            waitUntilClickable(browser, By.ID, "rqAnswerOption0", 15)
            if answer1Code == correctAnswerCode:
                answer1.click()
                time.sleep(calculateSleep(20))

            elif answer2Code == correctAnswerCode:
                answer2.click()
                time.sleep(calculateSleep(20))

        time.sleep(5)
        browser.close()
        time.sleep(2)
        browser.switch_to.window(window_name=browser.window_handles[0])
        time.sleep(2)

    def completePromotionalItems():
        """Complete promotional items"""
        try:
            item = getDashboardData(browser)["promotionalItem"]
            if (item["pointProgressMax"] == 100 or item["pointProgressMax"] == 200) and item["complete"] is False and \
                    item["destinationUrl"] == BASE_URL:
                browser.find_element(
                    By.XPATH, '//*[@id="promo-item"]/section/div/div/div/a').click()
                time.sleep(1)
                browser.switch_to.window(window_name=browser.window_handles[1])
                time.sleep(calculateSleep(8))
                browser.close()
                time.sleep(2)
                browser.switch_to.window(window_name=browser.window_handles[0])
                time.sleep(2)
        except:
            pass

    print('[MORE PROMO]', 'Trying to complete More Promotions...')
    morePromotions = getDashboardData(browser)['morePromotions']
    i = 0
    for promotion in morePromotions:
        try:
            i += 1
            if promotion['complete'] is False and promotion['pointProgressMax'] != 0:
                if promotion['promotionType'] == "urlreward":
                    completeMorePromotionSearch(promotion)
                elif promotion['promotionType'] == "quiz":
                    if promotion['pointProgressMax'] == 10:
                        completeMorePromotionABC(promotion)
                    elif promotion['pointProgressMax'] == 30 or promotion['pointProgressMax'] == 40:
                        completeMorePromotionQuiz(promotion)
                    elif promotion['pointProgressMax'] == 50:
                        completeMorePromotionThisOrThat(promotion)
                else:
                    if promotion['pointProgressMax'] == 100 or promotion['pointProgressMax'] == 200:
                        completeMorePromotionSearch(promotion)
            if promotion['complete'] is False and promotion['pointProgressMax'] == 100 and promotion[
                'promotionType'] == "" \
                    and promotion['destinationUrl'] == BASE_URL:
                completeMorePromotionSearch(promotion)
        except Exception as exc:
            displayError(exc)
            resetTabs(browser)

    completePromotionalItems()
    LOGS[CURRENT_ACCOUNT]['More promotions'] = True
    updateLogs()
    prGreen('[MORE PROMO] Completed More Promotions successfully !')


def completeMSNShoppingGame(browser: WebDriver) -> bool:
    """Complete MSN Shopping Game, returns True if completed successfully else False"""

    def expandShadowElement(element, index: int = None) -> Union[List[WebElement], WebElement]:
        """Returns childrens of shadow element"""
        if index is not None:
            shadow_root = WebDriverWait(browser, 45).until(
                ec.visibility_of(browser.execute_script(
                    'return arguments[0].shadowRoot.children', element)[index])
            )
        else:
            # wait to visible one element then get the list
            WebDriverWait(browser, 45).until(
                ec.visibility_of(browser.execute_script(
                    'return arguments[0].shadowRoot.children', element)[0])
            )
            shadow_root = browser.execute_script(
                'return arguments[0].shadowRoot.children', element)
        return shadow_root

    def getChildren(element) -> List[WebElement]:
        """get children"""
        children = browser.execute_script(
            'return arguments[0].children', element)
        return children

    def getSignInButton() -> WebElement:
        """check whether user is signed in or not and return the button to sign in"""
        script_to_user_pref_container = 'document.getElementsByTagName("shopping-page-base")[0]\
            .shadowRoot.children[0].children[1].children[0]\
            .shadowRoot.children[0].shadowRoot.children[0]\
            .getElementsByClassName("user-pref-container")[0]'
        WebDriverWait(browser, 60).until(ec.visibility_of(
            browser.execute_script(f'return {script_to_user_pref_container}')
        )
        )
        button = WebDriverWait(browser, 60).until(ec.visibility_of(
            browser.execute_script(
                f'return {script_to_user_pref_container}.\
                    children[0].children[0].shadowRoot.children[0].\
                    getElementsByClassName("me-control")[0]'
            )
        )
        )
        return button

    def signIn() -> None:
        """sign in"""
        sign_in_button = getSignInButton()
        sign_in_button.click()
        print("[MSN GAME] Signing in...")
        time.sleep(5)
        waitUntilVisible(browser, By.ID, 'newSessionLink', 10)
        browser.find_element(By.ID, 'newSessionLink').click()
        waitUntilVisible(browser, By.TAG_NAME, 'shopping-page-base', 60)
        expandShadowElement(browser.find_element(
            By.TAG_NAME, 'shopping-page-base'), 0)
        getSignInButton()

    def getGamingCard() -> Union[WebElement, Literal[False]]:
        """get gaming card, if completed before raises GamingCardIsNotActive exception"""
        shopping_page_base_childs = expandShadowElement(
            browser.find_element(By.TAG_NAME, 'shopping-page-base'), 0)
        shopping_homepage = shopping_page_base_childs.find_element(
            By.TAG_NAME, 'shopping-homepage')
        msft_feed_layout = expandShadowElement(
            shopping_homepage, 0).find_element(By.TAG_NAME, 'msft-feed-layout')
        msn_shopping_game_pane = expandShadowElement(msft_feed_layout)
        for element in msn_shopping_game_pane:
            if element.get_attribute("gamestate") == "active":
                return element
            elif element.get_attribute("gamestate") == "idle":
                browser.execute_script(
                    "arguments[0].scrollIntoView();", element)
                raise GamingCardIsNotActive
        else:
            return False

    def clickCorrectAnswer() -> None:
        """click correct answer"""
        options_container = expandShadowElement(gaming_card, 1)
        options_elements = getChildren(getChildren(options_container)[1])
        # click on the correct answer in options_elements
        correct_answer = options_elements[int(
            gaming_card.get_attribute("_correctAnswerIndex"))]
        # hover to show the select button
        correct_answer.click()
        time.sleep(1)
        # click 'select' button
        select_button = correct_answer.find_element(
            By.CLASS_NAME, 'shopping-select-overlay-button')
        WebDriverWait(browser, 5).until(
            ec.element_to_be_clickable(select_button))
        select_button.click()

    def clickPlayAgain() -> None:
        """click play again"""
        time.sleep(random.randint(4, 6))
        options_container = expandShadowElement(gaming_card)[1]
        getChildren(options_container)[0].find_element(
            By.TAG_NAME, 'button').click()

    try:
        if (ARGS.headless or ARGS.virtual_display) and platform.system() == "Linux":
            browser.set_window_size(1920, 1080)
        tries = 0
        print("[MSN GAME] Trying to complete MSN shopping game...")
        print("[MSN GAME] Checking if user is signed in ...")
        while tries <= 4:
            tries += 1
            goToURL(browser, "https://www.msn.com/en-us/shopping")
            waitUntilVisible(browser, By.TAG_NAME, 'shopping-page-base', 45)
            time.sleep(calculateSleep(15))
            try:
                sign_in_button = getSignInButton()
            except:
                if tries == 4:
                    raise ElementNotVisibleException(
                        "Sign in button did not show up")
            else:
                break
        time.sleep(5)
        if "Sign in" in sign_in_button.text:
            signIn()
        gaming_card = getGamingCard()
        scrolls = 0
        while not gaming_card and scrolls <= 5:
            scrolls += 1
            print(f"Locating gaming card - scrolling ({scrolls}/5)")
            browser.execute_script("window.scrollBy(0, 300);")
            time.sleep(calculateSleep(10))
            gaming_card = getGamingCard()
            if gaming_card:
                browser.execute_script(
                    "arguments[0].scrollIntoView();", gaming_card)
                print("[MSN GAME] Gaming card found")
                time.sleep(calculateSleep(10))
            if scrolls == 5 and not gaming_card:
                raise NoSuchElementException("Gaming card not found")
        print("[MSN GAME] Answering questions ...")
        for question in range(10):
            try:
                print(f"[MSN GAME] Answering {question}/10", end="\r")
                clickCorrectAnswer()
                clickPlayAgain()
                time.sleep(calculateSleep(10))
            except (NoSuchElementException, JavascriptException):
                break
    except NoSuchElementException:
        prYellow("[MSN GAME] Failed to locate MSN shopping game !")
        finished = False
    except GamingCardIsNotActive:
        prGreen("[MSN] Quiz has been already completed !")
        finished = True
    except Exception as exc:  # skipcq
        displayError(exc)
        prYellow("[MSN GAME] Failed to complete MSN shopping game !")
        finished = False
    else:
        prGreen("[MSN GAME] Completed MSN shopping game successfully !")
        finished = True
    finally:
        goToURL(browser, BASE_URL)
        LOGS[CURRENT_ACCOUNT]["MSN shopping game"] = True
        updateLogs()
        return finished


def getRemainingSearches(browser: WebDriver):
    """get remaining searches"""
    dashboard = getDashboardData(browser)
    searchPoints = 1
    counters = dashboard['userStatus']['counters']
    if not 'pcSearch' in counters:
        return 0, 0
    progressDesktop = counters['pcSearch'][0]['pointProgress'] + \
        counters['pcSearch'][1]['pointProgress']
    targetDesktop = counters['pcSearch'][0]['pointProgressMax'] + \
        counters['pcSearch'][1]['pointProgressMax']
    if targetDesktop == 33:
        # Level 1 EU
        searchPoints = 3
    elif targetDesktop == 55:
        # Level 1 US
        searchPoints = 5
    elif targetDesktop == 102:
        # Level 2 EU
        searchPoints = 3
    elif targetDesktop >= 170:
        # Level 2 US
        searchPoints = 5
    remainingDesktop = int((targetDesktop - progressDesktop) / searchPoints)
    remainingMobile = 0
    if dashboard['userStatus']['levelInfo']['activeLevel'] != "Level1":
        progressMobile = counters['mobileSearch'][0]['pointProgress']
        targetMobile = counters['mobileSearch'][0]['pointProgressMax']
        remainingMobile = int((targetMobile - progressMobile) / searchPoints)
    return remainingDesktop, remainingMobile


def getRedeemGoal(browser: WebDriver):
    """get redeem goal"""
    user_status = getDashboardData(browser)["userStatus"]
    return user_status["redeemGoal"]["title"], user_status["redeemGoal"]["price"]


def isElementExists(browser: WebDriver, _by: By, element: str) -> bool:
    """Returns True if given element exists else False"""
    try:
        browser.find_element(_by, element)
    except NoSuchElementException:
        return False
    return True


def accountBrowser(chosen_account: str):
    """Setup browser for chosen account"""
    global CURRENT_ACCOUNT  # pylint: disable=global-statement
    for account in ACCOUNTS:
        if account["username"].lower() == chosen_account.lower():
            CURRENT_ACCOUNT = account["username"]
            break
    else:
        return None
    proxy = account.get('proxy', None)
    browser = browserSetup(False, PC_USER_AGENT, proxy)
    return browser


def argumentParser():
    """getting args from command line"""

    def isValidTime(validtime: str):
        """check the time format and return the time if it is valid, otherwise return parser error"""
        try:
            t = datetime.strptime(validtime, "%H:%M").strftime("%H:%M")
        except ValueError:
            parser.error("Invalid time format, use HH:MM")
        else:
            return t

    def isSessionExist(session: str):
        """check if the session is valid and return the session if it is valid, otherwise return parser error"""
        if Path(f"{Path(__file__).parent}/Profiles/{session}").exists():
            return session
        else:
            parser.error(f"Session not found for {session}")

    def isAccountfileExists(accountfile: str):
        if Path(f"{Path(__file__).parent}/{accountfile}").is_file():
            return accountfile
        else:
            parser.error(f"Account file not found for {accountfile}")
    
    parser = ArgumentParser(
        description=f"Microsoft Rewards Farmer {version}",
        allow_abbrev=False,
        usage="You may use execute the program with the default config or use arguments to configure available options."
    )
    parser.add_argument('--everyday',
                        action='store_true',
                        help='This argument will make the script run everyday at the time you start.',
                        required=False)
    parser.add_argument('--headless',
                        help='Enable headless browser.',
                        action='store_true',
                        required=False)
    parser.add_argument('--session',
                        help='Creates session for each account and use it.',
                        action='store_true',
                        required=False)
    parser.add_argument('--error',
                        help='Display errors when app fails.',
                        action='store_true',
                        required=False)
    parser.add_argument('--fast',
                        help="Reduce delays where ever it's possible to make script faster.",
                        action='store_true',
                        required=False)
    parser.add_argument('--superfast',
                        help="Reduce delays where ever it's possible even further than fast mode to make script faster.",
                        action='store_true',
                        required=False)
    parser.add_argument('--telegram',
                        metavar=('<API_TOKEN>', '<CHAT_ID>'),
                        nargs=2,
                        help='This argument takes token and chat id to send logs to Telegram.',
                        type=str,
                        required=False)
    parser.add_argument('--discord',
                        metavar='<WEBHOOK_URL>',
                        nargs=1,
                        help='This argument takes webhook url to send logs to Discord.',
                        type=str,
                        required=False)
    parser.add_argument('--edge',
                        help='Use Microsoft Edge webdriver instead of Chrome.',
                        action='store_true',
                        required=False)
    parser.add_argument('--account-browser',
                        nargs=1,
                        type=isSessionExist,
                        help='Open browser session for chosen account.',
                        required=False)
    parser.add_argument('--start-at',
                        metavar='<HH:MM>',
                        help='Start the script at the specified time in 24h format (HH:MM).',
                        nargs=1,
                        type=isValidTime)
    parser.add_argument("--on-finish",
                        help="Action to perform on finish from one of the following: shutdown, sleep, hibernate, exit",
                        choices=["shutdown", "sleep", "hibernate", "exit"],
                        required=False,
                        metavar="ACTION")
    parser.add_argument("--redeem",
                        help="Enable auto-redeem rewards based on accounts.json goals.",
                        action="store_true",
                        required=False)
    parser.add_argument("--calculator",
                        help="MS Rewards Calculator",
                        action='store_true',
                        required=False)
    parser.add_argument("--skip-unusual",
                        help="Skip unusual activity detection.",
                        action="store_true",
                        required=False)
    parser.add_argument("--skip-shopping",
                        help="Skip MSN shopping game. Useful for people living in regions which do not support MSN Shopping.",
                        action="store_true",
                        required=False)
    parser.add_argument("--no-images",
                        help="Prevent images from loading to increase performance.",
                        action="store_true",
                        required=False)
    parser.add_argument("--shuffle",
                        help="Randomize the order in which accounts are farmed.",
                        action="store_true",
                        required=False)
    parser.add_argument("--no-webdriver-manager",
                        help="Use system installed webdriver instead of webdriver-manager.",
                        action="store_true",
                        required=False)
    parser.add_argument("--currency",
                        help="Converts your points into your preferred currency.",
                        choices=["EUR", "USD", "AUD", "INR", "GBP", "CAD", "JPY",
                                 "CHF", "NZD", "ZAR", "BRL", "CNY", "HKD", "SGD", "THB"],
                        action="store",
                        required=False)
    parser.add_argument("--virtual-display",
                        help="Use PyVirtualDisplay (intended for Raspberry Pi users).",
                        action="store_true",
                        required=False)
    parser.add_argument("--dont-check-for-updates",
                        help="Prevent script from updating.",
                        action="store_true",
                        required=False)
    parser.add_argument("--repeat-shopping",
                        help="Repeat MSN shopping so it runs twice per account.",
                        action="store_true",
                        required=False)
    parser.add_argument("--skip-if-proxy-dead",
                        help="Skips the account when provided Proxy is dead/ not working",
                        action="store_true",
                        required=False)
    parser.add_argument("--dont-check-internet",
                        help="Prevent script from checking internet connection.",
                        action="store_true",
                        required=False)
    parser.add_argument("--print-to-webhook",
                        help="Print every message to webhook.",
                        action="store_true",
                        required=False)
    parser.add_argument("--recheck-proxy",
                        help="Rechecks proxy in case you face proxy dead error",
                        action="store_true",
                        required=False)
    parser.add_argument("--accounts-file",
                        help="Specify the name of the accounts file in bot directory.",
                        metavar="<FILE NAME>",
                        required=False,
                        nargs=1,
                        type=isAccountfileExists)
    
    args = parser.parse_args()
    if args.superfast or args.fast:
        global SUPER_FAST, FAST  # pylint: disable=global-statement
        SUPER_FAST = args.superfast
        if args.fast and not args.superfast:
            FAST = True
    return args


def logs():
    """Read logs and check whether account farmed or not"""
    global LOGS  # pylint: disable=global-statement
    shared_items = []
    try:
        # Read datas on 'logs_accounts.txt'
        LOGS = json.load(
            open(f"{Path(__file__).parent}/Logs_{ACCOUNTS_PATH.stem}.txt", "r"))
        LOGS.pop("Elapsed time", None)
        # sync accounts and logs file for new accounts or remove accounts from logs.
        for user in ACCOUNTS:
            shared_items.append(user['username'])
            if not user['username'] in LOGS.keys():
                LOGS[user["username"]] = {"Last check": "",
                                          "Today's points": 0,
                                          "Points": 0}
        if shared_items != LOGS.keys():
            diff = LOGS.keys() - shared_items
            for accs in list(diff):
                del LOGS[accs]

        # check that if any of accounts has farmed today or not.
        for account in LOGS.keys():
            if LOGS[account]["Last check"] == str(date.today()) and list(LOGS[account].keys()) == ['Last check',
                                                                                                   "Today's points",
                                                                                                   'Points']:
                FINISHED_ACCOUNTS.append(account)
            elif LOGS[account]['Last check'] == 'Your account has been suspended':
                FINISHED_ACCOUNTS.append(account)
            elif LOGS[account]['Last check'] == str(date.today()) and list(LOGS[account].keys()) == [
                'Last check',
                "Today's points",
                'Points',
                'Daily',
                'Punch cards',
                'More promotions',
                'MSN shopping game',
                'PC searches'
            ]:
                continue
            else:
                LOGS[account]['Daily'] = False
                LOGS[account]['Punch cards'] = False
                LOGS[account]['More promotions'] = False
                LOGS[account]['MSN shopping game'] = False
                LOGS[account]['PC searches'] = False
            if not isinstance(LOGS[account]["Points"], int):
                LOGS[account]["Points"] = 0
        updateLogs()
        prGreen('\n[LOGS] Logs loaded successfully.\n')
    except FileNotFoundError:
        prRed(f'\n[LOGS] "Logs_{ACCOUNTS_PATH.stem}.txt" file not found.')
        LOGS = {}
        for account in ACCOUNTS:
            LOGS[account["username"]] = {"Last check": "",
                                         "Today's points": 0,
                                         "Points": 0,
                                         "Daily": False,
                                         "Punch cards": False,
                                         "More promotions": False,
                                         "MSN shopping game": False,
                                         "PC searches": False}
        updateLogs()
        prGreen(f'[LOGS] "Logs_{ACCOUNTS_PATH.stem}.txt" created.\n')
    except json.decoder.JSONDecodeError as e:
        prRed("\n[LOGS] Invalid JSON format in logs file, try to delete logs or fix the error then try again.")
        prRed(str(e))
        input("Press enter to close...")
        os._exit(0)


def updateLogs():
    """update logs"""
    _logs = copy.deepcopy(LOGS)
    for account in _logs:
        if account == "Elapsed time":
            continue
        _logs[account].pop("Redeem goal title", None)
        _logs[account].pop("Redeem goal price", None)
    with open(f'{Path(__file__).parent}/Logs_{ACCOUNTS_PATH.stem}.txt', 'w') as file:
        file.write(json.dumps(_logs, indent=4))


def cleanLogs():
    """clean logs"""
    LOGS[CURRENT_ACCOUNT].pop("Daily", None)
    LOGS[CURRENT_ACCOUNT].pop("Punch cards", None)
    LOGS[CURRENT_ACCOUNT].pop("More promotions", None)
    LOGS[CURRENT_ACCOUNT].pop("MSN shopping game", None)
    LOGS[CURRENT_ACCOUNT].pop("PC searches", None)


def finishedAccount():
    """terminal print when account finished"""
    New_points = POINTS_COUNTER - STARTING_POINTS
    prGreen('[POINTS] You have earned ' + str(New_points) + ' points today !')
    prGreen('[POINTS] You are now at ' + str(POINTS_COUNTER) + ' points !\n')

    FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
    if LOGS[CURRENT_ACCOUNT]["Points"] > 0 and POINTS_COUNTER >= LOGS[CURRENT_ACCOUNT]["Points"]:
        LOGS[CURRENT_ACCOUNT]["Today's points"] = POINTS_COUNTER - \
            LOGS[CURRENT_ACCOUNT]["Points"]
    else:
        LOGS[CURRENT_ACCOUNT]["Today's points"] = New_points
    LOGS[CURRENT_ACCOUNT]["Points"] = POINTS_COUNTER


def checkInternetConnection():
    """Check if you're connected to the inter-web superhighway"""
    if ARGS.dont_check_internet:
        return
    system = platform.system()
    while True:
        try:
            if system == "Windows":
                subprocess.check_output(
                    ["ping", "-n", "1", "8.8.8.8"], timeout=5)
            elif system == "Linux":
                subprocess.check_output(
                    ["ping", "-c", "1", "8.8.8.8"], timeout=5)
            return
        except subprocess.TimeoutExpired:
            prRed("[ERROR] No internet connection.")
            time.sleep(1)
        except FileNotFoundError:
            return
        except:
            return


def format_currency(points, currency):
    """
    Formats the given amount as a currency string.

    Args:
        amount (float): The amount to format.
        currency (str, optional): The currency code to use for formatting. Defaults to None.

    Returns:
        str: The formatted currency string.
    """
    convert = {
        "EUR": {"rate": 1500, "symbol": "€"},
        "AUD": {"rate": 1350, "symbol": "AU$"},
        "INR": {"rate": 16, "symbol": "₹"},
        "USD": {"rate": 1300, "symbol": "$"},
        "GBP": {"rate": 1700, "symbol": "£"},
        "CAD": {"rate": 1000, "symbol": "CA$"},
        "JPY": {"rate": 12, "symbol": "¥"},
        "CHF": {"rate": 1400, "symbol": "CHF"},
        "NZD": {"rate": 1200, "symbol": "NZ$"},
        "ZAR": {"rate": 90, "symbol": "R"},
        "BRL": {"rate": 250, "symbol": "R$"},
        "CNY": {"rate": 200, "symbol": "¥"},
        "HKD": {"rate": 170, "symbol": "HK$"},
        "SGD": {"rate": 950, "symbol": "S$"},
        "THB": {"rate": 40, "symbol": "฿"}
    }
    return f"{convert[currency]['symbol']}{points / convert[currency]['rate']:0.02f}"


def createMessage():
    """Create message"""
    today = date.today().strftime("%d/%m/%Y")
    total_earned = 0
    total_overall = 0
    message = f'📅 Daily report {today}\n\n'
    for index, value in enumerate(LOGS.items(), 1):
        redeem_message = None
        if value[1].get("Redeem goal title", None):
            redeem_title = value[1].get("Redeem goal title", None)
            redeem_price = value[1].get("Redeem goal price")
            redeem_count = value[1]["Points"] // redeem_price
            if ARGS.redeem:
                # only run if args.redeem mate
                if value[1]['Auto redeem']:
                    redeem_message = f"🎁 Auto redeem: {value[1]['Auto redeem']} {redeem_title} for {redeem_price} points ({redeem_count}x)\n\n"
            elif redeem_count > 1:
                redeem_message = f"🎁 Ready to redeem: {redeem_title} for {redeem_price} points ({redeem_count}x)\n\n"
            else:
                redeem_message = f"🎁 Ready to redeem: {redeem_title} for {redeem_price} points\n\n"
        if value[1]['Last check'] == str(date.today()):
            status = '✅ Farmed'
            new_points = value[1]["Today's points"]
            total_earned += new_points
            total_points = value[1]["Points"]
            total_overall += total_points
            message += f"{index}. {value[0]}\n📝 Status: {status}\n⭐️ Earned points: {new_points}\n🏅 Total points: {total_points}\n"
            if redeem_message:
                message += redeem_message
            else:
                message += "\n"
        elif value[1]['Last check'] == 'Your account has been suspended':
            status = '❌ Suspended'
            message += f"{index}. {value[0]}\n📝 Status: {status}\n\n"
        elif value[1]['Last check'] == 'Your account has been locked !':
            status = '⚠️ Locked'
            message += f"{index}. {value[0]}\n📝 Status: {status}\n\n"
        elif value[1]['Last check'] == 'Unusual activity detected !':
            status = '⚠️ Unusual activity detected'
            message += f"{index}. {value[0]}\n📝 Status: {status}\n\n"
        elif value[1]['Last check'] == 'Unknown error !':
            status = '⛔️ Unknown error occurred'
            message += f"{index}. {value[0]}\n📝 Status: {status}\n\n"
        elif value[1]['Last check'] == 'Your email or password was not valid !':
            status = '📛 Your email/password was invalid'
            message += f"{index}. {value[0]}\n📝 Status: {status}\n\n"
        elif value[1]['Last check'] == 'Provided Proxy is Dead, Please replace a new one and run the script again':
            status = '📛 Provided Proxy is Dead, Please replace a new one and run the script again'
            message += f"{index}. {value[0]}\n📝 Status: {status}\n\n"
        elif value[1]['Last check'] == 'Your TOTP secret was wrong !':
            status = '📛 TOTP code was wrong'
            message += f"{index}. {value[0]}\n📝 Status: {status}\n\n"
        else:
            status = f'Farmed on {value[1]["Last check"]}'
            new_points = value[1]["Today's points"]
            total_earned += new_points
            total_points = value[1]["Points"]
            total_overall += total_points
            message += f"{index}. {value[0]}\n📝 Status: {status}\n⭐️ Earned points: {new_points}\n🏅 Total points: {total_points}\n"
            if redeem_message:
                message += redeem_message
            else:
                message += "\n"
    if ARGS.currency:
        message += f"💵 Total earned points: {total_earned} "\
            f"({format_currency(total_earned, ARGS.currency)}) \n"
        message += f"💵 Total Overall points: {total_overall} "\
            f"({format_currency(total_overall, ARGS.currency)})"
    else:
        message += f"💵 Total earned points: {total_earned} "\
            f"(${total_earned / 1300:0.02f}) "\
            f"(€{total_earned / 1500:0.02f}) "\
            f"(AU${total_earned / 1350:0.02f}) "\
            f"(₹{total_earned / 16:0.02f}) \n"
        message += f"💵 Total Overall points: {total_overall} "\
            f"(${total_overall / 1300:0.02f}) "\
            f"(€{total_overall / 1500:0.02f}) "\
            f"(AU${total_overall / 1350:0.02f})"\
            f"(₹{total_overall / 16:0.02f})"

    return message


def prArgs():
    """print arguments"""
    if len(sys.argv) > 1 and not ARGS.calculator:
        total_enabled_flags = 0
        for arg in vars(ARGS):
            if getattr(ARGS, arg) is not False and getattr(ARGS, arg) is not None:
                prBlue(f"[FLAGS] {arg}: {getattr(ARGS, arg)}")
                total_enabled_flags += 1
        if total_enabled_flags == 0:
            prYellow("[FLAGS] No flags are used")


def sendReportToMessenger(message):
    """send report to messenger"""
    if ARGS.telegram:
        sendToTelegram(message)
    if ARGS.discord:
        sendToDiscord(message)


def sendToTelegram(message):
    """send to telegram"""
    t = get_notifier('telegram')
    if len(message) > 4096:
        messages = [message[i:i+4096] for i in range(0, len(message), 4096)]
        for ms in messages:
            t.notify(
                message=ms, token=ARGS.telegram[0], chat_id=ARGS.telegram[1])
    else:
        t.notify(message=message,
                 token=ARGS.telegram[0], chat_id=ARGS.telegram[1])


def sendToDiscord(message):
    """send to discord"""
    webhook_url = ARGS.discord[0]
    if len(message) > 2000:
        messages = [message[i:i + 2000] for i in range(0, len(message), 2000)]
        for ms in messages:
            content = {"username": "⭐️ Microsoft Rewards Bot ⭐️", "content": ms}
            response = requests.post(webhook_url, json=content)
    else:
        content = {"username": "⭐️ Microsoft Rewards Bot ⭐️",
                   "content": message}
        response = requests.post(webhook_url, json=content)
    if not ARGS.print_to_webhook:  # this is to prevent infinite loop
        if response.status_code == 204:
            prGreen("[LOGS] Report sent to Discord.\n")
        else:
            prRed("[ERROR] Could not send report to Discord.\n")


def setRedeemGoal(browser: WebDriver, goal: str):
    """
    Sets current account's goal for redeeming.
    @param browser - Selenium instance of the web browser.
    @param goal - Name of the goal to use.
    """
    print("[GOAL SETTER] Setting new account goal...")

    goal = goal.lower()
    goToURL(browser, "https://rewards.microsoft.com/")
    try:
        goal_name = browser.find_element(
            By.XPATH,
            value="/html/body/div[1]/div[2]/main/div/ui-view/mee-rewards-dashboard/main/div/mee-rewards-redeem-info-card/div/mee-card-group/div/div[1]/mee-card/div/card-content/mee-rewards-redeem-goal-card/div/div[2]/h3",
        )

        goal_progress = browser.find_element(
            By.XPATH,
            value="/html/body/div[1]/div[2]/main/div/ui-view/mee-rewards-dashboard/main/div/mee-rewards-redeem-info-card/div/mee-card-group/div/div[1]/mee-card/div/card-content/mee-rewards-redeem-goal-card/div/div[2]/p",
        )

        # If goal is not set or is not the specified one, then set/change it
        if "/" not in goal_progress.text.lower() or goal not in goal_name.text.lower():
            # If we need to change it, it is mandatory to refresh the set goal button
            if "/" in goal_progress.text.lower() and goal not in goal_name.text.lower():
                # Check if unspecified goal has reached 100%
                goal_progress = (
                    browser.find_element(
                        By.XPATH,
                        value="/html/body/div[1]/div[2]/main/div/ui-view/mee-rewards-dashboard/main/div/mee-rewards-redeem-info-card/div/mee-card-group/div/div[1]/mee-card/div/card-content/mee-rewards-redeem-goal-card/div/div[2]/p",
                    )
                    .text.replace(" ", "")
                    .split("/")
                )
                points = int(goal_progress[0].replace(",", ""))
                total = int(goal_progress[1].replace(",", ""))

                if points == total:
                    # Choose remove goal element instead of redeem now
                    element = browser.find_element(
                        By.XPATH,
                        value="/html/body/div[1]/div[2]/main/div/ui-view/mee-rewards-dashboard/main/div/mee-rewards-redeem-info-card/div/mee-card-group/div/div[1]/mee-card/div/card-content/mee-rewards-redeem-goal-card/div/div[2]/div/a[2]/span/ng-transclude",
                    )
                else:
                    element = browser.find_element(
                        By.XPATH,
                        value="/html/body/div[1]/div[2]/main/div/ui-view/mee-rewards-dashboard/main/div/mee-rewards-redeem-info-card/div/mee-card-group/div/div[1]/mee-card/div/card-content/mee-rewards-redeem-goal-card/div/div[2]/div/a/span/ng-transclude",
                    )

                element.click()
                time.sleep(3)
                element = browser.find_element(
                    By.XPATH,
                    value="/html/body/div[1]/div[2]/main/div/ui-view/mee-rewards-dashboard/main/div/mee-rewards-redeem-info-card/div/mee-card-group/div/div[1]/mee-card/div/card-content/mee-rewards-redeem-goal-card/div/div[2]/div/a/span/ng-transclude",
                )
            else:
                element = browser.find_element(
                    By.XPATH,
                    value="/html/body/div[1]/div[2]/main/div/ui-view/mee-rewards-dashboard/main/div/mee-rewards-redeem-info-card/div/mee-card-group/div/div[1]/mee-card/div/card-content/mee-rewards-redeem-goal-card/div/div[2]/div/a/span/ng-transclude",
                )
            element.click()
            time.sleep(3)
            elements = browser.find_elements(By.CLASS_NAME, "c-image")
            goal_found = False
            for elem in elements:
                if goal in elem.get_attribute("alt").lower():
                    elem.click()
                    goal_found = True
                    break

            if not goal_found:
                prRed(
                    "[GOAL SETTER] Specified goal not found! Search for any typos..."
                )
            else:
                prGreen("[GOAL SETTER] New account goal set successfully!")

    except (NoSuchElementException, ElementClickInterceptedException) as exc:
        prRed("[GOAL SETTER] Ran into an exception trying to redeem!")
        displayError(exc)
        return
    finally:
        goToURL(browser, BASE_URL)


def redeemGoal(browser: WebDriver):
    """
    Automatically redeems current account's goal.
    @param browser - Selenium instance of the web browser.
    """
    try:
        try:
            browser.find_element(
                By.XPATH,
                value="/html/body/div[1]/div[2]/main/div/ui-view/mee-rewards-dashboard/main/div/mee-rewards-redeem-info-card/div/mee-card-group/div/div[1]/mee-card/div/card-content/mee-rewards-redeem-goal-card/div/div[2]/div/a[1]",
            ).click()
            time.sleep(random.uniform(5, 7))
        except (NoSuchElementException, ElementClickInterceptedException):
            browser.find_element(
                By.XPATH,
                value="/html/body/div[1]/div[2]/main/div/ui-view/mee-rewards-dashboard/main/div/mee-rewards-redeem-info-card/div/mee-card-group/div/div[1]/mee-card/div/card-content/mee-rewards-redeem-goal-card/div/div[2]/div/a[1]",
            ).click()
            time.sleep(random.uniform(5, 7))

        try:
            url = browser.current_url
            url = url.split("/")
            id = url[-1]
            try:
                browser.find_element(
                    By.XPATH, value=f'//*[@id="redeem-pdp_{id}"]'
                ).click()
                time.sleep(random.uniform(5, 7))
            except (NoSuchElementException, ElementClickInterceptedException):
                browser.find_element(
                    By.XPATH, value="/html/body/div[1]/div[2]/main/div[2]/div[2]/div[3]/a[2]"
                ).click()
            # If a cookie consent container is present, we need to accept
            # those cookies to be able to redeem the reward
            if browser.find_elements(By.ID, value="wcpConsentBannerCtrl"):
                browser.find_element(
                    By.XPATH, value="/html/body/div[3]/div/div[2]/button[1]").click()
                time.sleep(random.uniform(2, 4))
            try:
                browser.find_element(
                    By.XPATH, value='//*[@id="redeem-checkout-review-confirm"]').click()
                time.sleep(random.uniform(2, 4))
            except (NoSuchElementException, ElementClickInterceptedException):
                browser.find_element(
                    By.XPATH, value='//*[@id="redeem-checkout-review-confirm"]/span[1]').click()
        except (NoSuchElementException, ElementClickInterceptedException) as exc:
            goToURL(browser, BASE_URL)
            prRed("[REDEEM] Ran into an exception trying to redeem!")
            prRed(str(exc))
            return
        # Handle phone verification landing page
        try:
            veri = browser.find_element(
                By.XPATH, value='//*[@id="productCheckoutChallenge"]/form/div[1]').text
            if veri.lower() == "phone verification":
                prRed("[REDEEM] Phone verification required!")
                LOGS[CURRENT_ACCOUNT]['Auto redeem'] = 'Phone verification required!'
                updateLogs()
                cleanLogs()
                return
        except (NoSuchElementException, ElementClickInterceptedException):
            pass
        finally:
            time.sleep(random.uniform(2, 4))
        try:
            error = browser.find_element(
                By.XPATH, value='//*[@id="productCheckoutError"]/div/div[1]').text
            if "issue with your account or order" in error.lower():
                message = f"\n[REDEEM] {CURRENT_ACCOUNT} has encountered the following message while attempting to auto-redeem rewards:\n{error}\nUnfortunately, this likely means this account has been shadow-banned. You may test your luck and contact support or just close the account and try again on another account."
                prRed(message)
                LOGS[CURRENT_ACCOUNT]['Auto redeem'] = 'Account banned!'
                updateLogs()
                cleanLogs()
                return
        except (NoSuchElementException, ElementClickInterceptedException):
            pass
        prGreen(f"[REDEEM] {CURRENT_ACCOUNT} card redeemed!")
        LOGS[CURRENT_ACCOUNT]['Auto redeem'] = 'Redeemed!'
        updateLogs()
        cleanLogs()
        global auto_redeem_counter  # pylint: disable=global-statement
        auto_redeem_counter += 1
    except (NoSuchElementException, ElementClickInterceptedException) as exc:
        prRed("[REDEEM] Ran into an exception trying to redeem!")
        prRed(str(exc))
        return


def calculateSleep(default_sleep: int):
    """
    Sleep calculated with this formular:
    on FAST: random.uniform((default_sleep/2) * 0.5, (default_sleep/2) * 1.5)
    on SUPER_FAST: random.uniform((default_sleep/4) * 0.5, (default_sleep/4) * 1.5)
    else: default_sleep
    """
    if SUPER_FAST:
        return random.uniform((default_sleep / 4) * 0.5, (default_sleep / 4) * 1.5)
    elif FAST:
        return random.uniform((default_sleep / 2) * 0.5, (default_sleep / 2) * 1.5)
    else:
        return default_sleep


def prRed(prt):
    """colour print"""
    if ARGS.print_to_webhook:
        return print(prt)
    print(f"\033[91m{prt}\033[00m")


def prGreen(prt):
    """colour print"""
    if ARGS.print_to_webhook:
        return print(prt)
    print(f"\033[92m{prt}\033[00m")


def prYellow(prt):
    """colour print"""
    if ARGS.print_to_webhook:
        return print(prt)
    print(f"\033[93m{prt}\033[00m")


def prBlue(prt):
    """colour print"""
    if ARGS.print_to_webhook:
        return print(prt)
    print(f"\033[94m{prt}\033[00m")


def prPurple(prt):
    """colour print"""
    if ARGS.print_to_webhook:
        return print(prt)
    print(f"\033[95m{prt}\033[00m")


def logo():
    """logo"""
    prRed("""
    ███╗   ███╗███████╗    ███████╗ █████╗ ██████╗ ███╗   ███╗███████╗██████╗ 
    ████╗ ████║██╔════╝    ██╔════╝██╔══██╗██╔══██╗████╗ ████║██╔════╝██╔══██╗
    ██╔████╔██║███████╗    █████╗  ███████║██████╔╝██╔████╔██║█████╗  ██████╔╝
    ██║╚██╔╝██║╚════██║    ██╔══╝  ██╔══██║██╔══██╗██║╚██╔╝██║██╔══╝  ██╔══██╗
    ██║ ╚═╝ ██║███████║    ██║     ██║  ██║██║  ██║██║ ╚═╝ ██║███████╗██║  ██║
    ╚═╝     ╚═╝╚══════╝    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝""")
    prPurple(
        f"            by @Charlesbel upgraded by @Farshadz1997        version {version}\n")


def tkinter_calculator():
    """Rewards Calculator GUI"""
    microsoft = 4750  # price of microsoft/xbox gift cards
    non_microsoft = 6750  # price of 3rd party gift cards

    # Create a new Tkinter window
    window = tk.Tk()
    window.title("RewardStimator - Microsoft Rewards Bot Estimator")
    window.geometry("500x280")
    window.resizable(False, False)

    # Add a title label
    title_label = ttk.Label(
        window, text="RewardStimator", font=("Helvetica", 16))
    title_label.pack(pady=10)

    # Create a frame for the form fields
    form_frame = ttk.Frame(window)
    form_frame.pack(pady=10)

    def validate_float_input(value):
        """validate input if it is float"""
        for i, _ in enumerate(value):
            if value[i] not in '0123456789.':
                return False

        # only allow 1 full stop
        if value.count(".") > 1:
            return False

        if "." in value and len(value.split(".", 1)[1]) > 2:
            return False

        return True

    def validate_numeric_input(value):
        """validate input if it is integer"""
        for i, _ in enumerate(value):
            if value[i] not in '0123456789':
                return False

        if not value == "":
            # the above if statement is required
            # otherwise it will return an error when clicking backspace
            if (int(value) > 99) or (int(value) <= 0):
                return False

        return True

    # Add a label for the price field
    price_label = ttk.Label(form_frame, text="Price:")
    price_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

    # Add an entry widget for the price field
    price_entry = ttk.Entry(form_frame, width=20, validate="key")
    price_entry.grid(row=0, column=1, padx=5, pady=5)
    price_entry.configure(validatecommand=(
        price_entry.register(validate_float_input), '%P'))

    # Add a label for the accounts field
    accounts_label = ttk.Label(form_frame, text="Accounts:")
    accounts_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

    # Add an entry widget for the accounts field
    accounts_entry = ttk.Entry(form_frame, width=20, validate="key")
    accounts_entry.grid(row=1, column=1, padx=5, pady=5)
    accounts_entry.configure(validatecommand=(
        accounts_entry.register(validate_numeric_input), '%P'))

    # Add a label for the balance field
    balance_label = ttk.Label(form_frame, text="Current Balance (default 0):")
    balance_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")

    # Add an entry widget for the balance field
    balance_entry = ttk.Entry(form_frame, width=20, validate="key")
    balance_entry.grid(row=2, column=1, padx=5, pady=5)
    balance_entry.configure(validatecommand=(
        balance_entry.register(validate_float_input), '%P'))

    # Add a label for the daily points field
    daily_points_label = ttk.Label(form_frame, text="Estimated daily points:")
    daily_points_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")

    # Estimated daily points
    estimated_daily_points = ttk.Entry(form_frame, width=20, validate="key")
    estimated_daily_points.grid(row=3, column=1, padx=5, pady=5)
    estimated_daily_points.configure(validatecommand=(
        estimated_daily_points.register(validate_float_input), '%P'))

    # Add a label for the associated field
    associated_label = ttk.Label(
        form_frame, text="Microsoft Associated Gift Card:")
    associated_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")

    # Add radio buttons for the associated field
    associated_var = tk.BooleanVar()
    yes_radio = ttk.Radiobutton(
        form_frame, text="Yes", variable=associated_var, value=True)
    no_radio = ttk.Radiobutton(
        form_frame, text="No", variable=associated_var, value=False)
    yes_radio.grid(row=4, column=1, padx=5, pady=0, sticky="w")
    no_radio.grid(row=4, column=1, padx=5, pady=0, sticky="e")

    # Function to submit the form
    def submit():
        """run on submit button pressed"""
        price = price_entry.get()
        accounts = accounts_entry.get()
        balance = balance_entry.get()
        daily_points = estimated_daily_points.get()
        associated = associated_var.get()

        # Validate form data
        if not price or not accounts:
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        try:
            price = float(price)
            accounts = int(accounts)
            balance = float(balance) if balance != "" else 0
            daily_points = float(estimated_daily_points.get())
        except ValueError:
            messagebox.showerror("Critical Error, now closing...")
            sys.exit("Error (ValueError)")

        non = '' if associated else 'Non-'
        cards_required = ceil((price - balance) / 5)
        cr_per_acc = ceil(cards_required / accounts)  # cards per account
        excess = (cr_per_acc * accounts * 5) - price + balance
        elapsed_time = ceil(
            ((microsoft if associated else non_microsoft) / daily_points) * cr_per_acc)

        if cards_required <= 0:
            messagebox.showerror(
                "Error", "Current balance is higher or equal to price.")
            return

        messagebox.showinfo("RewardStimator Result", f""
                                                     f"Total $5 {non}Microsoft gift cards required: {cards_required}"
                                                     f"\n{non}Microsoft gift cards required per account: {cr_per_acc}"
                                                     f"\nExcess: ${excess:.2f}"
                                                     f"\nEstimated elapsed elapsed_time: ~{elapsed_time} days\n")

    submit_button = ttk.Button(window, text="Submit", command=submit)
    submit_button.pack(pady=10)

    window.mainloop()


def loadAccounts():
    """get or create accounts.json"""
    global ACCOUNTS, ACCOUNTS_PATH  # pylint: disable=global-statement
    try:
        if ARGS.accounts_file:
            ACCOUNTS_PATH = Path(__file__).parent / ARGS.accounts_file[0]
        else:
            ACCOUNTS_PATH = Path(__file__).parent / 'accounts.json'
        ACCOUNTS = json.load(open(ACCOUNTS_PATH, "r"))
    except FileNotFoundError:
        with open(ACCOUNTS_PATH, 'w') as f:
            f.write(json.dumps([{
                "username": "Your Email",
                "password": "Your Password"
            }], indent=4))
        prPurple(f"[ACCOUNT] Accounts credential file '{ACCOUNTS_PATH.name}' created."
                 "\n[ACCOUNT] Edit with your credentials and save, then press any key to continue...")
        input()
        ACCOUNTS = json.load(open(ACCOUNTS_PATH, "r"))
    except json.decoder.JSONDecodeError as e:
        prRed("\n[ACCOUNTS] Invalid JSON format in accounts file.")
        prRed(str(e))
        input("Press enter to close...")
        os._exit(0)
    finally:
        if ARGS.shuffle:
            random.shuffle(ACCOUNTS)


def update_handler(local_version):
    """Checks if the update is the latest"""
    # Check if version is unknown
    if local_version == "Unknown":
        prRed("Update handler will not run due to the local version being unknown.")

    # initialize functions
    def loadingbar(configuration: dict, skip_text_after_loading_bar_finished) -> None:
        """
        eg. Loading response... [#########################]
        config = {
            "text_after_loading_bar_finished": "Successfully loaded",
            "text_before_loading_bar": "Loading response... ",
            "size_of_loading_bar": 25,
            "delay": 0.05,
            "design_of_loaded_bar": "#",
            "design_of_unloaded_bar": "."
        }
        """
        for i in range(configuration["size_of_loading_bar"]):
            sys.stdout.write(configuration["text_before_loading_bar"] + "[{0}]   \r".format(
                configuration["design_of_loaded_bar"] * (i + 1) + configuration["design_of_unloaded_bar"] * (
                    (configuration["size_of_loading_bar"] - 1) - i)))
            sys.stdout.flush()
            time.sleep(configuration["delay"])
        print(end='\x1b[2K')  # clears the line
        if not skip_text_after_loading_bar_finished:
            sys.stdout.write(configuration["text_after_loading_bar_finished"])

    def update_window(current_version, future_version, feature_list) -> None:
        """Creates tkinter window which shows available update, and it's feature list"""
        # Create the Tkinter window
        window = tk.Tk()
        window.title("New Version Available")
        window.geometry("500x400")
        window.configure(bg="#fff")
        window.resizable(False, False)
        # Add some styling
        style = ttk.Style()
        style.configure("Title.TLabel", font=(
            "Segoe UI", 16, "bold"), background="#fff", foreground="#1E90FF")
        style.configure("Feature.TLabel", font=("Segoe UI", 12),
                        background="#fff", foreground="#333")
        style.configure("Listbox.TListbox", font=(
            "Segoe UI", 12), foreground="#fff")
        # Add a label indicating a new version is available
        version_label = ttk.Label(
            window, text="A New Version is Available!", style="Title.TLabel", background="#fff")
        version_label.pack(padx=20, pady=20)
        update_label = ttk.Label(window,
                                 text=f"The current version downloaded on your device is outdated ({current_version}). A new update is available ({future_version}). To update use 'py update.py --update'.\nChange log:",
                                 style="Feature.TLabel", background="#fff", wraplength="460")
        update_label.pack(padx=20, pady=0, anchor=tk.W)
        # Add a listbox displaying features
        listbox_frame = ttk.Frame(window)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        listbox = tk.Listbox(listbox_frame, width=50, height=5, font=("Segoe UI", 12), background="#fff",
                             foreground="#333",
                             highlightthickness=0, bd=0, selectbackground="#1E90FF", selectforeground="#FFF",
                             relief=tk.FLAT, exportselection=False, activestyle="none", takefocus=False)
        for feature in feature_list:
            listbox.insert(tk.END, feature)
        listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True, anchor=tk.CENTER)
        # Start the Tkinter event loop
        window.mainloop()

    # function variables
    repo = r"https://raw.githubusercontent.com/farshadz1997/Microsoft-Rewards-bot/master"

    # create loading bar
    loadingbar({
        "text_after_loading_bar_finished": "",
        "text_before_loading_bar": "[UPDATER] Getting latest version from the internet...",
        "size_of_loading_bar": 25,
        "delay": 0.05,
        "design_of_loaded_bar": "#",
        "design_of_unloaded_bar": "."
    }, True)

    # GET THE LATEST VERSION - the following line if the url ends in '/'
    repo = f'{repo}version.json' if repo[-1] == "/" else f'{repo}/version.json'
    try:
        latest_version = requests.get(repo)
    except requests.exceptions.RequestException as exc:
        print("[UPDATER] Unable to check latest version. ")
        print(exc if ERROR else "")
        return

    # Error handling
    if latest_version.status_code != 200:
        print(
            f"[UPDATER] Unable to check latest version (Status: {latest_version.status_code})")
        return

    try:
        response = json.loads(latest_version.text)
    except json.JSONDecodeError:
        print("[UPDATER] Unable to check latest version (JSONDecodeError)")
        return

    # COMPARE LOCAL AND LATEST VERSION
    if local_version != response["version"]:
        if not (ARGS.headless or ARGS.virtual_display):
            update_window(
                local_version, response['version'], response['changelog'])
        prRed(f"\n[UPDATER] Your version ({local_version}) is outdated. "
              f"Please update to {response['version']} using 'py update.py --update'.")
        return
    print(f"[UPDATER] Your version ({local_version}) is up to date!")


def farmer():
    """function that runs other functions to farm."""
    global ERROR, MOBILE, CURRENT_ACCOUNT, STARTING_POINTS  # pylint: disable=global-statement
    try:
        for account in ACCOUNTS:
            CURRENT_ACCOUNT = account['username']
            if CURRENT_ACCOUNT in FINISHED_ACCOUNTS:
                continue
            if LOGS[CURRENT_ACCOUNT]["Last check"] != str(date.today()):
                LOGS[CURRENT_ACCOUNT]["Last check"] = str(date.today())
                updateLogs()
            prYellow('********************' +
                     CURRENT_ACCOUNT + '********************')
            if not LOGS[CURRENT_ACCOUNT]['PC searches']:
                browser = browserSetup(
                    False,
                    PC_USER_AGENT,
                    account.get('proxy', None)
                )
                print('[LOGIN]', 'Logging-in...')
                login(browser, account['username'], account['password'], account.get(
                    'totpSecret', None))
                prGreen('[LOGIN] Logged-in successfully !')
                STARTING_POINTS = POINTS_COUNTER
                prGreen('[POINTS] You have ' + str(POINTS_COUNTER) +
                        ' points on your account !')
                goToURL(browser, BASE_URL)
                waitUntilVisible(browser, By.ID, 'app-host', 30)
                redeem_goal_title, redeem_goal_price = getRedeemGoal(browser)

                # Update goal if it is not the required one for auto-redeem
                if ARGS.redeem:
                    if 'goal' in account and not account['goal'].lower() in redeem_goal_title:
                        # Account goal does not match its json goal
                        goal = account["goal"].lower()
                    elif 'Amazon' not in redeem_goal_title:
                        # Account goal needs to have the default goal
                        print(
                            '[REDEEM] Goal has not been defined for this account, defaulting to Amazon gift card...'
                        )
                        goal = "amazon"
                    else:
                        # Goal is ok for this account
                        goal = ''
                    if goal != '':
                        # Goal needs to be updated
                        setRedeemGoal(browser, goal)
                        redeem_goal_title, redeem_goal_price = getRedeemGoal(
                            browser)

                if not LOGS[CURRENT_ACCOUNT]['Daily']:
                    completeDailySet(browser)
                if not LOGS[CURRENT_ACCOUNT]['Punch cards']:
                    completePunchCards(browser)
                if not LOGS[CURRENT_ACCOUNT]['More promotions']:
                    completeMorePromotions(browser)
                if not ARGS.skip_shopping and not LOGS[CURRENT_ACCOUNT]['MSN shopping game']:
                    finished = False
                    if ARGS.repeat_shopping:
                        finished = completeMSNShoppingGame(browser)
                        prYellow(
                            "Running repeated MSN shopping. It will likely result in error due to msn shopping likely completed")
                    if not finished:
                        completeMSNShoppingGame(browser)
                remainingSearches, remainingSearchesM = getRemainingSearches(
                    browser)
                MOBILE = bool(remainingSearchesM)
                if remainingSearches != 0:
                    print('[BING]', 'Starting Desktop and Edge Bing searches...')
                    bingSearches(browser, remainingSearches)
                    prGreen(
                        '\n[BING] Finished Desktop and Edge Bing searches !')
                LOGS[CURRENT_ACCOUNT]['PC searches'] = True
                updateLogs()
                ERROR = False
                browser.quit()

            if MOBILE:
                browser = browserSetup(
                    True,
                    account.get('mobile_user_agent', MOBILE_USER_AGENT),
                    account.get('proxy', None)
                )
                print('[LOGIN]', 'Logging-in mobile...')
                login(browser, account['username'], account['password'], account.get(
                    'totpSecret', None), True)
                prGreen('[LOGIN] Logged-in successfully !')
                if LOGS[account['username']]['PC searches'] and ERROR:
                    STARTING_POINTS = POINTS_COUNTER
                    goToURL(browser, BASE_URL)
                    waitUntilVisible(browser, By.ID, 'app-host', 30)
                    redeem_goal_title, redeem_goal_price = getRedeemGoal(
                        browser)
                    remainingSearches, remainingSearchesM = getRemainingSearches(
                        browser)
                if remainingSearchesM != 0:
                    print('[BING]', 'Starting Mobile Bing searches...')
                    bingSearches(browser, remainingSearchesM, True)
                    prGreen('\n[BING] Finished Mobile Bing searches !')
                browser.quit()

            if redeem_goal_title != "" and redeem_goal_price <= POINTS_COUNTER:
                prGreen(
                    f"[POINTS] Account ready to redeem {redeem_goal_title} for {redeem_goal_price} points.")
                if ARGS.redeem and auto_redeem_counter < MAX_REDEEMS:
                    # Start auto-redeem process
                    browser = browserSetup(
                        False, PC_USER_AGENT, account.get('proxy', None))
                    print('[LOGIN]', 'Logging-in...')
                    login(browser, account['username'], account['password'], account.get(
                        'totpSecret', None))
                    prGreen('[LOGIN] Logged-in successfully!')
                    goToURL(browser, BASE_URL)
                    waitUntilVisible(browser, By.ID, 'app-host', 30)
                    redeemGoal(browser)
                if ARGS.telegram or ARGS.discord:
                    LOGS[CURRENT_ACCOUNT]["Redeem goal title"] = redeem_goal_title
                    LOGS[CURRENT_ACCOUNT]["Redeem goal price"] = redeem_goal_price
            finishedAccount()
            cleanLogs()
            updateLogs()

    except FunctionTimedOut:
        prRed('[ERROR] Time out raised.\n')
        ERROR = True
        browser.quit()
        farmer()

    except SessionNotCreatedException:
        prBlue('[Driver] Session not created.')
        prBlue(
            '[Driver] Please download correct version of webdriver form link below:')
        prBlue('[Driver] https://chromedriver.chromium.org/downloads')
        input('Press any key to close...')
        sys.exit()

    except KeyboardInterrupt:
        ERROR = True
        browser.quit()
        try:
            input(
                '\n\033[94m[INFO] Farmer paused. Press enter to continue...\033[00m\n')
            farmer()
        except KeyboardInterrupt:
            sys.exit("Force Exit (ctrl+c)")

    except ProxyIsDeadException:
        LOGS[CURRENT_ACCOUNT]['Last check'] = 'Provided Proxy is Dead, Please replace a new one and run the script again'
        FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
        updateLogs()
        cleanLogs()
        prPurple(
            '\n[PROXY] Your Provided Proxy is Dead, Please replace a new one and run the script again\n')
        checkInternetConnection()
        farmer()

    except TOTPInvalidException:
        browser.quit()
        LOGS[CURRENT_ACCOUNT]['Last check'] = 'Your TOTP secret was wrong !'
        FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
        updateLogs()
        cleanLogs()
        prRed('[ERROR] Your TOTP secret was wrong !')
        checkInternetConnection()
        farmer()

    except AccountLockedException:
        browser.quit()
        LOGS[CURRENT_ACCOUNT]['Last check'] = 'Your account has been locked !'
        FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
        updateLogs()
        cleanLogs()
        prRed('[ERROR] Your account has been locked !')
        checkInternetConnection()
        farmer()

    except InvalidCredentialsException:
        browser.quit()
        LOGS[CURRENT_ACCOUNT]['Last check'] = 'Your email or password was not valid !'
        FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
        updateLogs()
        cleanLogs()
        prRed('[ERROR] Your Email or password was not valid !')
        checkInternetConnection()
        farmer()

    except UnusualActivityException:
        browser.quit()
        LOGS[CURRENT_ACCOUNT]['Last check'] = 'Unusual activity detected !'
        FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
        updateLogs()
        cleanLogs()
        prRed("[ERROR] Unusual activity detected !")
        checkInternetConnection()
        farmer()

    except AccountSuspendedException:
        browser.quit()
        LOGS[CURRENT_ACCOUNT]['Last check'] = 'Your account has been suspended'
        LOGS[CURRENT_ACCOUNT]["Today's points"] = 'N/A'
        LOGS[CURRENT_ACCOUNT]["Points"] = 'N/A'
        cleanLogs()
        updateLogs()
        FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
        checkInternetConnection()
        farmer()

    except RegionException:
        browser.quit()
        if account.get("proxy", False):
            LOGS[CURRENT_ACCOUNT]['Last check'] = 'Unusual activity detected !'
            FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
            updateLogs()
            cleanLogs()
            prRed("[ERROR] Unusual activity detected !")
            checkInternetConnection()
            farmer()
        else:
            prRed('[ERROR] Microsoft Rewards is not available in this country or region !')
            input('[ERROR] Press any key to close...')
            os._exit(0)
    
    except DashboardException:
        browser.quit()
        LOGS[CURRENT_ACCOUNT]["Last check"] = "Unknown error !"
        FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
        updateLogs()
        cleanLogs()
        checkInternetConnection()
        farmer()

    except Exception as e:
        if "executable needs to be in PATH" in str(e):
            prRed('[ERROR] WebDriver not found.\n')
            prRed(str(e))
            input("Press Enter to close...")
            os._exit(0)
        displayError(e)
        print('\n')
        ERROR = True
        if browser is not None:
            browser.quit()
        checkInternetConnection()
        farmer()

    else:
        if ARGS.telegram or ARGS.discord:
            message = createMessage()
            sendReportToMessenger(message)
        FINISHED_ACCOUNTS.clear()


def main():
    """main"""
    global LANG, GEO, TZ  # pylint: disable=global-statement
    if not platform.system() == "Linux":
        # show colors in terminal
        os.system('color')
    # MS REWARD CALCULATOR
    if ARGS.calculator:
        tkinter_calculator()
        return sys.exit(0)
    logo()
    prArgs()
    loadAccounts()

    LANG, GEO, TZ = getCCodeLangAndOffset()
    if ARGS.account_browser:
        prBlue(f"\n[INFO] Opening session for {ARGS.account_browser[0]}")
        browser = accountBrowser(ARGS.account_browser[0])
        input("Press Enter to close when you finished...")
        if browser is not None:
            browser.quit()
    run_at = None
    if ARGS.start_at:
        run_at = ARGS.start_at[0]
    elif ARGS.everyday and ARGS.start_at is None:
        run_at = datetime.now().strftime("%H:%M")
        prBlue(f"\n[INFO] Starting everyday at {run_at}.")

    if ARGS.virtual_display:
        createDisplay()

    if run_at is not None:
        prBlue(f"\n[INFO] Farmer will start at {run_at}")
        while True:
            if datetime.now().strftime("%H:%M") == run_at:
                if not ARGS.dont_check_for_updates:
                    update_handler(version)
                start = time.time()
                logs()
                farmer()
                if not ARGS.everyday:
                    break
            time.sleep(30)
    else:
        start = time.time()
        if not ARGS.dont_check_for_updates:
            update_handler(version)  # CHECK FOR UPDATES
        logs()
        farmer()
    end = time.time()
    delta = end - start
    hour, remain = divmod(delta, 3600)
    minutes, sec = divmod(remain, 60)
    print(f"Farmer finished in: {hour:02.0f}:{minutes:02.0f}:{sec:02.0f}")
    print(f"Farmer finished on {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    LOGS["Elapsed time"] = f"{hour:02.0f}:{minutes:02.0f}:{sec:02.0f}"
    updateLogs()
    if ARGS.on_finish:
        plat = platform.system()
        if ARGS.on_finish == "shutdown":
            if plat == "Windows":
                os.system("shutdown /s /t 10")
            elif plat == "Linux":
                os.system("systemctl poweroff")
        elif ARGS.on_finish == "sleep":
            if plat == "Windows":
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            elif plat == "Linux":
                os.system("systemctl suspend")
        elif ARGS.on_finish == "hibernate":
            if plat == "Windows":
                os.system("shutdown /h")
            elif plat == "Linux":
                os.system("systemctl hibernate")
        elif ARGS.on_finish == "exit":
            return
    input('Press enter to close the program...')


def get_version():
    """Get version from version.json"""
    try:
        VERSION_PATH = Path(__file__).parent / 'version.json'
        with open(VERSION_PATH, 'r') as version_json:
            return json.load(version_json)['version']
    except Exception as exc:  # skipcq
        displayError(exc)
        return "Unknown"


if __name__ == '__main__':
    version = get_version()
    global ARGS  # pylint: disable=global-statement
    ARGS = argumentParser()

    def print(*args, **kwargs):
        if ARGS.print_to_webhook and (ARGS.telegram or ARGS.discord):
            sendReportToMessenger("```" + " ".join(args) + " ```")
        return builtins.print(*args, **kwargs)

    try:
        main()
    except Exception as e:
        displayError(e)
        input("press Enter to close...")
