import platform
import time
import unittest

from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions

from BaseTest import BaseTest, WithFirefox, WithChrome, username, password


class RunENMWorkflow(BaseTest):

    def setUp(self):
        BaseTest.setUp(self)
        if username:
            self.portal.signInWithPassword(username, password)
        else:
            self.portal.signInAsGuest()
        self.addCleanup(self.portal.signOut)


    def test_enm_workflow(self):
        link = self.portal.find_element_by_partial_link_text("Ecological Niche Modelling")
        link.click()

        # It is possible to run the workflow directly from the current page, but
        # here we click on the workflow-specific page

        link = self.portal.find_element_by_link_text("Ecological niche modelling workflow")
        link.click()

        link = self.portal.find_element_by_partial_link_text("Run workflow")
        link.click()
        # XXX Firefox 27.0.1 on Windows 7 hangs here

        # Use the default inputs

        start = self.portal.find_element_by_xpath("//input[@value='Start Run']")
        start.click()

        self.assertIn('Run was successfully created', self.portal.getFlashNotice())

        runURL = self.portal.current_url
        self.addCleanup(self.cancelRunAtURL, runURL)

        self.portal.waitForRunStatusContains("Running", 600, 1)

        startWorkflow = time.time()

        # Algorithm selection - use defaults
        with self.portal.waitForInteraction(300, 1):
            firstInteraction = time.time()
            print('Time to first interaction = {0:.1f}s'.format(firstInteraction - startWorkflow))
            continueButton = self.portal.wait(60).until(
                expected_conditions.element_to_be_clickable((By.XPATH, '//button/span[text()="Continue"]')))
            action_chains = ActionChains(self.portal.browser)
            action_chains.move_to_element(continueButton).click().perform()

        # Algorithm parameter values - use defaults
        with self.portal.waitForInteraction(300, 1):
            continueButton = self.portal.wait(60).until(
                expected_conditions.element_to_be_clickable((By.XPATH, '//button/span[text()="Continue"]')))
            action_chains = ActionChains(self.portal.browser)
            action_chains.move_to_element(continueButton).click().perform()

        # Select layers - use defaults
        with self.portal.waitForInteraction(300, 1):
            continueButton = self.portal.wait(60).until(
                expected_conditions.element_to_be_clickable((By.XPATH, '//button/span[text()="Submit selected layers"]')))
            action_chains = ActionChains(self.portal.browser)
            action_chains.move_to_element(continueButton).click().perform()

        # Select or create input mask - create mask
        with self.portal.waitForInteraction(300, 1):
            continueButton = self.portal.wait(60).until(
                expected_conditions.element_to_be_clickable((By.XPATH, '//button/span[text()="Create a new mask"]')))
            action_chains = ActionChains(self.portal.browser)
            action_chains.move_to_element(continueButton).click().perform()

        # Code for BioSTIF interaction does not work consistently.
        # Abandon run before we get there.

        self.removeRunAtURL(runURL)


        # BioSTIF - the remaining code cancels the BioSTIF interaction,
        # causing the workflow to finish. 
        # with self.portal.waitForInteraction(300, 1) as iframe:
        #     # a dialog pops up with [msg_error_application_start_failed] - if it
        #     # appears dismiss it else after 20 seconds, hit the abort button
        #     try:
        #         self.portal.acceptAlert(30)
        #     except TimeoutException:
        #         pass
        #     try:
        #         self.portal.acceptAlert(30)
        #     except TimeoutException:
        #         pass
        #     self.portal.switch_to_frame(iframe)
        #     continueButton = self.portal.wait(60).until(
        #         expected_conditions.element_to_be_clickable(
        #             (By.ID, 'user_cancel')
        #             )
        #         )
        #     action_chains = ActionChains(self.portal.browser)
        #     action_chains.move_to_element(continueButton).click(continueButton).perform()

        # self.portal.waitForRunStatusContains("Finished", 300, 1)

        # link = self.portal.find_element_by_partial_link_text("Delete")
        # link.click()
        # self.portal.acceptAlert()
        # self.assertIn('Run was deleted', self.portal.getFlashNotice())


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
