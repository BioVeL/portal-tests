import platform
import time
import unittest

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from BaseTest import BaseTest, WithFirefox, WithChrome, username, password


class RunENMWorkflow(BaseTest):

    def setUp(self):
        BaseTest.setUp(self)
        self.portal.goToStartPage()
        if username:
            self.portal.signInWithPassword(username, password)
        else:
            self.portal.signInAsGuest()

    def tearDown(self):
        # Cancel any active workflow run
        self.browser.switch_to_default_content()
        try:
            link = self.browser.find_element_by_partial_link_text("Cancel")
        except NoSuchElementException:
            pass
        else:
            link.click()
            time.sleep(2)
            self.browser.switch_to_alert().accept()
            self.browser.switch_to_default_content()
            try:
                self.portal.waitForRunStatusContains("Cancelled", 120)
            except TimeoutException:
                pass

        BaseTest.tearDown(self)

    def test_enm_workflow(self):
        link = self.browser.find_element_by_partial_link_text("Ecological Niche Modelling")
        link.click()

        # It is possible to run the workflow directly from the current page, but
        # here we click on the workflow-specific page

        link = self.browser.find_element_by_link_text("Ecological niche modelling workflow")
        link.click()

        link = self.browser.find_element_by_partial_link_text("Run workflow")
        link.click()
        # XXX Firefox 27.0.1 on Windows 7 hangs here

        # Use the default inputs

        start = self.browser.find_element_by_xpath("//input[@value='Start Run']")
        start.click()

        self.portal.waitForRunFlashContains("Run was successfully created.", 60)

        self.portal.waitForRunStatusContains("Running", 600, 1)

        startWorkflow = time.time()

        # Algorithm selection - use defaults
        with self.portal.waitForInteraction(300, 1):
            firstInteraction = time.time()
            print('Time to first interaction = {0:.1f}s'.format(firstInteraction - startWorkflow))
            continueButton = WebDriverWait(self.browser, 60).until(
                expected_conditions.presence_of_element_located((By.XPATH, '//button/span[text()="Continue"]')))
            continueButton.click()

        # Algorithm parameter values - use defaults
        with self.portal.waitForInteraction(300, 1):
            continueButton = WebDriverWait(self.browser, 60).until(
                expected_conditions.presence_of_element_located((By.XPATH, '//button/span[text()="Continue"]')))
            continueButton.click()


        # The third interaction is more complex, selecting checkboxes for layers.
        # So, we let the test fall through to tearDown, where it will cancel the
        # workflow run.
        # with self.portal.waitForInteraction(300, 1):
        #     with open('file.html', 'w') as f:
        #         f.write(self.browser.page_source)



# Firefox on Windows hangs on click of Run Workflow button using Selenium, but
# not when running workflow manually
# confirmed on (FF27.0.1, Win7)
@unittest.skipIf(platform.system() == 'Windows', 'Selenium hangs with Firefox on Windows')
class RunENMWorkflowFirefox(RunENMWorkflow, unittest.TestCase, WithFirefox):
    pass

if WithChrome:
    class RunENMWorkflowChrome(RunENMWorkflow, unittest.TestCase, WithChrome):
        pass


if __name__ == '__main__':
    unittest.main()
