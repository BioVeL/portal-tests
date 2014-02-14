# BioVeL Portal Tests

These tests check that a BioVeL Portal is running OK.

## Prerequisites

The tests require Python 3 and Selenium.

### Ubuntu 12.10 and later

```
$ sudo apt-get install python3 python3-pip

$ sudo pip3 install selenium
```

### Ubuntu 12.04

```
$ sudo apt-get install python3 python3-setuptools

$ sudo easy_install3 pip

$ sudo pip3 install selenium
```

### Windows 7

> Python 3.4 should have simpler instructions, but it has not been generally released.

Download and install the Python 3 MSI Installer from http://www.python.org/

To install Selenium, read the instructions at http://selenium-python.readthedocs.org/en/latest/installation.html#detailed-instructions-for-windows-users

## Running tests

Create a file `config.py` containing a URL for the front page of the portal,
and a username and password for a registered user.  See `config.py.example`
for information

To run all the tests:
```
$ ./test.sh
```

To run an individual test, run the Python file for the test directly, e.g.:
```
$ python3 testSignInAsGuest.py
```

## Configuring Selenium browsers

Firefox is supported out of the box. Tests will be run using Firefox and any
additional browsers that are enabled. i.e. each test may be run multiple times,
using different browsers.

Other browsers typically requires some additional setup to work with Selenium.

### Chromium / Google Chrome

See http://code.google.com/p/selenium/wiki/ChromeDriver

### Internet Explorer

See http://code.google.com/p/selenium/wiki/InternetExplorerDriver

This is currently untested.

### Safari

See http://code.google.com/p/selenium/wiki/SafariDriver

This is currently untested.

## Tests

The tests can be divided into 3 types:

1. General portal tests - simple tests that check that the portal itself is 
working.

2. Simple workflow tests - simple workflow runs to check that basic facilities
and services are running.

3. BioVeL workflow tests - run each BioVeL workflow with particular parameters
and datasets to check that they are working.

