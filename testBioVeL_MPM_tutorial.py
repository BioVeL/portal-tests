import os, time, unittest

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions

from selenium.webdriver.support.select import Select

from BaseTest import BaseTest, WithFirefox, WithChrome, username, password


class RunRConnectionTest(BaseTest):

    def setUp(self):
        BaseTest.setUp(self)
        self.portal.signInWithPassword(username, password)
        self.addCleanup(self.portal.signOut)

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

        self.assertIn('Workflow was successfully uploaded and saved', self.portal.getFlashNotice())

        saveButton = self.portal.find_element_by_name('commit')
        saveButton.click()

        self.assertIn('Workflow was successfully updated', self.portal.getFlashNotice())

        workflowURL = self.portal.current_url

        link = self.portal.find_element_by_partial_link_text("Run workflow")
        link.click()

        with self.portal.workflowInputs() as inputs:
            inputs.setInputText('iterations', 1000)
            inputs.setInputFile('stageMatrixFile', os.path.join(os.getcwd(), 'BioVeL_POP_MPM/MTers87_88.txt'))

        startRun = self.portal.find_element_by_name('commit')
        startRun.click()

        self.assertIn('Run was successfully created', self.portal.getFlashNotice())

        self.addCleanup(self.cancelRunAtURL, self.portal.current_url)

        self.portal.waitForRunStatusContains("Running", 600, 1)

        abundances = {
        'S': 69,
        'J': 111,
        'V': 100, 
        'G': 21,
        'D': 43
        }

        with self.portal.waitForInteraction(300, 1):
            content = self.portal.wait(30).until(
                expected_conditions.presence_of_element_located(
                    (By.ID, 'content')
                    )
                )
            for tr in content.find_elements_by_xpath('./tr'):
                stage = tr.find_element_by_xpath('./td[1]').text
                self.assertIn(stage, abundances)
                if stage in ('S', 'J'):
                    recruited = tr.find_element_by_xpath('./td[2]/input[@type="checkbox"]')
                    recruited.click()
                elif stage == 'G':
                    reproductive = tr.find_element_by_xpath('./td[3]/input[@type="checkbox"]')
                    reproductive.click()
            submit = self.portal.find_element_by_id('submit')
            submit.find_element_by_xpath('./input[@type="button"]').click()

        with self.portal.waitForInteraction(300, 1):
            content = self.portal.wait(30).until(
                expected_conditions.presence_of_element_located(
                    (By.ID, 'content')
                    )
                )
            for div in content.find_elements_by_xpath('./div'):
                stage = div.find_element_by_tag_name('label').text
                self.assertIn(stage, abundances)
                textbox = div.find_element_by_tag_name('input')
                textbox.send_keys(Keys.BACK_SPACE + str(abundances[stage]))
            time.sleep(5)
            content.find_element_by_xpath('./input[@type="button"]').click()

        self.portal.waitForRunStatusContains("Finished", 300, 1)
        time.sleep(5)

        link = self.portal.find_element_by_partial_link_text("Delete")
        link.click()
        self.portal.acceptAlert()
        self.assertIn('Run was deleted', self.portal.getFlashNotice())

        self.removeWorkflowAtURL(workflowURL)

@unittest.skipUnless(username, 'No username login provided')
class RunRConnectionTestFirefox(RunRConnectionTest, unittest.TestCase, WithFirefox):
    pass

if WithChrome:
    @unittest.skipUnless(username, 'No username login provided')
    class RunRConnectionTestChrome(RunRConnectionTest, unittest.TestCase, WithChrome):
        pass


if __name__ == '__main__':
    unittest.main()
