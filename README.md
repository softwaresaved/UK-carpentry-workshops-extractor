# UK-carpentry-workshops-extractor
This project contains a Ruby script that extracts the details of Carpentry workshops and instructors per country recorded in Software Carpentry's AMY system and saves them to a set of CSV files (named after the date they are generated on and the country they are from, e.g. `carpentry-workshops_GB_2017-06-26.csv`, `carpentry-instructors_GB_2017-06-26.csv`).

This includes Software Carpentry, Data Carpentry and Train The Trainer (instructor training) workshops (as well as Library Carpentry workshops when they start being recorded in AMY, and any other future workshop types).

The script uses AMY's public API to extract certain information, but also accesses some private pages (to extract additional data not exposed via the API). Hence, in order for the script to work fully, one needs to have an account in AMY (with a proper username and password, not AMY's authentication via GitHub).

Tested with `ruby 2.2.1`.

## Setup
You can pass various command line options to the script (see the section below). There are defaults set for all the options but your AMY username and password. You have to either pass them as command line arguments, or configure them in  special config file `amy_login.yml`.

To do the latter, create a copy of `amy_login.yml.pre` config file (located in the project root), rename it to `amy_login.yml` and configure your AMY username and password there accordingly. Make sure you do not share this file with the others as it contains sensitive information.

## Running the script
From the project root, do:

```$ ruby extract-workshops-instructors.rb```

There are several command line options available, see below for details.

```
$ ruby extract-workshops-instructors.rb -h
Usage: ruby extract-workshops-instructors.rb [-u USERNAME] [-p PASSWORD] [-c COUNTRY_CODE] [-w WORKSHOPS_FILE] [-i INSTRUCTORS_FILE]

    -u, --username USERNAME          Username to use to authenticate to AMY
    -p, --password PASSWORD          Password to use to authenticate to AMY
    -c, --country_code COUNTRY_CODE  ISO-3166-1 two-letter country_code code or 'all' for all countries. Defaults to 'GB'.
    -w WORKSHOPS_FILE,               File path where to save the workshops extracted from AMY to. Defaults to carpentry-workshops_COUNTRY_CODE_DATE.csv.
        --workshops_file
    -i INSTRUCTORS_FILE,             File path where to save the instructors extracted from AMY to. Defaults to carpentry-instructors_COUNTRY_CODE_DATE.csv.
        --instructors_file
    -v, --version                    Show version
    -h, --help                       Show this help message
```