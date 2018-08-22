# gphoto-desc-upload

**Upload Google Photo Descriptions**

This python script solves the following problem: I uploaded large number of images to Google Photos but I had the descriptions in a text file and wanted to attach them to each photo.

The description file `captions.txt` contains mapping between filename and description, one image per file, tab-separated (as was required by [album generator from Margin Hacks](http://marginalhacks.com/Hacks/album/) which I had been using for many years):

```
file1.jpg   description of first file
file2.jpg   description of second file
```

The script simulates user actions (browsing the photos and adding descriptions) using Selenium Webdriver. It is dependent on certain elements in Google webpage, their names, classes etc. Changes made by Google can break it.

Stable internet connection is required, the script is not designed to recover from lost connection.

## Installation

```
git clone https://github.com/petrdoubek/gphoto-desc-upload.git
```

Or just download [gphoto-desc-upload.py](https://raw.githubusercontent.com/petrdoubek/gphoto-desc-upload/master/gphoto-desc-upload.py). 

Write your Google username and password into `credentials.json` in the same directory as the script:

```json
{
  "username": "someuser",
  "password": "somepassword"
}
```

You also need:

- python 3.6
- Chrome browser (it should be one line change to use different browser but I have not tested)
- [Selenium Webdriver](https://seleniumhq.github.io/selenium/docs/api/py/index.html) - the python package and driver for your browser

## Usage

Prepare `captions.txt` in the same directory as the script and run:

```
python3 gphoto-desc-upload.py
```

The script opens a new browser, logs in to your Google account and browses through all photos in your albums, adding the description if available in your `captions.txt` (as a safeguard it will not replace description by shorter one). One photo takes several seconds so the whole runtime can be quite long.

In some unexpected situations, the script may ask you to check the browser and manually fix the problem, that usually means making sure that the info tab is open and filename is visible. How often it happens depends on responsiveness of the site. From some situations the script does not recover and you have to restart it. Use the configuration below to skip the albums that were already processed.

You can configure some things by changing constants in the code:

- `ADD_COLUMNS`: normally descriptions file has 2 columns: filename, description; add any additional columns to description?
- `ONLY_DOWNLOAD`: opposite mode, download the captions instead of uploading
- `ASK_ALBUMS`: ask before processing each album
- `REMOVE_HASHTAGGED`: if photo filename is preceded by hash in the descriptions file, remove it from the album
- `ALBUM_NAME_CONTAINS`: process only albums whose name contains given string, set to None for all
- `SKIP_ALBUMS_UNTIL`: skip all albums until the one that contains this string, set to None for no skipping

## Disclaimer

Use the script at your risk. Observe first if it does what you would expect before letting it run unsupervised.

## Implementation Notes

### Why not use API?

The API from Google [does not support update of metadata](https://developers.google.com/picasa-web/docs/3.0/releasenotes). Looking back I could have uploaded the photos together with metadata using the API (that is possible).

### Why are there so many sleeps and retrys in the code?

I added them when I experienced a problem with a particular action. Probably some of them are not needed or could be replaced by a cleaner solution, feel free to improve the script.

