import os, platform, time, unittest

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions

from selenium.webdriver.support.select import Select

from BaseTest import BaseTest, WithFirefox, WithChrome, username, password


class RunMPMWorkflow(BaseTest):

    def setUp(self):
        BaseTest.setUp(self)
        self.portal.signInWithPassword(username, password)
        self.addCleanup(self.portal.signOut)

    def waitForStatusRunning(self, status):
        self.assertIn(status, ('Connecting to Taverna Server', 'Queued',
            'Running', 'Waiting for user input', 'Failed'))
        if status == 'Failed':
            self.fail('Workflow run failed')
        elif status in ('Running', 'Waiting for user input'):
            return True

    def waitForStatusFinished(self, status):
        self.assertIn(status, ('Running', 'Waiting for user input',
            'Gathering run outputs and log', 'Finished', 'Failed'))
        if status == 'Failed':
            self.fail('Workflow run failed')
        elif status == 'Finished':
            return True

    def test_workflow(self):
        self.portal.selectWorkflowsTab()

        link = self.portal.find_element_by_partial_link_text('Upload a workflow')
        link.click()

        time0 = time.time()
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
        time1 = time.time()
        print('Upload time: {0:.4}'.format(time1 - time0))

        saveButton = self.portal.find_element_by_name('commit')
        saveButton.click()

        self.assertIn('Workflow was successfully updated', self.portal.getFlashNotice())

        workflowURL = self.portal.current_url

        link = self.portal.find_element_by_partial_link_text("Run workflow")
        link.click()

        with self.portal.workflowInputs() as inputs:
            inputs.setInputText('iterations', 1000)
            inputs.setInputFile('stageMatrixFile', os.path.join(os.getcwd(), 'BioVeL_POP_MPM/MTers87_88.txt'))
            self.pause(1)

        startRun = self.portal.find_element_by_name('commit')
        startRun.click()

        self.assertIn('Run was successfully created', self.portal.getFlashNotice())

        self.addCleanup(self.cancelRunAtURL, self.portal.current_url)

        self.portal.watchRunStatus(self.waitForStatusRunning, 600)

        time0 = time.time()

        abundances = {
        'S': 69,
        'J': 111,
        'V': 100,
        'G': 21,
        'D': 43
        }

        with self.portal.waitForInteraction(300, 1):
            time1 = time.time()
            print('Time to first interaction: {0:.4}'.format(time1 - time0))
            content = self.portal.wait(30).until(
                expected_conditions.presence_of_element_located(
                    (By.ID, 'content')
                    )
                )
            time2 = time.time()
            print('Load interaction content: {0:.4}'.format(time2 - time1))
            for tr in content.find_elements_by_xpath('./tr'):
                stage = tr.find_element_by_xpath('./td[1]').text
                self.assertIn(stage, abundances)
                if stage in ('S', 'J'):
                    recruited = tr.find_element_by_xpath('./td[2]/input[@type="checkbox"]')
                    recruited.click()
                    self.pause(0.5)
                elif stage == 'G':
                    reproductive = tr.find_element_by_xpath('./td[3]/input[@type="checkbox"]')
                    reproductive.click()
                    self.pause(0.5)
            self.pause(1)
            submit = self.portal.find_element_by_id('submit')
            submit.find_element_by_xpath('./input[@type="button"]').click()
            time0 = time.time()

        with self.portal.waitForInteraction(300, 1):
            content = self.portal.wait(30).until(
                expected_conditions.presence_of_element_located(
                    (By.ID, 'content')
                    )
                )
            time1 = time.time()
            print('Time between interactions: {0:.4}'.format(time1 - time0))
            for div in content.find_elements_by_xpath('./div'):
                stage = div.find_element_by_tag_name('label').text
                self.assertIn(stage, abundances)
                textbox = div.find_element_by_tag_name('input')
                textbox.send_keys(Keys.BACK_SPACE + str(abundances[stage]))
                self.pause(0.5)
            self.pause(0.5)
            content.find_element_by_xpath('./input[@type="button"]').click()
            time0 = time.time()

        self.portal.watchRunStatus(self.waitForStatusFinished, 300)
        time1 = time.time()
        print('Analysis time: {0:.4}'.format(time1 - time0))
        self.pause(10)

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
    import sys
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--pause':
            pause = True
            del sys.argv[i]
        else:
            i += 1
    unittest.main()
