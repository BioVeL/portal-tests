import unittest
from BaseTest import BaseTest, WithFirefox, WithChrome, username, password


class SignInWithPassword(BaseTest):

    def test_can_access_as_visitor(self):

        title = self.portal.title
        self.assertIn('BioVeL', title)
        self.assertIn('Portal', title)

        self.assertFalse(self.portal.isSignedIn())

        self.portal.signInWithPassword(username, password)

        self.assertTrue(self.portal.isSignedIn())

        self.portal.signOut()

        self.assertFalse(self.portal.isSignedIn())


@unittest.skipUnless(username, 'No username login provided')
class SignInWithPasswordFirefox(SignInWithPassword, unittest.TestCase, WithFirefox):
    pass


if WithChrome:
    @unittest.skipUnless(username, 'No username login provided')
    class SignInWithPasswordChrome(SignInWithPassword, unittest.TestCase, WithChrome):
        pass



if __name__ == '__main__':
    unittest.main()
