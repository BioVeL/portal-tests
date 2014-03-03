import platform
import time
import unittest

# from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions

from BaseTest import ExistingWorkflowTest, WithFirefox, WithChrome


class RunENMWorkflow(ExistingWorkflowTest):

    def test_enm_workflow(self):
        link = self.portal.find_element_by_partial_link_text("Ecological Niche Modelling")
        self.portal.click(link)

        with self.runWorkflow('Ecological niche modelling workflow'):
            # Algorithm selection - use defaults
            with self.portal.waitForInteraction(300, 1):
                firstInteraction = time.time()
                continueButton = self.portal.wait(60).until(
                    expected_conditions.element_to_be_clickable((By.XPATH, '//button/span[text()="Continue"]')))
                self.portal.click(continueButton)

            # Algorithm parameter values - use defaults
            with self.portal.waitForInteraction(300, 1):
                continueButton = self.portal.wait(60).until(
                    expected_conditions.element_to_be_clickable((By.XPATH, '//button/span[text()="Continue"]')))
                self.portal.click(continueButton)

            # Select layers - use defaults
            with self.portal.waitForInteraction(300, 1):
                continueButton = self.portal.wait(60).until(
                    expected_conditions.element_to_be_clickable((By.XPATH, '//button/span[text()="Submit selected layers"]')))
                self.portal.click(continueButton)

            # Select or create input mask - create mask
            with self.portal.waitForInteraction(300, 1):
                continueButton = self.portal.wait(60).until(
                    expected_conditions.element_to_be_clickable((By.XPATH, '//button/span[text()="Create a new mask"]')))
                self.portal.click(continueButton)

            # Code for BioSTIF interaction does not work consistently.
            # Abandon run before we get there.

            self.fail('BioSTIF not working')

            # BioSTIF - the remaining code cancels the BioSTIF interaction,
            # causing the workflow to finish.
            # with self.portal.waitForInteraction(300, 1) as interaction:
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
            #     interaction.switchBack()
            #     continueButton = self.portal.wait(60).until(
            #         expected_conditions.element_to_be_clickable(
            #             (By.ID, 'user_cancel')
            #             )
            #         )
            #     self.portal.click(continueButton)

            # self.portal.watchRunStatus(self.waitForStatusFinished, 300)

            # link = self.portal.find_element_by_partial_link_text("Delete")
            # self.portal.click(link)
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
