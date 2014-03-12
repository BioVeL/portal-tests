# BioVeL Portal Tests

These tests check that a BioVeL Portal is running OK.

## Prerequisites

The tests require Python 3 and Selenium.

### Ubuntu 12.10 and later

```
$ sudo apt-get install python3 python3-pip

$ sudo pip3 install selenium requests
```

### Ubuntu 12.04

```
$ sudo apt-get install python3 python3-setuptools

$ sudo easy_install3 pip

$ sudo pip3 install selenium requests
```

### Windows 7

Download and install the Python 3.4 MSI Installer from http://www.python.org/

Open a command window and run:
```
C:\Python34\python.exe -m pip install selenium requests
```

## Running tests

*Note, the tests __must__ be run from the top-level directory (the directory
containing this README file).*

Create a file `config.py` containing a URL for the front page of the portal,
and a username and password for a registered user.  See `config.py.example`
for information.

To run all the tests:
```
$ ./test.sh
```

On Windows, run:
```
C:\Python34\python.exe -m unittest discover
```

To run an individual test, run the Python file for the test directly, e.g.:
```
$ python3 testSignInAsGuest.py
```

On Windows, run:
```
C:\Python34\python.exe testSignInAsGuest.py
```

## Known Problems

Selenium InternetExplorer driver does not work with Internet Explorer 11 yet.

Selenium using Firefox 27 on Windows 7 causes Firefox to hang. The problem does
not appear when using Firefox manually, so this seems to be a Selenium problem.


## Configuring Selenium browsers

Firefox is supported out of the box. Tests will be run using Firefox and any
additional browsers that are enabled. i.e. each test may be run multiple times,
using different browsers.

Other browsers typically require some additional setup to work with Selenium.

### Chromium / Google Chrome

See http://code.google.com/p/selenium/wiki/ChromeDriver

### Internet Explorer

See http://code.google.com/p/selenium/wiki/InternetExplorerDriver

This is currently untested.  The current drivers do not support IE11.

### Safari

See http://code.google.com/p/selenium/wiki/SafariDriver

This is currently untested.

## Tests

The tests can be divided into 3 types:

1. General portal tests - simple tests that check that the portal itself is 
working.
  * testSignInAsGuest - sign in with no password
  * testSignInWithPassword - sign in with existing registered user

2. Simple workflow tests - simple workflow runs to check that basic facilities
and services are running.  These tests are uploaded and deleted during the test.
  * testRConnection - check that very simple RShell works with R on localhost

3. BioVeL workflow tests - run each BioVeL workflow with particular parameters
and datasets to check that they are working. This attempts to use the public
workflows already installed in the portal. 
  * tutorial_DRW_A.py
  * testBioVeL_ENM_default - Ecological Niche Modelling workflow default inputs
  * testMPM_upload - Matrix Population Modelling
