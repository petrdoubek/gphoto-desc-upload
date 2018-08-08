from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import csv
import json
import selenium
import time

INTERACTIVE = False  # ask before processing each album
ALBUM_NAME_CONTAINS = None  # process only albums whose name contains given string, set to None for all

CREDENTIALS_FILENAME = 'credentials.json'
DESCRIPTIONS_FILENAME = 'captions.txt'
DESCRIPTIONS_DELIMITER = '\t'

CLASS_ALBUM_NAME = 'mfQCMe'
CLASS_ALBUM_LINK = "//a[@class='MTmRkb']"


def wait4xpath(browser, xpath, sec):
    return WebDriverWait(browser, sec).until(EC.presence_of_element_located((By.XPATH, xpath)))


def google_signin(browser, credentials):
    browser.get('https://photos.google.com/login')
    email_field = wait4xpath(browser, "//input[@name='identifier']", 10)
    email_field.send_keys(credentials['username'])
    next_button = browser.find_element_by_id('identifierNext')
    next_button.click()
    time.sleep(1)
    password_field = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.NAME, 'password')))
    password_field.send_keys(credentials['password'])
    signin_button = browser.find_element_by_id('passwordNext')
    signin_button.click()
    time.sleep(1)
    if '2-Step' in browser.page_source:
        input("Please authenticate the login and press Enter")


def photo_open_info(page):
    try:
        info_button = wait4xpath(page, "//div[@aria-label='Open info']", 1)
        if not info_button.is_displayed():
            print('WARNING info button not displayed, moving mouse')
            selenium.webdriver.common.action_chains.ActionChains(page).move_to_element_with_offset(page, 100, 10)
            time.sleep(1)
        info_button.click()
    except:
        print('ERROR unable to open info ... hopefully it is open, continuing')


def photo_close_info(page):
    try:
        page.find_element_by_xpath("//div[@aria-label='Close info']").click()
        time.sleep(1)
    except:
        print('ERROR unable to close info ... probably not needed, continuing')


def photo_get_filename(browser):
    for attempt in range(2):
        time.sleep(2)  # would be faster to wait for the xpath but I do not know how to select only visible elements by xpath
        elems = browser.find_elements_by_xpath("//div[contains(@aria-label, 'Filename: ')]")
        for f in elems:
            if f.is_displayed():
                return f.get_attribute('aria-label').replace('Filename: ', '')

        # no visible filenames found or no filenames at all, try opening Info, unfortunately it vanishes quite often
        if attempt == 0:
            photo_open_info(browser)

    return None


def photo_get_description_elem(browser):
    elems = browser.find_elements_by_xpath("//textarea[@aria-label='Description']")
    for e in elems:
        if e.is_displayed():
            return e
    return None


def process_photo(browser, last_file, descriptions):
    while True:
        filename = photo_get_filename(browser)
        if filename is None:
            if input('  WARNING: No filename, check the page, open Info manually if needed. Read again? [y/n]') == 'n':
                break
        elif filename == last_file:
            if input('  WARNING: Filename repeated, check the page, advance manually if needed. Read again? [y/n]') == 'n':
                break
        else:
            break

    description = photo_get_description_elem(browser)

    if description is None:
        print('  %s: description not editable, most likely not your photo' % filename)
    elif filename in descriptions:
        if len(descriptions[filename]) >= len(description.text):
            print('  %s:  %s  --->  %s' % (filename, description.text, descriptions[filename]))
            description.clear()
            description.send_keys(descriptions[filename])
            time.sleep(1)
        else:
            print('WARNING  %s:  %s  -x->  %s  NEW DESCRIPTION SHORTER, ASSUMING IT IS OUTDATED'
                  % (filename, description.text, descriptions[filename]))
    else:
        print('  %s:  %s  -x->' % (filename, description.text))

    return filename


def all_albums_page(browser):
    browser.get('https://photos.google.com/albums')
    time.sleep(1)
    assert 'Albums - Google Photos' in browser.title


def album_name(a):
    return a.find_element_by_class_name(CLASS_ALBUM_NAME).text


def process_album(browser, a, descriptions):
    # open album in new tab
    browser.execute_script("window.open('%s', 'album');" % a.get_attribute('href'))
    browser.switch_to.window('album')

    # find first photo
    try:
        photo_link = wait4xpath(browser, "//a[contains(@aria-label, 'Photo - ')]", 10)
    except selenium.common.exceptions.NoSuchElementException:
        print('WARNING empty album?')
        photo_link = None

    # go the first photo and use "Next" button to iterate through whole album
    last_file = None
    while photo_link:
        try:
            photo_link.click()
        except selenium.common.exceptions.ElementNotVisibleException:
            break  # indicates the last file

        last_file = process_photo(browser, last_file, descriptions)

        photo_link = browser.find_element_by_xpath("//div[@aria-label='View next photo']")

    time.sleep(3)
    browser.close()
    browser.switch_to.window(browser.window_handles[0])


def process_account(credentials_filename, descriptions_filename):
    credentials = load_credentials(credentials_filename)
    descriptions = load_descriptions(descriptions_filename)

    browser = webdriver.Chrome()
    browser.implicitly_wait(1)
    google_signin(browser, credentials)

    all_albums_page(browser)
    albums = browser.find_elements_by_xpath(CLASS_ALBUM_LINK)

    for a in albums:
        name = album_name(a)
        if ALBUM_NAME_CONTAINS is None or ALBUM_NAME_CONTAINS in name:
            print('Album: %s' % name)
            if not INTERACTIVE or input('Process? [y/n]') == 'y':
                process_album(browser, a, descriptions)

    time.sleep(5)
    browser.quit()


def load_credentials(credentials_filename):
    with open(credentials_filename, 'r') as file:
        credentials = json.load(file)
        assert 'username' in credentials and 'password' in credentials
    print('Credentials loaded from %s.' % credentials_filename)
    return credentials


def load_descriptions(descriptions_filename):
    descriptions = {}
    with open(descriptions_filename, 'r') as file:
        reader = csv.reader(file, delimiter=DESCRIPTIONS_DELIMITER)
        for row in reader:
            if len(row) >= 2:
                descriptions[row[0]] = row[1]
                if len(row) >= 3 and len(row[2]) > 1 and row[2][0] != '<':
                    descriptions[row[0]] += '; ' + row[2]
    print('Descriptions loaded from %s, %d records.' % (descriptions_filename, len(descriptions)))
    return descriptions


"""MAIN"""
process_account(CREDENTIALS_FILENAME, DESCRIPTIONS_FILENAME)
