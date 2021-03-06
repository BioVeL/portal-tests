import re, time, urllib.parse, urllib.request

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait


class UnexpectedRunStatusException(Exception):
    pass


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

    def selectFile(self, fileInputElement, filename):
        fileInputElement.send_keys(
            urllib.request.url2pathname(
                urllib.parse.urlparse('file:///' + filename).path
                )
            )

    def getRepoVersion(self):
        # Return the repo version id encoded in the portal version number
        footer = self.browser.find_element_by_id('ft')
        version = footer.find_element_by_xpath('./div/p').text
        match = re.search(r'Portal version: Alpha ([\d]+) -', version)
        if match:
            repover = int(match.group(1))
        else:
            assert re.search(r'Portal version: \d\.\d\.\d-([\d]+)', version), version
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

    def getRunStatus(self):
        text = self.find_element_by_xpath("//div[@id='run-info']/div[1]/p[3]").text
        assert text.startswith('Status:'), repr(text)
        return text.split(':', 1)[1].strip()

    def watchRunStatus(self, func, timeout, *args, **kw):
        watchUntil = time.time() + timeout
        while True:
            status = self.getRunStatus()
            result = func(status)
            if result is not None:
                return result
            timeout = watchUntil - time.time()
            self.wait(timeout, *args, **kw).until_not(
                expected_conditions.text_to_be_present_in_element(
                    (By.XPATH, "//div[@id='run-info']/div[1]/p[3]"), status
                    )
                )

    def waitForInteraction(self, timeout, *args, **kw):
        class WithInteractionPage:

            def __init__(self, portal, timeout, args, kw):
                self.portal = portal
                self.timeout = timeout
                self.args = args
                self.kw = kw

            def waitForUserInputStatus(self, status):
                if status == 'Waiting for user input':
                    return True
                elif status in ('Failed', 'Finished'):
                    raise UnexpectedRunStatusException(status)

            def __enter__(self):
                # Rather than initially waiting for the appearance of the modal
                # dialog, wait for run status to indicate that the portal is
                # waiting for user input. This allows us to detect alternative
                # paths, such as failure or unexpected finish.  Note, this first
                # test can sometimes get triggered by the lingering status of a
                # previous interaction, so sometimes this first test will return
                # immediately and fallback on the wait for the modal dialog.
                # This is why we add the remainder of the timeout to the second
                # wait.
                waitUntil = time.time() + self.timeout
                self.portal.watchRunStatus(self.waitForUserInputStatus, self.timeout, *self.args, **self.kw)
                timeout = waitUntil - time.time()
                modal_interaction_dialog = self.portal.wait(timeout, *self.args, **self.kw).until(
                    expected_conditions.presence_of_element_located(
                        (By.ID, 'modal-interaction-dialog')
                        )
                    )
                self.iframe = modal_interaction_dialog.find_element_by_tag_name('iframe')
                # The parent dialog has a specified size, so should not return 0
                self.dialog = modal_interaction_dialog.find_element_by_xpath('..')
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
                        self.portal.wait(self.timeout, *self.args, **self.kw).until(
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

            @property
            def location(self):
                self.portal.switch_to_default_content()
                location = self.dialog.location
                self.switchBack()
                return location

            @property
            def size(self):
                self.portal.switch_to_default_content()
                size = self.dialog.size
                self.switchBack()
                return size

            def switchBack(self):
                # After a context switch (e.g. an alert), return to the interaction page
                self.portal.switch_to_frame(self.iframe)

        return WithInteractionPage(self, timeout, args, kw)

    def workflowInputs(self):
        try:
            workflow_input = self.browser.find_element_by_class_name('workflow_input')
        except NoSuchElementException:
            return None
        return RunInputs(self, workflow_input)


class RunInputs:

    def __init__(self, portal, workflow_input):
        self.portal = portal
        self.workflow_input = workflow_input

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
        self.portal.selectFile(fileInput, path)
