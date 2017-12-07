# Carpentry workshops and instructor extractors, analysers and mappers
This project contains several ruby and python scripts to extract the details
of Carpentry (Software, Data, Library and Train The Trainer) workshops and instructors
and consequently analyse the extracted data in summary tables and plot it on various graphs and maps.

## Carpentry workshops and instructor extractors (in ruby)

This project contains 2 ruby scripts (`extract_workshops.rb` and `extract_instructors.rb`) that extract
the details of Carpentry workshops
and instructors per country (or for all countries) recorded in Carpentries' system AMY.

The extracted data is saved to CSV files and named after the date they are generated on and the
country they are from, e.g. `carpentry-workshops_GB_2017-06-26.csv`, `carpentry-instructors_AU_2017-06-26.csv`
within the appropriate `data/workshops` or `data/instructors` folders off the project's root.

The scripts use AMY's API to extract certain information, but also access some private HTML pages in AMY's UI
(to extract additional data not exposed via the API). Hence, in order for the script to work fully, one needs to have an account in AMY (with a proper username and password, not using AMY's authentication via GitHub).

Tested with Mac OS Sierra (10.12) and `ruby 2.2.1`.

### Extractor scripts' setup
You can pass various command line options to the scripts (see the section below). There are defaults set for all the options, apart from your AMY username and password. You have to either pass them as command line arguments, or configure them in  special config file `amy_login.yml`.

To do the latter, create a copy of `amy_login.yml.pre` config file (located in the project root), rename it to `amy_login.yml` and configure your AMY username and password there accordingly. Make sure you do not share this file with the others as it contains sensitive information.

### Extractor scripts' dependencies
The following ruby gems are required by the extractor scripts, so you will have to install them prior to running the scripts (e.g. via `bundle install`).
```
yaml
open-uri
json
optparse
ostruct
date
csv
fileutils
nokogiri
```

### Running extractor scripts
To run the extractor scripts, from the project root do:

```$ ruby extract_workshops.rb```

or

```$ ruby extract_instructors.rb```

There are several command line options available, see below for details.
```
$ ruby extract_workshops.rb -h
Usage: ruby extract_workshops.rb [-u USERNAME] [-p PASSWORD] [-c COUNTRY_CODE] [-w WORKSHOPS_FILE]

    -u, --username USERNAME          Username to use to authenticate to AMY
    -p, --password PASSWORD          Password to use to authenticate to AMY
    -c, --country_code COUNTRY_CODE  ISO-3166-1 two-letter country_code code or 'all' for all countries. Defaults to 'GB'.
    -w WORKSHOPS_FILE,               File within 'data/workshops' directory where to save the workshops extracted from AMY to. Defaults to carpentry-workshops_COUNTRY_CODE_DATE.csv.
        --workshops_file
    -v, --version                    Show version
    -h, --help                       Show this help message
```
```
$ ruby extract_instructors.rb -h
Usage: ruby extract_instructors.rb [-u USERNAME] [-p PASSWORD] [-c COUNTRY_CODE] [-i INSTRUCTORS_FILE]

    -u, --username USERNAME          Username to use to authenticate to AMY
    -p, --password PASSWORD          Password to use to authenticate to AMY
    -c, --country_code COUNTRY_CODE  ISO-3166-1 two-letter country_code code or 'all' for all countries. Defaults to 'GB'.
    -i INSTRUCTORS_FILE,             File within 'data/instructors' directory where to save the instructors extracted from AMY to. Defaults to carpentry-instructors_COUNTRY_CODE_DATE.csv.
        --instructors_file
    -v, --version                    Show version
    -h, --help                       Show this help message
```

## Carpentry workshops and instructor analysers and mappers (in python)

The project contains 2 python scripts (`analyse_workshops.py` and `analyse_instructors.py`) to analyse the data resulting from the extraction phase and 5 (at the moment) python mapper scripts (`map_*.py`)
to map the data from the extraction phase.

Analyser scripts creates resulting Excel spreadsheets with various summary tables and graphs and saves them in `data/workshops` or `data/instructors` folders.

Mapper scripts generate various interactive maps embedded in HTML files and stores them in `data/workshops` or `data/instructors` folders.

Finally, there is an option to upload the analyses and maps files to Google Drive, which you have to setup prior to running the scripts. By default, the resulting files are
only saved locally and are not uploaded to Google Drive.

Tested with Mac OS Sierra (10.12) and `python 3.6.0`.

### Analyser and mapper scripts' setup
If you want the scripts to upload the resulting analyses Excel spreadsheets and maps to Google Drive, you need to do the following.

* Generate a project in [Google Developer's Console](https://console.developers.google.com/).

* Enable the [Google Drive API](https://console.developers.google.com/apis/api/drive.googleapis.com/overview) for your project to allow the scripts to access the Google Drive.

* Create a new OAuth client ID from the Google API Console Credential page (the type of client ID
should be set to 'Other'). Detailed instructions on how to this are
[available online](https://developers.google.com/api-client-library/python/samples/samples).
Download the generated credentials file and save it as `client_secret.json` in the root directory of this project.
* You will also need the ID of the parent folder in Google Drive where you want the files to be uploaded, and
 to pass that to the script via the command-line option `-gid` (see below for details). If this option is not specified, by default the scripts will only
 save the generated files to the `data/workshops` or `data/instructors` folders and will not attempt to upload anything to Google Drive.

### Analyser and mapper scripts' dependencies
To prepare your python environment for running the python scripts, you need to install some dependencies listed in `requirements.txt`:

```pip install -r requirements.txt```
```
folium
json
matplotlib
numpy
pandas
pydrive
shapefile
traceback
glob
```
### Running analyser and mapper scripts
To run the analyser and mapper python scrips, from the project root do, e.g.:

```$ python analyse_workshops.py```

or

```$ python analyse_instructors.py```

or, to run one of the mappers, do

```$ python map_instructor_affiliations.py```

There are several command line options available for both analyses and mapper scripts, depending on if they are dealing with workshops or instructors. See below for details.
```
$ python analyse_workshops.py -h
usage: analyse_workshops.py [-h] [-w WORKSHOPS_FILE]
                            [-gid GOOGLE_DRIVE_DIR_ID]

optional arguments:
  -h, --help            show this help message and exit
  -w WORKSHOPS_FILE, --workshops_file WORKSHOPS_FILE
                        an absolute path to the workshops CSV file to analyse
  -gid GOOGLE_DRIVE_DIR_ID, --google_drive_dir_id GOOGLE_DRIVE_DIR_ID
                        ID of a Google Drive directory where to upload the
                        analyses and map files to
```
```
$ python analyse_instructors.py -h
usage: analyse_instructors.py [-h] [-i INSTRUCTORS_FILE]
                              [-gid GOOGLE_DRIVE_DIR_ID]

optional arguments:
  -h, --help            show this help message and exit
  -i INSTRUCTORS_FILE, --instructors_file INSTRUCTORS_FILE
                        an absolute path to instructors CSV file to analyse
  -gid GOOGLE_DRIVE_DIR_ID, --google_drive_dir_id GOOGLE_DRIVE_DIR_ID
                        ID of a Google Drive directory where to upload the
                        analyses and map files to
```
