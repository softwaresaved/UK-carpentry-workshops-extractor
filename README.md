# Carpentry workshops and instructor data extracting, analysing and mapping
This project contains several Python standalone and equivalent Jupyter Notebook scripts to extract, analyse and map the details
of Carpentry workshops and instructors from The Carpentry's record keeping system AMY using AMY's API.

## Python version
Recommended Python version is Python 3. Code was tested with Mac OS Sierra (10.12), Mac OS High Sierra (10.13), Mac OS Mojave (10.14) and `python 3.6`. 
Other Python versions may or may not work.

## Dependencies 
Dependencies for the scripts are listed in `requirements.txt` in the project root 
and can be installed via `pip install -r requirements.txt`

## Carpentry workshops and instructor data extraction
The scripts `amy_data_extract.py` extracts the details of Carpentry workshops
and instructors from AMY. It can be configured to extract data for a country or for all countries (which is the default option if none specified).

The extracted data is saved in 2 separate CSV files in `data/raw` folder off the project root - one for instructors and one for workshops. The files
are named after the date they are generated on and the
country the data relate to, e.g. `carpentry-workshops_GB_2017-06-26.csv`, `carpentry-instructors_AU_2017-06-26.csv` or `carpentry-instructors_ALL_2019-07-08.csv`.

### Setup
The script needs to authenticate to AMY so one needs to have an account in AMY (with a proper username and password, not using AMY's authentication via GitHub).
You can configure your login details in `amy_login.yml` file in project root or pass them via command line arguments (in which case the user will be prompted for password which 
will not be echoed - you should never pass password as a command line argument). 

If using a file to configure credentials, rename the existing `amy_login.yml.pre` config file (located in the project root) 
to `amy_login.yml` and configure your AMY username and password there accordingly. Make sure you do not share this file with the others or put it in version control 
as it contains sensitive information.

Alternatively, you can pass username and password as command line parameters to the script via `-u USERNAME -p` command line options, after which you will be prompted to enter your password 
in command line prompt. 
You can pass various other command line options to the script as well - see the section below for details.


### Command line options
You can run the extractor script from the project root using the following command line options.
```
$ python amy_data_extract.py --help
usage: amy_data_extract.py [-h] [-c COUNTRY_CODE] [-u USERNAME]
                           [-p [PASSWORD]]
                           [-out_workshops OUTPUT_WORKSHOPS_FILE]
                           [-out_instructors OUTPUT_INSTRUCTORS_FILE]

optional arguments:
  -h, --help            show this help message and exit
  -c COUNTRY_CODE, --country_code COUNTRY_CODE
                        ISO-3166-1 two-letter country_code code or leave blank
                        for all countries
  -u USERNAME, --username USERNAME
                        Username to login to AMY
  -p [PASSWORD], --password [PASSWORD]
                        Password to log in to AMY - you will be prompted for
                        it (please do not enter your password on the command
                        line even though it is possible)
  -out_workshops OUTPUT_WORKSHOPS_FILE, --output_workshops_file OUTPUT_WORKSHOPS_FILE
                        File path where workshops data extracted from AMY will
                        be saved in CSV format. If omitted, data will be saved
                        to data/raw/ directory and will be named as
                        'carpentry_workshops_<COUNTRY_CODE>_<DATE>'.csv.
  -out_instructors OUTPUT_INSTRUCTORS_FILE, --output_instructors_file OUTPUT_INSTRUCTORS_FILE
                        File path where instructors data extracted from AMY
                        will be saved in CSV format. If omitted, data will be
                        saved to data/raw/ directory and will be named as
                        'carpentry_instructors_<COUNTRY_CODE>_<DATE>'.csv.
```

## Carpentry workshops and instructors analyser scripts

The project contains 2 python scripts - `analyse_workshops.py` and `analyse_instructors.py` - to analyse the data resulting from the extraction phase.
to map the data from the extraction phase.

Analyser scripts create resulting Excel spreadsheets with various summary tables and graphs and saves them in `data/analyses` folders off the project root.

### Command line options
There are several command line options available for analyser scripts, depending on if they are dealing with workshops or instructors. See below for details.
```
$ python analyse_workshops.py --help
usage: analyse_workshops.py [-h] [-in INPUT_FILE] [-out OUTPUT_FILE]

optional arguments:
  -h, --help            show this help message and exit
  -in INPUT_FILE, --input_file INPUT_FILE
                        The path to the input data CSV file to analyse/map. If
                        omitted, the latest file with workshops/instructors
                        data from data/raw/ directory off project root will be
                        used, if such exists.
  -out OUTPUT_FILE, --output_file OUTPUT_FILE
                        File path where data analyses will be saved in xslx
                        Excel format. If omitted, the Excel file will be saved
                        to data/analyses/ directory and will be named as
                        'analysed_<INPUT_FILE_NAME>'.
```
```
$ python analyse_instructors.py --help
usage: analyse_instructors.py [-h] [-in INPUT_FILE] [-out OUTPUT_FILE]

optional arguments:
  -h, --help            show this help message and exit
  -in INPUT_FILE, --input_file INPUT_FILE
                        The path to the input data CSV file to analyse/map. If
                        omitted, the latest file with workshops/instructors
                        data from data/raw/ directory off project root will be
                        used, if such exists.
  -out OUTPUT_FILE, --output_file OUTPUT_FILE
                        File path where data analyses will be saved in xslx
                        Excel format. If omitted, the Excel file will be saved
                        to data/analyses/ directory and will be named as
                        'analysed_<INPUT_FILE_NAME>'.
```