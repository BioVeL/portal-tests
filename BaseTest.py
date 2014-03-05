import os, sys, time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.support.select import Select

import PortalBrowser

# To run workflows as registered user, add a username and password to config.py,
# Otherwise workflows are run as the guest user. config.py example:
# starturl = 'http://my.host/'
# username = 'myname'
# password = 'mysecret'
starturl = 'http://beta.biovel.eu/'
username = None
password = None
try:
    from config import *
except ImportError:
    pass

class WithFirefox:

    def getBrowser(self):
        driver = webdriver.Firefox()
        driver.set_window_size(1024,640)
        return driver


# Test if Chromium browser (Google Chrome) is available
print('Checking availability of Chromium...', end='')
try:
    chrome = webdriver.Chrome()
except WebDriverException as exc:
    print('no:', exc, sep='\n')
    WithChrome = None
else:
    print('yes')
    chrome.quit()
    class WithChrome:
        def getBrowser(self):
            return webdriver.Chrome()

def browserQuit(browser):
    # short sleep, so anyone viewing can see final state of browser
    time.sleep(2)
    browser.quit()


class BaseTest:

    def setUp(self):
        module = sys.modules[self.__class__.__module__]
        if 'pause' in dir(module) and module.pause:
            self.addPause = True
        browser = self.getBrowser()
        # ensure browser quit is called, even if setUp fails
        self.addCleanup(browserQuit, browser)
        self.portal = PortalBrowser.PortalBrowser(browser, starturl)


    addPause = False

    def pause(self, t):
        if self.addPause:
            time.sleep(t)

def wraplist(value):
    if isinstance(value, str):
        pass
    else:
        try:
            # list, tuple
            value = '[' + ','.join([wraplist(v) for v in value]) + ']'
        except TypeError:
            # int, float
            value = str(value)
    return value

class Interactions:

    def __init__(self, test, portal):
        self.test = test
        self.portal = portal
        self.results = None

    def __enter__(self):
        self.portal.watchRunStatus(self.test.waitForStatusRunning, 600)

        return self

    def __exit__(self, type, value, tb):
        if type is None:
            self.portal.watchRunStatus(self.test.waitForStatusFinished, 600)

            runOutputs = self.portal.find_element_by_id('run-outputs')
            for output in runOutputs.find_elements_by_xpath('.//div[@class="output"]'):
                mimeType = output.find_element_by_xpath('.//span[@class="mime_type"]')
                if mimeType.text == '(application/x-error)':
                    self.test.fail(output.find_element_by_xpath('.//pre').text)

            self.results = {}

