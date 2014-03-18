import os.path, platform, shutil, tempfile, time, urllib.parse, urllib.request
import unittest

from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions

from BaseTest import WorkflowTest, WorkflowRun, WithFirefox, WithChrome


class RunDRWWorkflow(WorkflowTest):

    def setUp(self):
        super().setUp()
        saveURL = self.portal.current_url
        self.portal.get('https://wiki.biovel.eu/x/e4Sz')
        self.screenshot('inputFileOnWiki')
        content = self.portal.find_element_by_id('content')
        link = content.find_element_by_link_text('inputfile_DRW_lessonA_105recs_v2.csv')
        fileUrl = link.get_attribute('href')
        fullUrl = urllib.parse.urljoin(self.portal.current_url, fileUrl)
        tempdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tempdir, ignore_errors=True)
        self.inputFile = os.path.join(tempdir, 'inputfile_DRW_lessonA_105recs_v2.csv')
        urllib.request.urlretrieve(fullUrl, self.inputFile)
        self.portal.get(saveURL)

    def test_drw_workflow(self):
        self.screenshot('screen-drw-09a')

        link = self.portal.find_element_by_partial_link_text("Taxonomic Refinement")
        self.pause(1)
        self.portal.click(link)

        self.screenshot('screen-drw-10a')

        run = self.runExistingWorkflow('Data Refinement Workflow v14')

        # Store the run URL here, to help with browser restart. If we do this
        # later, we tend to get the interaction page URL instead
        runUrl = self.portal.current_url

        # Choose Input file
        with run.waitForInteraction(300) as interaction:
            continueButton = self.portal.wait(60).until(
                expected_conditions.element_to_be_clickable((By.XPATH, '//button/div[text()="Submit"]')))
            title = self.portal.find_element_by_xpath('/html/body/table/tbody/tr[1]/td/div').text
            self.assertEqual(title, 'Choose Input file')
            fileInput = self.portal.find_element_by_xpath('/html/body/table/tbody/tr[2]/td/form/input')
            self.pause(1)
            fileInput.send_keys(self.inputFile)
            self.screenshot('screen-drw-11b', interaction.location, interaction.size)
            self.pause(1)
            self.portal.click(continueButton)

        class ExitInteraction(Exception):
            pass
        try:
            # Choose Sub-workflow
            with run.waitForInteraction(300) as interaction:
                continueButton = self.portal.wait(60).until(
                    expected_conditions.element_to_be_clickable((By.XPATH, '//button/div[text()="OK"]')))
                title = self.portal.find_element_by_xpath('/html/body/table/tbody/tr[1]/td/div').text
                self.assertEqual(title, 'Choose Sub-Workflow')
                self.screenshot('screen-drw-12a', interaction.location, interaction.size)
                self.pause(1)
                # For normal exit of the with block, the code will wait until
                # the interaction disappears. To exit without that, we raise
                # an exception.
                raise ExitInteraction()
        except ExitInteraction:
            pass

        # Demonstration of quitting browser, and restarting
        self.restartBrowser()
        self.pause(1)
        self.screenshot('screen-drw-12b')

        self.portal.selectRunsTab()
        self.pause(1)
        self.screenshot('screen-drw-13a')

        # Return to run - we don't actually select the run from the Runs tab, as
        # we would have to work out which run was ours - we use our saved URL
        self.portal.get(runUrl)

        # Need to update run to use new portal
        run = WorkflowRun(self, self.portal)
        time.sleep(2)

        # Choose Sub-workflow
        with run.waitForInteraction(300) as interaction:
            continueButton = self.portal.wait(60).until(
                expected_conditions.element_to_be_clickable((By.XPATH, '//button/div[text()="OK"]')))
            title = self.portal.find_element_by_xpath('/html/body/table/tbody/tr[1]/td/div').text
            self.assertEqual(title, 'Choose Sub-Workflow')
            input = self.portal.find_element_by_xpath('//label[text()="Data Selection (BioSTIF)"]/../input')
            self.pause(1)
            input.click()
            self.screenshot('screen-drw-13b', interaction.location, interaction.size)
            self.pause(1)
            self.portal.click(continueButton)

        # BioSTIF
        with run.waitForInteraction(300) as interaction:
            # There are a series of alerts that may show up during BioSTIF
            # initialisation. We can usually plough on after accepting, but
            # sometimes it's a real failure and we need to abort
            try:
                self.portal.wait(15).until(
                    expected_conditions.alert_is_present()
                    )
                self.pause(5)
                alert = self.portal.switch_to_alert()
                text = alert.text
                if text == '[msg_error_application_start_failed]':
                    alert.accept()
                    self.portal.switch_to_default_content()
                    interaction.switchBack()
                    self.portal.wait(15).until(
                        expected_conditions.alert_is_present()
                        )
                    self.pause(5)
                    alert = self.portal.switch_to_alert()
                    text = alert.text
                self.assertEqual(text, 'BioSTIF cannot be started OpenLayers is not defined')
                alert.accept()
                try:
                    self.portal.switch_to_default_content()
                except UnexpectedAlertPresentException:
                    # Sometimes, in Chrome, a third dialog appears immediately
                    # after the above one - and we cannot continue
                    alert = self.portal.switch_to_alert()
                    self.assertEqual(alert.text, 'BioSTiF could not start:  an error occurred: Error initializing BioSTIF: OpenLayers is not defined')
                    self.fail('Error initializing BioSTIF: OpenLayers is not defined')
                interaction.switchBack()
            except TimeoutException:
                # Normal execution with no alerts (or only the first) should
                # end up here
                pass

            # Select draw polygon
            polygonButton = self.portal.wait(60).until(
                expected_conditions.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.mapControl.polygonDeactivated")
                    )
                )
            polygonButton.click()

            # Get size of map view
            mapViewPortElement = self.portal.wait(10).until(
                expected_conditions.presence_of_element_located(
                    (By.ID, "OpenLayers.Map_12_OpenLayers_ViewPort")
                    )
                )
            mapHeight = mapViewPortElement.size['height']
            mapWidth = mapViewPortElement.size['width']

            with open('file0.html', 'wt') as f:
                f.write(self.portal.page_source)

            # Define the points where we are going to click to make the polygon
            points = [(0.45, 0.5), (0.42, 0.7), (0.53, 0.9), (0.55, 0.5)]

            # Draw the polygon
            (prevX, prevY) = points.pop(0)
            chain = ActionChains(self.portal.browser).move_to_element_with_offset(
                mapViewPortElement, int(prevX*mapWidth), int(prevY*mapHeight)
                )
            for (x, y) in points:
                chain = chain.click().move_by_offset(
                    int((x-prevX)*mapWidth), int((y-prevY)*mapHeight)
                    )
                prevX = x
                prevY = y
            chain.double_click().perform()
            time.sleep(5)
            self.screenshot('screen-drw-14a', interaction.location, interaction.size)

            # Filter elements inside polygon
            filterButton = self.portal.wait(30).until(
                expected_conditions.presence_of_element_located(
                    (By.ID, "smallButton filter")
                    )
                )
            self.pause(1)
            filterButton.click()

            # We cheat a little here. Removing the layers is tricky using
            # Selenium because the 'no overlay' option is not visible on many
            # displays. Scrolling a menu created using a div and CSS is hard,
            # so we reverse the order of the screenshots to get what we need
            time.sleep(5)
            self.screenshot('screen-drw-15a', interaction.location, interaction.size)

            dropdown = self.portal.find_element_by_xpath('//div[@id="mapContainerDiv"]//div[@title="Select layer for spatial filtering"]')
            self.pause(1)
            dropdown.click()

            menuItem = dropdown.find_element_by_xpath('..//dt[text()="ETOPO1 Global Relief Model"]')
            self.pause(1)
            menuItem.click()

            # For screenshot, we let the layer load, and then open the menu again
            time.sleep(5)
            dropdown.click()
            time.sleep(1)
            self.screenshot('screen-drw-14b', interaction.location, interaction.size)

            # Click ok to save changes and go back to subworkflow chooser
            bioStifSaveButton = self.portal.wait(10).until(
                expected_conditions.presence_of_element_located(
                    (By.ID, "user_ok")
                    )
                )
            bioStifSaveButton.click()

        # # Choose Sub-workflow
        # with run.waitForInteraction(300, 1):
        #     continueButton = self.portal.wait(60).until(
        #         expected_conditions.element_to_be_clickable((By.XPATH, '//button/div[text()="OK"]')))
        #     title = self.portal.find_element_by_xpath('/html/body/table/tbody/tr[1]/td/div').text
        #     self.assertEqual(title, 'Choose Sub-Workflow')
        #     input = self.portal.find_element_by_xpath('//label[text()="Data Quality (Google Refine)"]/../input')
        #     self.pause(1)
        #     input.click()
        #     self.screenshot('ChooseRefine')
        #     self.pause(1)
        #     self.portal.click(continueButton)

        # Choose Sub-workflow
        with run.waitForInteraction(300) as interaction:
            continueButton = self.portal.wait(60).until(
                expected_conditions.element_to_be_clickable((By.XPATH, '//button/div[text()="OK"]')))
            title = self.portal.find_element_by_xpath('/html/body/table/tbody/tr[1]/td/div').text
            self.assertEqual(title, 'Choose Sub-Workflow')
            input = self.portal.find_element_by_xpath('//label[text()="End Workflow"]/../input')
            self.pause(1)
            input.click()
            self.screenshot('screen-drw-20b', interaction.location, interaction.size)
            self.pause(1)
            self.portal.click(continueButton)

        results = run.waitForFinish(300)

        csv_output = results['csv_output'].getValue()
        count = csv_output.count('\n')
        print(count)

        self.screenshot('screen-drw-21a')

# Firefox on Windows hangs on click of Run Workflow button using Selenium, but
# not when running workflow manually
# confirmed on (FF27.0.1, Win7)
@unittest.skipIf(platform.system() == 'Windows', 'Selenium hangs with Firefox on Windows')
class RunDRWWorkflowFirefox(RunDRWWorkflow, unittest.TestCase, WithFirefox):
    pass

if WithChrome:
    class RunDRWWorkflowChrome(RunDRWWorkflow, unittest.TestCase, WithChrome):
        pass


if __name__ == '__main__':
    import sys
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--pause':
            pause = True
            del sys.argv[i]
        elif arg.startswith('--screenshot='):
            screenshotBase = arg.split('=', 1)[1]
            del sys.argv[i]
        else:
            i += 1
    unittest.main()
