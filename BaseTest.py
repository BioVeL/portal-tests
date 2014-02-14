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
    print('no:')
    print(exc)
    WithChrome = None
else:
    print('yes')
    chrome.quit()
    class WithChrome:
        def getBrowser(self):
            return webdriver.Chrome()


class BaseTest:

    def browserQuit(self):
        # short sleep, so anyone viewing can see final state of browser
        time.sleep(2)
        self.browser.quit()

    def setUp(self):
        self.browser = self.getBrowser()
        # ensure browser quit is called, even if setUp fails
        self.addCleanup(self.browserQuit)
        self.portal = PortalBrowser.PortalBrowser(self.browser, starturl)

    def tearDown(self):
        self.portal.signOut()

