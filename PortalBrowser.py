import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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

    def acceptAlert(self, timeout=10):
        WebDriverWait(self.browser, timeout).until(
            expected_conditions.alert_is_present()
            )
        self.browser.switch_to_alert().accept()
        self.browser.switch_to_default_content()

    def click(self, element):
        # Although elements have a click method, it seems to play up, possibly
        # when browser loses focus. Search for "selenium missing click" to get
        # an idea of the problem. Most complaints are on IE, but Chrome seems
        # susceptible as well. The incantation below, with the move operation
        # before the click, seems to work more reliably.
        action_chains = ActionChains(self.browser)
        action_chains.move_to_element(element).click().perform()

    def getRepoVersion(self):
        # Return the repo version id encoded in the portal version number
        footer = self.browser.find_element_by_id('ft')
        version = footer.find_element_by_xpath('./div/p').text
        repover = int(version.split('-')[1])
        return repover

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

    def watchRunStatus(self, func, timeout, *args, **kw):
        watchUntil = time.time() + timeout
        text = self.find_element_by_xpath("//div[@id='run-info']/div[1]/p[3]").text
        assert text.startswith('Status:'), repr(text)
        status = text.split(':')[1].strip()
        result = func(status)
        while result is None:
            timeout = watchUntil - time.time()
            self.wait(timeout, *args, **kw).until_not(
                expected_conditions.text_to_be_present_in_element(
                    (By.XPATH, "//div[@id='run-info']/div[1]/p[3]"), status
                    )
                )
            text = self.find_element_by_xpath("//div[@id='run-info']/div[1]/p[3]").text
            assert text.startswith('Status:'), repr(text)
            status = text.split(':', 1)[1].strip()
            result = func(status)
        return result

    def waitForInteraction(self, *args, **kw):
        class WithInteractionPage:

            def __init__(self, portal, args, kw):
                self.portal = portal
                self.args = args
                self.kw = kw

            def __enter__(self):
                modal_interaction_dialog = self.portal.wait(*self.args, **self.kw).until(
                    expected_conditions.presence_of_element_located(
                        (By.ID, 'modal-interaction-dialog')
                        )
                    )
                self.iframe = modal_interaction_dialog.find_element_by_tag_name('iframe')
                self.portal.switch_to_frame(self.iframe)
                return self

            def __exit__(self, type, value, tb):
                if type:
                    pass
                else:
                    self.portal.switch_to_default_content()
                    if self.portal.getRepoVersion() >= 10584:
                        # wait for interaction to be detached from DOM, to avoid
                        # subsequent waits for interaction pages from finding
                        # this interaction.
                        self.portal.wait(*args, **kw).until(
                            expected_conditions.staleness_of(self.iframe)
                            )
                    else:
                        # Older versions of the portal fail to detach the
                        # interaction page properly, leading to multiple
                        # interactions in the DOM (although they are hidden).
                        # These portals can be made to work by deleting the
                        # instances of id 'modal-interaction-dialog' that are
                        # children of the body.
                        self.portal.wait(60).until(
                            expected_conditions.presence_of_element_located(
                                (By.XPATH, '/html/body/div[@id="modal-interaction-dialog"]')
                                )
                            )
                        self.portal.execute_script('document.getElementById("body").removeChild(document.getElementById("modal-interaction-dialog"))')

            def switchBack(self):
                # After a context switch (e.g. an alert), return to the interaction page
                self.portal.switch_to_frame(self.iframe)

        return WithInteractionPage(self, args, kw)

    def workflowInputs(self):
        class WithWorkflowInputs:
            def __init__(self, portal):
                self.portal = portal

            def __enter__(self):
                self.workflow_input = self.portal.find_element_by_class_name('workflow_input')
                return self

            def __exit__(self, type, value, tb):
                pass

            def setInputText(self, name, value):
                textArea = self.workflow_input.find_element_by_xpath(
                    './*[@data-input-name="{0}"]//textarea'.format(name)
                    )
                action_chains = ActionChains(self.portal.browser)
                action_chains.move_to_element(textArea).click().send_keys(
                    Keys.BACK_SPACE*len(textArea.text)+str(value)
                    ).perform()

            def setInputFile(self, name, path):
                fileInput = self.workflow_input.find_element_by_xpath(
                    './*[@data-input-name="{0}"]//input[@type="file"]'.format(name)
                    )
                fileInput.send_keys(path)

        return WithWorkflowInputs(self)
