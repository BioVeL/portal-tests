from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
import time

import PortalBrowser

# To run workflows as registered user, add a username and password to config.py,
# Otherwise workflows are run as the guest user. config.py example:
# starturl = 'http://my.host/'
# username = 'myname'
# password = 'mysecret'
try:
    from config import starturl, username, password
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

    def cancelRunAtURL(self, runURL):
        # There may be an alert in the way, so acknowledge it.
        try:
            self.portal.acceptAlert(1)
        except TimeoutException:
            pass

        # Then load the run page
        self.portal.get(runURL)

        # Check if the run has been deleted already
        errorMessage = self.portal.getFlashError()
        if errorMessage and 'does not exist' in self.portal.getFlashError():
            return False

        # On a valid run page, there may be a modal interaction dialog in the 
        # way, so attempt to close it first.
        try:
            link = self.portal.find_element_by_class_name('ui-dialog-titlebar-close')
        except NoSuchElementException:
            pass
        else:
            link.click()

        # Click on the Cancel button
        try:
            link = self.portal.find_element_by_partial_link_text("Cancel")
        except NoSuchElementException:
            pass
        else:
            link.click()
            # Click OK on the "Are you sure?" alert
            self.portal.acceptAlert()
            # Workflow may finish just as workflow is cancelled, so check
            # that first, and if it is not the case, wait for Cancelled.
            try:
                self.portal.waitForRunStatusContains("Finished", 5)
            except TimeoutException:
                try:
                    self.portal.waitForRunStatusContains("Cancelled", 120)
                except TimeoutException:
                    pass
        return True

    def removeRunAtURL(self, runURL):
        if self.cancelRunAtURL(runURL):
            link = self.portal.find_element_by_partial_link_text("Delete")
            link.click()
            self.portal.acceptAlert()
            self.assertIn('Run was deleted', self.portal.getFlashNotice())
            self.portal.get(runURL)
        self.assertIn('does not exist', self.portal.getFlashError())

    def removeWorkflowAtURL(self, workflowURL):
        self.portal.get(workflowURL)

        link = self.portal.find_element_by_partial_link_text("Manage workflow")
        link.click()

        link = self.portal.find_element_by_partial_link_text("Delete workflow")
        link.click()

        self.portal.acceptAlert()

        self.portal.get(workflowURL)

        self.assertIn('does not exist', self.portal.getFlashError())