class WorkflowTest(BaseTest):
    '''WorkflowTest: class to run a specific workflow'''

    def setUp(self):
        BaseTest.setUp(self)
        if username:
            self.portal.signInWithPassword(username, password)
        else:
            self.portal.signInAsGuest()
        self.addCleanup(self.portal.signOut)

    def reportFailedRun(self):
        advanced = self.portal.find_element_by_id('advanced')
        # Click on title to make Advanced section visible. This is required
        # in order to read the text attributes
        advanced.find_element_by_xpath('.//*[@class="foldTitle"]').click()
        outputs = advanced.find_elements_by_xpath('.//div[@class="foldContent"]/*')
        messages = [(element.text.strip() or 'None') for element in outputs]
        messages.insert(0, 'Workflow run failed:')
        self.fail('\n---\n'.join(messages))

    def waitForStatusRunning(self, status):
        self.assertIn(status, (
            'Connecting to Taverna Server', 'Initializing new workflow run',
            'Uploading run inputs', 'Queued', 'Starting run', 'Running',
            'Waiting for user input', 'Failed'
            )
        )
        if status == 'Failed':
            self.reportFailedRun()
        elif status in ('Running', 'Waiting for user input'):
            return True

    def waitForStatusFinished(self, status):
        self.assertIn(status, (
            'Running', 'Waiting for user input', 'Gathering run outputs and log',
            'Running post-run tasks', 'Finished', 'Failed'
            )
        )
        if status == 'Failed':
            self.reportFailedRun()
        elif status == 'Finished':
            return True

    def cancelRunAtURL(self, runURL):
        # There may be an alert in the way, so acknowledge it.
        try:
            self.portal.acceptAlert(1)
        except TimeoutException:
            pass

        # Then load the run page
        self.portal.get(runURL)

        # Check if the run has been deleted already
        errorMessage = self.portal.getFlashError()
        if errorMessage and 'does not exist' in self.portal.getFlashError():
            return False

        # On a valid run page, there may be a modal interaction dialog in the
        # way, so attempt to close it first.
        try:
            link = self.portal.find_element_by_class_name('ui-dialog-titlebar-close')
        except NoSuchElementException:
            pass
        else:
            link.click()

        # Click on the Cancel button
        try:
            link = self.portal.find_element_by_partial_link_text("Cancel")
        except NoSuchElementException:
            pass
        else:
            link.click()
            # Click OK on the "Are you sure?" alert
            self.portal.acceptAlert()
            # Workflow may finish just as workflow is cancelled, so check
            # that first, and if it is not the case, wait for Cancelled.
            try:
                self.portal.waitForRunStatusContains("Finished", 5)
            except TimeoutException:
                try:
                    self.portal.waitForRunStatusContains("Cancelled", 120)
                except TimeoutException:
                    pass
        return True

    def removeRunAtURL(self, runURL):
        if self.cancelRunAtURL(runURL):
            link = self.portal.find_element_by_partial_link_text("Delete")
            link.click()
            self.portal.acceptAlert()
            self.assertIn('Run was deleted', self.portal.getFlashNotice())
            self.portal.get(runURL)
        message = self.portal.getFlashError()
        if message:
            self.assertIn('does not exist', self.portal.getFlashError())
        elif self.portal.getRepoVersion() == 10550 and isinstance(self, WithFirefox):
            # portal 10550 does not display the flash message here
            # Since it'll be history soon, don't bother notifying the error
            pass
        else:
            filename = str(time.time()) + '.png'
            self.portal.save_screenshot(filename)
            raise RuntimeError('"does not exist" not in flash error - see {0}'.format(filename))


    def runExistingWorkflow(self, name, textInputs=None, fileInputs=None):
        link = self.portal.find_element_by_link_text(name)
        self.portal.click(link)

        link = self.portal.find_element_by_partial_link_text("Run workflow")
        self.portal.click(link)

        if textInputs:
            for name, value in textInputs.items():
                value = wraplist(value)
                inputs.setInputText(name, value)
                self.pause(1)
        if fileInputs:
            for name, value in fileInputs.items():
                inputs.setInputFile(name, os.path.join(os.getcwd(), value))
                self.pause(1)
        self.pause(1)

        start = self.portal.find_element_by_xpath("//input[@value='Start Run']")
        start.click()

        self.assertIn('Run was successfully created', self.portal.getFlashNotice())

        runURL = self.portal.current_url
        self.addCleanup(self.cancelRunAtURL, runURL)

        return Interactions(self, self.portal)

    def runUploadedWorkflow(self, filename, topic, textInputs=None, fileInputs=None):
        self.portal.selectWorkflowsTab()

        link = self.portal.find_element_by_partial_link_text('Upload a workflow')
        self.pause(1)
        link.click()

        filename = self.portal.find_element_by_id('workflow_data')
        self.pause(1)
        filename.send_keys(os.path.join(os.getcwd(), 'BioVeL_POP_MPM/matrix_population_model_analysis_v10.t2flow'))

        category = self.portal.find_element_by_id('workflow_category_id')
        self.pause(1)
        select = Select(category)
        select.select_by_visible_text('Population Modelling')

        keepPrivate = self.portal.find_element_by_id('sharing_scope_0')
        self.pause(1)
        keepPrivate.click()

        nextButton = self.portal.find_element_by_id('workflow_submit_btn')
        self.pause(1)
        nextButton.click()

        self.assertIn('Workflow was successfully uploaded and saved', self.portal.getFlashNotice())

        saveButton = self.portal.find_element_by_name('commit')
        self.pause(1)
        saveButton.click()

        self.assertIn('Workflow was successfully updated', self.portal.getFlashNotice())

        workflowURL = self.portal.current_url
        self.addCleanup(self.removeWorkflowAtURL, workflowURL)

        link = self.portal.find_element_by_partial_link_text("Run workflow")
        self.pause(1)
        self.portal.click(link)

        with self.portal.workflowInputs() as inputs:
            if textInputs:
                for name, value in textInputs.items():
                    value = wraplist(value)
                    inputs.setInputText(name, value)
                    self.pause(1)
            if fileInputs:
                for name, value in fileInputs.items():
                    inputs.setInputFile(name, os.path.join(os.getcwd(), value))
                    self.pause(1)
        self.pause(1)

        start = self.portal.find_element_by_xpath("//input[@value='Start Run']")
        start.click()

        self.assertIn('Run was successfully created', self.portal.getFlashNotice())

        runURL = self.portal.current_url
        self.addCleanup(self.removeRunAtURL, runURL)

        return Interactions(self, self.portal)

    def removeWorkflowAtURL(self, workflowURL):
        self.portal.get(workflowURL)

        link = self.portal.find_element_by_partial_link_text("Manage workflow")
        self.pause(1)
        link.click()

        link = self.portal.find_element_by_partial_link_text("Delete workflow")
        self.pause(1)
        link.click()

        self.pause(1)
        self.portal.acceptAlert()

        self.pause(1)
        self.portal.get(workflowURL)

        self.assertIn('does not exist', self.portal.getFlashError())
