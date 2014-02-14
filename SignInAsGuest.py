import unittest
from BaseTest import BaseTest, WithFirefox, WithChrome


class SignInAsGuest(BaseTest):

    def test_can_access_as_visitor(self):
        self.portal.goToStartPage()

        title = self.browser.title
        self.assertIn('BioVeL', title)
        self.assertIn('Portal', title)

        self.assertFalse(self.portal.isSignedIn())

        self.portal.signInAsGuest()

        self.assertTrue(self.portal.isSignedIn())

        self.portal.signOut()

        self.assertFalse(self.portal.isSignedIn())


class SignInAsGuestFirefox(SignInAsGuest, unittest.TestCase, WithFirefox):
    pass


if WithChrome:
    class SignInAsGuestChrome(SignInAsGuest, unittest.TestCase, WithChrome):
        pass


if __name__ == '__main__':
    unittest.main()
