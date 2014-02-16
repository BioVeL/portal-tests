from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

class PortalBrowser:

    def __init__(self, browser, url):
        self.browser = browser
        browser.get(url)

    def __getattr__(self, name):
        # If method does not exist, pass it on to the browser
        return getattr(self.browser, name)

    # Always present portal components

    def getPageHeader(self):
        return self.browser.find_element_by_id('header')

    def selectHomeTab(self):
        link = self.getPageHeader().find_element_by_partial_link_text("Home")
        link.click()

    def selectWorkflowsTab(self):
        link = self.getPageHeader().find_element_by_partial_link_text("Workflows")
        link.click()

    def selectRunsTab(self):
        link = self.getPageHeader().find_element_by_partial_link_text("Runs")
        link.click()

    def getFlashResult(self):
        try:
            return (False, self.browser.find_element_by_id('error_flash').text)
        except NoSuchElementException:
            return (True, self.browser.find_element_by_id('notice_flash').text)

    def getFlashNotice(self):
        try:
            return self.browser.find_element_by_id('notice_flash').text
        except NoSuchElementException:
            return None

    def getFlashError(self):
        try:
            return self.browser.find_element_by_id('error_flash').text
        except NoSuchElementException:
            return None

    def acceptAlert(self):
        WebDriverWait(self.browser, 10).until(
            expected_conditions.alert_is_present()
            )
        self.browser.switch_to_alert().accept()
        self.browser.switch_to_default_content()

    # Sign In

    def getSignOutLink(self):
        return self.getPageHeader().find_element_by_partial_link_text("Log out")

    def signOut(self):
        try:
            link = self.getSignOutLink()
        except NoSuchElementException:
            changed = False
        else:
            link.click()
            changed = True
        return changed

    def isSignedIn(self):
        try:
            self.getSignOutLink()
        except NoSuchElementException:
            return False
        return True

    def signInAsGuest(self):
        link = self.browser.find_element_by_link_text("Click here to log into the guest account")
        link.click()

    def signInWithPassword(self, username, password):
        header = self.getPageHeader()
        link = header.find_element_by_partial_link_text("Log in")
        link.click()
        confirm = WebDriverWait(header, 5).until(
            expected_conditions.element_to_be_clickable(
                (By.ID, 'login_button')
                )
            )
        userInput = header.find_element_by_id('login')
        userInput.send_keys(username)
        passInput = header.find_element_by_id('password')
        passInput.send_keys(password)
        confirm.click()
        
    # Workflow Runs

    # All the wait... methods take the timeout and other parameters used in
    # WebDriverWait, but excluding the initial browser driver parameter

    def wait(self, *args, **kw):
        return WebDriverWait(self.browser, *args, **kw)

    def waitForRunStatusContains(self, status, *args, **kw):
        WebDriverWait(self.browser, *args, **kw).until(
            expected_conditions.text_to_be_present_in_element(
                (By.XPATH, "//div[@id='run-info']/div[1]/p[3]"), status
                )
            )

    find_modal = (By.ID, 'modal-interaction-dialog')

    def waitForInteractionPageOpen(self, *args, **kw):
        modal_interaction_dialog = WebDriverWait(self.browser, *args, **kw).until(
            expected_conditions.presence_of_element_located(self.find_modal)
            )
        iframe = modal_interaction_dialog.find_element_by_tag_name('iframe')
        self.browser.switch_to_frame(iframe)

    def waitForInteractionPageClose(self, *args, **kw):
        self.browser.switch_to_default_content()
        WebDriverWait(self.browser, *args, **kw).until(
            expected_conditions.invisibility_of_element_located(self.find_modal)
            )
        # Due to bug http://jira.biovel.eu/browse/SERVINF-380 the old modal is
        # kept around. Here we delete it to ensure only one element has the id.
        try:
            self.browser.execute_script('document.getElementById("body").removeChild(document.getElementById("modal-interaction-dialog"))')
        except WebDriverException:
            # Hopefully, this indicates that SERVINF-380 has been fixed
            pass

    def waitForInteraction(self, *args, **kw):
        class WithInteractionPage:

            def __init__(self, portal, args, kw):
                self.portal = portal
                self.args = args
                self.kw = kw

            def __enter__(self):
                self.portal.waitForInteractionPageOpen(*self.args, **self.kw)

            def __exit__(self, type, value, tb):
                self.portal.waitForInteractionPageClose(*self.args, **self.kw)

        return WithInteractionPage(self, args, kw)
