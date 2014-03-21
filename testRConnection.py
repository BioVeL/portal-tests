import platform, unittest

from BaseTest import WorkflowTest, WithFirefox, WithChrome, username


class RunRConnectionTest(WorkflowTest):

    def test_workflow(self):
        run = self.runUploadedWorkflow('t2flow/Rconnect.t2flow', 'Other')

        results = run.waitForFinish(60)

        out = results['out']
        value = out.getValue()
        if out.getMimeType() == 'application/x-error':
            self.fail(value)
        else:
            self.assertEqual(value, '28364')

# Firefox on Windows hangs on click of Workflow Submit button using Selenium, but
# not when running workflow manually
# confirmed on (FF27.0.1, Win7)
@unittest.skipIf(platform.system() == 'Windows', 'Selenium hangs with Firefox on Windows')
@unittest.skipUnless(username, 'No username login provided')
class RunRConnectionTestFirefox(RunRConnectionTest, unittest.TestCase, WithFirefox):
    pass

if WithChrome:
    @unittest.skipUnless(username, 'No username login provided')
    class RunRConnectionTestChrome(RunRConnectionTest, unittest.TestCase, WithChrome):
        pass


if __name__ == '__main__':
    unittest.main()
