from selenium import webdriver
from selenium.common.exceptions import WebDriverException
import time

import PortalBrowser

# To run workflows as registered user, add a username and password to config.py,
# Otherwise workflows are run as the guest user. config.py example:
# starturl = 'http://my.host/'
# username = 'myname'
# password = 'mysecret'
try:
    from config import *
except ImportError:
    starturl = 'http://beta.biovel.eu/'
    username = None
    password = None


class WithFirefox:

    def getBrowser(self):
        return webdriver.Firefox()


# Test if Chromium browser (Google Chrome) is available
print('Checking availability of Chromium...', end='')
try:
    chrome = webdriver.Chrome()
except WebDriverException as exc:
    print('no:', exc, sep='\n')
    WithChrome = None
else:
    print('yes')
    chrome.quit()
    class WithChrome:
        def getBrowser(self):
            return webdriver.Chrome()

def browserQuit(browser):
    # short sleep, so anyone viewing can see final state of browser
    time.sleep(2)
    browser.quit()


class BaseTest:

    def setUp(self):
        browser = self.getBrowser()
        # ensure browser quit is called, even if setUp fails
        self.addCleanup(browserQuit, browser)
        self.portal = PortalBrowser.PortalBrowser(browser, starturl)

    def tearDown(self):
        self.portal.signOut()

