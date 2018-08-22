import selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

import csv
import json
import time

IMPLICIT_WAIT_SEC = 3

ADD_COLUMNS = True  # normally descriptions file has 2 columns: filename, description; add any additional columns to description?
ONLY_DOWNLOAD = False  # opposite mode, download the captions instead of uploading
ASK_ALBUMS = False  # ask before processing each album
REMOVE_HASHTAGGED = False  # if photo filename is preceded by hash in the descriptions file, remove it from the album
ALBUM_NAME_CONTAINS = None  # process only albums whose name contains given string, set to None for all
SKIP_ALBUMS_UNTIL = None  # skip all albums until the one that contains this string, set to None for no skipping

CREDENTIALS_FILENAME = 'credentials.json'
DESCRIPTIONS_FILENAME = 'captions.txt'
DESCRIPTIONS_DELIMITER = '\t'
DOWNLOAD_FILENAME = 'download.txt'

CLASS_ALBUM_NAME = 'mfQCMe'
CLASS_ALBUM_LINK = "//a[@class='MTmRkb']"


def wait4xpath(browser, xpath, first_visible=False):
    elems = browser.find_elements_by_xpath(xpath)
    if first_visible:
        elem = next(iter([ e for e in elems if e.is_displayed() ]), None)
    else:
        elem = elems[0] if len(elems) > 0 else None
    if elem is not None:
        selenium.webdriver.common.action_chains.ActionChains(browser).move_to_element(elem).perform()
    return elem


def google_signin(browser, credentials):
    browser.get('https://photos.google.com/login')
    email_field = wait4xpath(browser, "//input[@type='email' and @name='identifier']")
    email_field.send_keys(credentials['username'])
    next_button = wait4xpath(browser, "//div[@role='button' and @id='identifierNext']")
    next_button.click()
    time.sleep(1)
    password_field = wait4xpath(browser, "//input[@type='password' and @name='password']")
    password_field.send_keys(credentials['password'])
    signin_button = wait4xpath(browser, "//div[@role='button' and @id='passwordNext']")
    signin_button.click()
    time.sleep(1)
    if '2-Step' in browser.page_source:
        input("Please authenticate the login and press Enter")


def photo_open_info(browser):
    """open the Info tab and make sure it is open"""
    for attempt in range(3):
        # look for Close Info button, if it is visible all is good
        close_button = wait4xpath(browser, "//div[@role='button' and @aria-label='Close info']", first_visible=True)
        if close_button is not None:
            return

        # locate info button, if found click it
        info_button = wait4xpath(browser, "//div[@aria-label='Open info']", first_visible=True)
        if info_button is not None:
            info_button.click()
            return

        # move mouse near the top of the screen, hope it brings info button up
        selenium.webdriver.common.action_chains.ActionChains(browser).move_to_element_with_offset(browser, 100, 10)

    input("WARNING: Cannot open info, please help! (Then press Enter)")


def photo_remove_from_album(browser):
    more_clicked, menu_clicked = False, False
    for attempt in range(5):  # this is problematic action, finding/clicking the menu item sometimes takes several attempts
        if not more_clicked:
            more_options = wait4xpath(browser, "//div[@aria-label='More options' and @role='button']", first_visible=True)
            if more_options is None:
                time.sleep(1)
                continue
            more_options.click()
            more_clicked = True

        if not menu_clicked:
            remove_menu = wait4xpath(browser, "//div[div[text()='Remove from album']]", first_visible=True)
            if remove_menu is None:
                time.sleep(1)
                continue
            remove_menu.click()
            time.sleep(1)
            if wait4xpath(browser, "//div[text()='Remove item from album?']") is None:  # verify the popup appeared
                time.sleep(1)
                continue
            menu_clicked = True

        remove_button = wait4xpath(browser, "//div[@role='button' and content/span='Remove']", first_visible=True)
        if remove_button is None:
            time.sleep(1)
            continue
        remove_button.click()
        return

    input("Cannot remove from album, please help! (Then press Enter)")


def photo_get_filename(browser):
    for attempt in range(3):
        time.sleep(1)
        elem = wait4xpath(browser, "//div[contains(@aria-label, 'Filename: ')]", first_visible=True)
        if elem is not None:
            return elem.get_attribute('aria-label').replace('Filename: ', '')
        time.sleep(1)  # need this, it takes time for the info tab to appear

    return None


def photo_set_description(desc, text):
    desc.clear()
    desc.send_keys(text)
    time.sleep(1)


def process_photo(browser, last_file, descriptions, download_file, album):
    max_attempts = 3
    while True:
        filename = photo_get_filename(browser)
        if filename is None:
            if input('  WARNING: No filename, check the page, open Info manually if needed. Read again? [y/n]') == 'n':
                break
        elif filename == last_file:
            if max_attempts > 0:
                max_attempts -= 1
                browser.refresh()
                time.sleep(1)
                continue
            if input('  WARNING: Filename repeated, check the page, advance manually if needed. Read again? [y/n]') == 'n':
                break
        else:
            break

    desc = wait4xpath(browser, "//textarea[@aria-label='Description']", first_visible=True)

    if ONLY_DOWNLOAD:
        download_file.write('%s%s%s\n' %
                            (filename, DESCRIPTIONS_DELIMITER, desc.text if desc is not None else ''))
        return filename

    deleted = False
    if desc is None:
        print('  %s: description not editable, most likely not your photo' % filename)
    elif filename in descriptions:
        if descriptions[filename] == desc.text:
            print('  %s:  %s  ====  %s' % (filename, desc.text, descriptions[filename]))
        elif len(descriptions[filename]) < len(desc.text):
            print('  %s:  %s  -x->  %s  NEW DESCRIPTION SHORTER, ASSUMING IT IS OUTDATED'
                  % (filename, desc.text, descriptions[filename]))
        else:
            print('  %s:  %s  --->  %s' % (filename, desc.text, descriptions[filename]))
            photo_set_description(desc, descriptions[filename])

    elif REMOVE_HASHTAGGED and '#'+filename in descriptions:
        new_text = descriptions['#'+filename] + (' (removed from %s)' % album)
        photo_set_description(desc, new_text)
        photo_remove_from_album(browser)
        print('  %s:  %s  xxxx  %s' % (filename, desc.text, new_text))
        deleted = True
        time.sleep(3)  # TODO
    else:
        print('  %s:  %s  -x->' % (filename, desc.text))

    return filename, deleted


