# gphoto-desc-upload

**Upload Google Photo Descriptions**

This python script solves the following problem: I uploaded large number of images to Google Photos but I had the descriptions in a text file and wanted to attach them to each photo.

The description file `captions.txt` contains mapping between filename and description, one image per file, tab-separated (as was required by [album generator from Margin Hacks](http://marginalhacks.com/Hacks/album/) which I had been using for many years):

```
file1.jpg   description of first file
file2.jpg   description of second file
```

The script simulates user actions (browsing the photos and adding descriptions) using Selenium Webdriver. It is dependent on certain elements in Google webpage, their names, classes etc. Thus it is fragile, changes made by Google can break it.

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

You can configure some things by changing the constants, see the script. I have not bothered with command line options as I am not going to use the script after the upload is done.

## Why not use API?

The API from Google [does not support update of metadata](https://developers.google.com/picasa-web/docs/3.0/releasenotes). Looking back I could have uploaded the photos together with metadata using the API (that is possible).