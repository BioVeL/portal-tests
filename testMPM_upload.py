import os, platform, unittest, urllib.request

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions

from BaseTest import WorkflowTest, WithFirefox, WithChrome, username


class RunMPMWorkflow(WorkflowTest):

    def test_tutorial(self):
        run = self.runUploadedWorkflow(
            'BioVeL_POP_MPM/matrix_population_model_analysis_v10.t2flow',
            'Population Modelling',
            textInputs=self.textInputs,
            fileInputs=self.fileInputs
        )

        with run.waitForInteraction(300, 1):
            confirm = self.portal.wait(60).until(
                expected_conditions.presence_of_element_located(
                    (By.XPATH, '//*[@id="submit"]/input[@value="Confirm"]')
                    )
                )
            rows = self.portal.find_elements_by_xpath('//*[@id="content"]/tr')
            self.assertTrue(rows, 'no interaction stage rows found')
            for tr in rows:
                stage = tr.find_element_by_xpath('./td[1]').text
                self.assertIn(stage, self.abundances)
                if stage in ('S', 'J'):
                    recruited = tr.find_element_by_xpath('./td[2]/input[@type="checkbox"]')
                    recruited.click()
                    self.pause(0.5)
                elif stage == 'G':
                    reproductive = tr.find_element_by_xpath('./td[3]/input[@type="checkbox"]')
                    reproductive.click()
                    self.pause(0.5)
            self.pause(1)
            confirm.click()

        with run.waitForInteraction(300, 1):
            confirm = self.portal.wait(60).until(
                expected_conditions.presence_of_element_located(
                    (By.XPATH, '//*[@id="content"]/input[@value="Confirm"]')
                    )
                )
            rows = self.portal.find_elements_by_xpath('//*[@id="content"]/div')
            self.assertTrue(rows, 'no interaction abundance rows found')
            for div in rows:
                stage = div.find_element_by_tag_name('label').text
                self.assertIn(stage, self.abundances)
                textbox = div.find_element_by_tag_name('input')
                textbox.send_keys(Keys.BACK_SPACE + str(self.abundances[stage]))
                self.pause(0.5)
            self.pause(0.5)
            confirm.click()

        results = run.waitForFinish(300, 1)

        for result in results.values():
            if result.getMimeType() == 'application/x-error':
                self.fail(result.getValue())

class MPMDefaultInputs:

    textInputs = None
    fileInputs = None
    abundances = {
        'S': 69,
        'J': 111,
        'V': 100,
        'G': 21,
        'D': 43
    }

class MPMTutorialInputs:
    textInputs = {
        'iterations': 1000
    }
    fileInputs = {
        'stageMatrixFile': os.path.join(os.getcwd(), 'BioVeL_POP_MPM/MTers87_88.txt')
    }
    abundances = {
        'S': 69,
        'J': 111,
        'V': 100,
        'G': 21,
        'D': 43
    }

# Firefox on Windows hangs on click of Workflow Submit button using Selenium, but
# not when running workflow manually
# confirmed on (FF27.0.1, Win7)
@unittest.skipIf(platform.system() == 'Windows', 'Selenium hangs with Firefox on Windows')
@unittest.skipUnless(username, 'No username login provided')
class RunMPMDefaultFirefox(MPMDefaultInputs, RunMPMWorkflow, unittest.TestCase, WithFirefox):
    pass

if WithChrome:
    @unittest.skipUnless(username, 'No username login provided')
    class RunMPMDefaultChrome(MPMDefaultInputs, RunMPMWorkflow, unittest.TestCase, WithChrome):
        pass

# Firefox on Windows hangs on click of Workflow Submit button using Selenium, but
# not when running workflow manually
# confirmed on (FF27.0.1, Win7)
@unittest.skipIf(platform.system() == 'Windows', 'Selenium hangs with Firefox on Windows')
@unittest.skipUnless(username, 'No username login provided')
class RunMPMTutorialFirefox(MPMTutorialInputs, RunMPMWorkflow, unittest.TestCase, WithFirefox):
    pass

if WithChrome:
    @unittest.skipUnless(username, 'No username login provided')
    class RunMPMTutorialChrome(MPMTutorialInputs, RunMPMWorkflow, unittest.TestCase, WithChrome):
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
