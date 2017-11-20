# Carpentry workshops and instructor extractor
This project contains 2 Ruby scripts (`extract_workshops.rb` and `extract_instructors.rb`) that extract the details of Carpentry (Software, Data and Train The Trainer) workshops and instructors per country (or for all countries) recorded in Software Carpentry's AMY system. The extracted data is saved to CSV files named after the date they are generated on and the country they are from, e.g. `carpentry-workshops_GB_2017-06-26.csv`, `carpentry-instructors_GB_2017-06-26.csv` within the `data` folder.

The scripts use AMY's public API to extract certain information, but also accesses some private HTML pages (to extract additional data not exposed via the API). Hence, in order for the script to work fully, one needs to have an account in AMY (with a proper username and password, not using AMY's authentication via GitHub).

Tested with Mac OS Sierra (10.12) and `ruby 2.2.1`.

## Setup
You can pass various command line options to the scripts (see the section below). There are defaults set for all the options, apart from your AMY username and password. You have to either pass them as command line arguments, or configure them in  special config file `amy_login.yml`.

To do the latter, create a copy of `amy_login.yml.pre` config file (located in the project root), rename it to `amy_login.yml` and configure your AMY username and password there accordingly. Make sure you do not share this file with the others as it contains sensitive information.

## Running the scripts
There is a command line script ```run_ingest.sh``` that you can use to run the code, which calls one of the Ruby scripts `extract_workshops.rb` with some parameters pre-filled. You can tweak it to suit your requirements, see below for the available paramaters.

```$ sh run_ingest.sh```

Alternatively, to run the code directly, from the project root do:

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

## Running the analysis and maps
To prepare for running Python install libraries:
* pip install -r requirements.txt

If you want to run the code directly from the project root you can, for example, do:
```python analyse_workshops.py```

Otherwise, There are several command line options available:
```
 analyse_workshops.py -h
usage: analyse_workshops.py [-h] [-w WORKSHOPS_FILE] [-i INSTRUCTORS_FILE]
                            [-gid GOOGLE_DRIVE_DIR_ID]

optional arguments:
  -h, --help            show this help message and exit
  -w WORKSHOPS_FILE, --workshops_file WORKSHOPS_FILE
                        an absolute path to the workshops file to analyse
  -i INSTRUCTORS_FILE, --instructors_file INSTRUCTORS_FILE
                        an absolute path to instructors file to analyse
  -gid GOOGLE_DRIVE_DIR_ID, --google_drive_dir_id GOOGLE_DRIVE_DIR_ID
                        ID of a Google Drive directory where to upload the
                        analyses and map files to
```
