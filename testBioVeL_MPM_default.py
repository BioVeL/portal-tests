import os, platform, unittest

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions

from selenium.webdriver.support.select import Select

from BaseTest import BaseTest, WithFirefox, WithChrome, username, password


class RunMPMWorkflow(BaseTest):

    def setUp(self):
        BaseTest.setUp(self)
        self.portal.signInWithPassword(username, password)
        self.addCleanup(self.portal.signOut)

    def waitForStatusRunning(self, status):
        if self.portal.getRepoVersion() <= 10513:
            self.assertIn(status, ('Connecting to Taverna Server',
                'Initializing new workflow run', 'Uploading run inputs',
                'Queued', 'Starting run', 'Running', 'Failed'))
        else:
            self.assertIn(status, ('Connecting to Taverna Server', 'Queued',
                'Starting run', 'Running', 'Waiting for user input', 'Failed'))
        if status == 'Failed':
            self.fail('Workflow run failed')
        elif status in ('Running', 'Waiting for user input'):
            return True

    def waitForStatusFinished(self, status):
        self.assertIn(status, ('Running', 'Waiting for user input',
            'Gathering run outputs and log', 'Running post-run tasks', 'Finished', 'Failed'))
        if status == 'Failed':
            self.fail('Workflow run failed')
        elif status == 'Finished':
            return True

    def test_workflow(self):
        self.portal.selectWorkflowsTab()

        link = self.portal.find_element_by_partial_link_text('Upload a workflow')
        link.click()

        filename = self.portal.find_element_by_id('workflow_data')
        filename.send_keys(os.path.join(os.getcwd(), 'BioVeL_POP_MPM/matrix_population_model_analysis_v10.t2flow'))

        category = self.portal.find_element_by_id('workflow_category_id')
        select = Select(category)
        select.select_by_visible_text('Population Modelling')

        keepPrivate = self.portal.find_element_by_id('sharing_scope_0')
        keepPrivate.click()

        nextButton = self.portal.find_element_by_id('workflow_submit_btn')
        nextButton.click()
        # XXX Firefox 27.0.1 on Windows 7 hangs here

        self.assertIn('Workflow was successfully uploaded and saved', self.portal.getFlashNotice())

        saveButton = self.portal.find_element_by_name('commit')
        saveButton.click()

        self.assertIn('Workflow was successfully updated', self.portal.getFlashNotice())

        workflowURL = self.portal.current_url

        link = self.portal.find_element_by_partial_link_text("Run workflow")
        link.click()

        startRun = self.portal.find_element_by_name('commit')
        startRun.click()

        self.assertIn('Run was successfully created', self.portal.getFlashNotice())

        self.addCleanup(self.cancelRunAtURL, self.portal.current_url)

        self.portal.watchRunStatus(self.waitForStatusRunning, 600)

        with self.portal.waitForInteraction(300, 1):
            confirm = self.portal.wait(60).until(
                expected_conditions.presence_of_element_located(
                    (By.XPATH, '//*[@id="submit"]/input[@value="Confirm"]')
                    )
                )
            confirm.click()

        with self.portal.waitForInteraction(300, 1):
            confirm = self.portal.wait(60).until(
                expected_conditions.presence_of_element_located(
                    (By.XPATH, '//*[@id="content"]/input[@value="Confirm"]')
                    )
                )
            confirm.click()

        self.portal.watchRunStatus(self.waitForStatusFinished, 300)

        link = self.portal.find_element_by_partial_link_text("Delete")
        link.click()
        self.portal.acceptAlert()
        self.assertIn('Run was deleted', self.portal.getFlashNotice())

        self.removeWorkflowAtURL(workflowURL)

# Firefox on Windows hangs on click of Workflow Submit button using Selenium, but
# not when running workflow manually
# confirmed on (FF27.0.1, Win7)
@unittest.skipIf(platform.system() == 'Windows', 'Selenium hangs with Firefox on Windows')
@unittest.skipUnless(username, 'No username login provided')
class RunMPMWorkflowFirefox(RunMPMWorkflow, unittest.TestCase, WithFirefox):
    pass

if WithChrome:
    @unittest.skipUnless(username, 'No username login provided')
    class RunMPMWorkflowChrome(RunMPMWorkflow, unittest.TestCase, WithChrome):
        pass


if __name__ == '__main__':
    unittest.main()