def albums_page(browser):
    browser.get('https://photos.google.com/albums')
    time.sleep(1)
    assert 'Albums - Google Photos' in browser.title


def album_name(a):
    return a.find_element_by_class_name(CLASS_ALBUM_NAME).text


def process_album(browser, a, descriptions, download_file, album):
    # open album in new tab
    browser.execute_script("window.open('%s', 'album');" % a.get_attribute('href'))
    browser.switch_to.window('album')

    # find first photo
    try:
        photo_link = wait4xpath(browser, "//a[contains(@aria-label, 'Photo - ')]")
    except selenium.common.exceptions.NoSuchElementException:
        print('WARNING empty album?')
        photo_link = None

    # go the first photo and use "Next" button to iterate through whole album
    last_file, deleted = None, False
    max_attempts = 5
    while photo_link:
        if not deleted:  # advance to next photo only if the last one was not deleted (in that case it advances automatically)
            try:
                photo_link.click()
                max_attempts = 5
                if last_file is None:
                    photo_open_info(browser)  # open info panel for the first photo
            except selenium.common.exceptions.ElementNotVisibleException:
                break  # indicates the last file
            except selenium.common.exceptions.WebDriverException:
                if max_attempts > 0:
                    max_attempts -= 1
                    time.sleep(1)
                    continue
                input('ERROR when clicking photo, check that browser is on photo page, continue (Enter) or break')

        last_file, deleted = process_photo(browser, last_file, descriptions, download_file, album)
        if not deleted:
            photo_link = wait4xpath(browser, "//div[@aria-label='View next photo']")

    browser.close()
    browser.switch_to.window(browser.window_handles[0])


def process_account(credentials_filename, descriptions_filename):
    credentials = load_credentials(credentials_filename)
    descriptions = load_descriptions(descriptions_filename)
    download_file = None
    if ONLY_DOWNLOAD:
        download_file = open(DOWNLOAD_FILENAME, "w")
        print("Download mode. Opened %s to write descriptions." % DOWNLOAD_FILENAME)

    browser = start_browser()
    google_signin(browser, credentials)
    print("Sign-in completed.")

    albums_page(browser)
    albums = browser.find_elements_by_xpath(CLASS_ALBUM_LINK)
    print("Album links loaded.")

    global SKIP_ALBUMS_UNTIL
    for a in albums:
        name = album_name(a)
        if SKIP_ALBUMS_UNTIL is not None and SKIP_ALBUMS_UNTIL in name:
            SKIP_ALBUMS_UNTIL = None
        if (SKIP_ALBUMS_UNTIL is None) and (ALBUM_NAME_CONTAINS is None or ALBUM_NAME_CONTAINS in name):
            if not ASK_ALBUMS or input('Process %s? [y/n]' % name) == 'y':
                print('Album: %s' % name)
                process_album(browser, a, descriptions, download_file, name)
                continue

        print('Skipped: %s' % name)

    time.sleep(3)
    browser.quit()

    if download_file:
        download_file.close()


def start_browser():
    options = selenium.webdriver.ChromeOptions()
    options.add_argument("--lang=en");
    options.add_experimental_option('prefs', {'intl.accept_languages': 'en_EN'})
    browser = selenium.webdriver.Chrome(options=options)
    browser.implicitly_wait(IMPLICIT_WAIT_SEC)
    return browser


def load_credentials(credentials_filename):
    with open(credentials_filename, 'r') as file:
        credentials = json.load(file)
        assert 'username' in credentials and 'password' in credentials
    print('Credentials loaded from %s.' % credentials_filename)
    return credentials


def load_descriptions(descriptions_filename):
    if ONLY_DOWNLOAD:
        return {}
    descriptions = {}
    with open(descriptions_filename, 'r') as file:
        reader = csv.reader(file, delimiter=DESCRIPTIONS_DELIMITER)
        for row in reader:
            if len(row) >= 2:
                descriptions[row[0]] = row[1]
                if ADD_COLUMNS:
                    for a in row[2:]:
                        if len(a) > 0 and a[0] != '<':
                            descriptions[row[0]] += '; ' + a
            elif len(row) == 1 and row[0][0] == '#':
                descriptions[row[0]] = ''  # filename preceded by hash was my instruction not to include photo in album
    print('Descriptions loaded from %s, %d records.' % (descriptions_filename, len(descriptions)))
    return descriptions


"""MAIN"""
process_account(CREDENTIALS_FILENAME, DESCRIPTIONS_FILENAME)
