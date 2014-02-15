import os, time, unittest

from selenium.common.exceptions import NoSuchElementException, TimeoutException
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.select import Select
# from selenium.webdriver.support.ui import WebDriverWait

from BaseTest import BaseTest, WithFirefox, WithChrome, username, password


class RunRConnectionTest(BaseTest):

    def setUp(self):
        BaseTest.setUp(self)
        if username:
            self.portal.signInWithPassword(username, password)
        else:
            self.portal.signInAsGuest()

    def tearDown(self):
        # Cancel any active workflow run
        self.portal.switch_to_default_content()
        try:
            link = self.portal.find_element_by_partial_link_text("Cancel")
        except NoSuchElementException:
            pass
        else:
            link.click()
            self.portal.acceptAlert()
            try:
                self.portal.waitForRunStatusContains("Cancelled", 120)
            except TimeoutException:
                pass

        BaseTest.tearDown(self)

    def test_workflow(self):
        self.portal.selectWorkflowsTab()

        link = self.portal.find_element_by_partial_link_text('Upload a workflow')
        link.click()

        filename = self.portal.find_element_by_id('workflow_data')
        filename.send_keys(os.path.join(os.getcwd(), 't2flow/Rconnect.t2flow'))

        category = self.portal.find_element_by_id('workflow_category_id')
        select = Select(category)
        select.select_by_visible_text('Other')

        keepPrivate = self.portal.find_element_by_id('sharing_scope_0')
        keepPrivate.click()

        nextButton = self.portal.find_element_by_id('workflow_submit_btn')
        nextButton.click()

        self.assertIn('Workflow was successfully uploaded and saved', self.portal.getFlashMessage())

        saveButton = self.portal.find_element_by_name('commit')
        saveButton.click()

        self.assertIn('Workflow was successfully updated', self.portal.getFlashMessage())

        workflowURL = self.portal.current_url

        link = self.portal.find_element_by_partial_link_text("Run workflow")
        link.click()

        startRun = self.portal.find_element_by_name('commit')
        startRun.click()

        self.assertIn('Run was successfully created', self.portal.getFlashMessage())

        self.portal.waitForRunStatusContains("Running", 600, 1)

        self.portal.waitForRunStatusContains("Finished", 600, 1)

        link = self.portal.find_element_by_partial_link_text("Delete")
        link.click()

        self.portal.acceptAlert()

        self.assertIn('Run was deleted', self.portal.getFlashMessage())

        self.portal.get(workflowURL)

        link = self.portal.find_element_by_partial_link_text("Manage workflow")
        link.click()

        link = self.portal.find_element_by_partial_link_text("Delete workflow")
        link.click()

        self.portal.acceptAlert()

class RunRConnectionTestFirefox(RunRConnectionTest, unittest.TestCase, WithFirefox):
    pass

if WithChrome:
    class RunRConnectionTestChrome(RunRConnectionTest, unittest.TestCase, WithChrome):
        pass


if __name__ == '__main__':
    unittest.main()
