import os, sys, time, urllib.parse

import requests

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

    def screenshotTag(self):
        return 'ffx'

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
        def screenshotTag(self):
            return 'chr'

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
        if 'screenshotBase' in dir(module):
            self.screenshotBase = module.screenshotBase
        browser = self.getBrowser()
        # ensure browser quit is called, even if setUp fails
        self.addCleanup(browserQuit, browser)
        self.portal = PortalBrowser.PortalBrowser(browser, starturl)


    addPause = False

    def pause(self, t):
        if self.addPause:
            time.sleep(t)

    screenshotBase = None

    def screenshot(self, stubname, location=None, size=None):
        if self.screenshotBase:
            filename = os.path.join(self.screenshotBase, '%s-%s.png' % (stubname, self.screenshotTag()))
            if location is None:
                self.portal.save_screenshot(filename)
            else:
                tmpfile = os.path.join(self.screenshotBase, '%s-%s-full.png' % (stubname, self.screenshotTag()))
                self.portal.save_screenshot(tmpfile)
                from PIL import Image
                # Pass an open file handle to PIL, to allow proper closure
                # (at end of with block) as Python now warns about deleted
                # unclosed files
                with open(tmpfile, 'rb') as f:
                    im = Image.open(f)
                    # Chromium returns floats, but PIL requires ints
                    left = int(location['x'])
                    top = int(location['y'])
                    right = left + int(size['width'])
                    bottom = top + int(size['height'])
                    im = im.crop((left, top, right, bottom))
                    im.save(filename)

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

class WorkflowResult:

    def __init__(self, portal, mimeType, downloadLink):
        self.portal = portal
        self.mimeType = mimeType
        self.downloadLink = downloadLink

    def getMimeType(self):
        return self.mimeType

    def getValue(self):
        cookies = {cookie['name']: cookie['value'] for cookie in self.portal.get_cookies()}
        r = requests.get(self.downloadLink, cookies=cookies)
        r.connection.close()
        return r.text

class WorkflowRun:

    def __init__(self, test, portal):
        self.test = test
        self.portal = portal

    def waitForInteraction(self, *args, **kw):
        return self.portal.waitForInteraction(*args, **kw)

    def waitForFinish(self, *args, **kw):
        self.portal.watchRunStatus(self.test.waitForStatusFinished, *args, **kw)

        results = {}

        runOutputs = self.portal.find_element_by_id('run-outputs')
        for output in runOutputs.find_elements_by_xpath('.//div[@class="output"]'):
            name = output.find_element_by_xpath('./a[@id]').get_attribute('id')
            mimeTypeSpan = output.find_element_by_xpath('.//span[@class="mime_type"]')
            self.test.assertRegex(mimeTypeSpan.text, r'^\([^)]+\)$')
            mimeType = mimeTypeSpan.text[1:-1] # remove outer parentheses
            downloadLink = output.find_element_by_xpath('.//a[@href]').get_attribute('href')
            fullUrl = urllib.parse.urljoin(self.portal.current_url, downloadLink)
            self.test.assertNotIn(name, results)
            results[name] = WorkflowResult(self.portal, mimeType, fullUrl)

        return results


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
        if username:
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
        else:
            # Guest user cannot delete workflow runs
            self.cancelRunAtURL(runURL)

    def runExistingWorkflow(self, name, textInputs=None, fileInputs=None):
        link = self.portal.find_element_by_link_text(name)
        self.portal.click(link)

        link = self.portal.find_element_by_partial_link_text("Run workflow")
        self.portal.click(link)

        inputs = self.portal.workflowInputs()
        if inputs:
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

        self.portal.watchRunStatus(self.waitForStatusRunning, 600)

        return WorkflowRun(self, self.portal)

    def runUploadedWorkflow(self, filename, topic, textInputs=None, fileInputs=None):
        self.portal.selectWorkflowsTab()

        link = self.portal.find_element_by_partial_link_text('Upload a workflow')
        self.pause(1)
        link.click()

        workflowFileInput = self.portal.find_element_by_id('workflow_data')
        self.pause(1)
        workflowFileInput.send_keys(os.path.join(os.getcwd(), filename))

        category = self.portal.find_element_by_id('workflow_category_id')
        self.pause(1)
        select = Select(category)
        select.select_by_visible_text(topic)

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

        inputs = self.portal.workflowInputs()
        if inputs:
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

        self.portal.watchRunStatus(self.waitForStatusRunning, 600)

        return WorkflowRun(self, self.portal)

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
