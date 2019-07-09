# Carpentry workshops and instructor data extracting, analysing and mapping
This project contains several python standalone scripts (and accompanying ipython notebooks) to extract, analyse and map the details
of Carpentry workshops and instructors from The Carpentry's record keeping system AMY using AMY's API.

Tested with Mac OS Sierra (10.12), Mac OS High Sierra (10.13), Mac OS Mojave (10.14) and `python 3.6`.


## Carpentry workshops and instructor data extraction
The scripts `amy_data_extract.py` extracts the details of Carpentry workshops
and instructors from AMY. It can be configured to extract data for a country or for all countries (which is the default option if none specified).

The extracted data is saved in 2 separate CSV files in `data/raw` folder off the project root - one for instructors and one for workshops. The files
are named after the date they are generated on and the
country the data relate to, e.g. `carpentry-workshops_GB_2017-06-26.csv`, `carpentry-instructors_AU_2017-06-26.csv` or `carpentry-instructors_ALL_2019-07-08.csv`.

### Extractor script's setup
The script needs to authenticate to AMY so one needs to have an account in AMY (with a proper username and password, not using AMY's authentication via GitHub).
You can configure your login details in `amy_login.yml` file in project root or pass them via command line arguments (in which case the user will be prompted for password which 
will not be echoed - you should never pass password as a command line argument). 

If using a file to configure credentials, rename the existing `amy_login.yml.pre` config file (located in the project root) 
to `amy_login.yml` and configure your AMY username and password there accordingly. Make sure you do not share this file with the others or put it in version control 
as it contains sensitive information.

Alternatively, you can pass username and password as command line parameters to the script via `-u USERNAME -p` command line options, after which you will be prompted to enter your password 
in command line prompt. 
You can pass various other command line options to the script as well - see the section below for details.

### Extractor script's dependencies
The following libraries are required by the extractor script, so you will have to install them prior to running it (e.g. via `pip install`).
```
requests
pandas
datetime
yaml
traceback
json
sys
os
re
argparse
getpass
```

### Running extractor script and command line options
You can run the extractor script from the project root using the following command line options.
```
$ python amy_data_extract.py -h
usage: amy_data_extract.py [-h] [-c COUNTRY_CODE] [-u USERNAME]
                           [-p [PASSWORD]]

optional arguments:
  -h, --help            show this help message and exit
  -c COUNTRY_CODE, --country_code COUNTRY_CODE
                        ISO-3166-1 two-letter country_code code or leave blank
                        for all countries
  -u USERNAME, --username USERNAME
                        Username to login to AMY
  -p [PASSWORD], --password [PASSWORD]
                        Password to log in to AMY - you will be prompted for
                        it (do not enter your password on command line even though it is possible)
```

## Carpentry workshops and instructors analyser scripts

The project contains 2 python scripts - `analyse_workshops.py` and `analyse_instructors.py` - to analyse the data resulting from the extraction phase.
to map the data from the extraction phase.

Analyser scripts create resulting Excel spreadsheets with various summary tables and graphs and saves them in `data/analyses` folders off the project root.

### Analyser and mapper scripts' dependencies
The following libraries are required by the analyser scripts, so you will have to install them prior to running it (e.g. via `pip install`).
```
json
matplotlib
numpy
pandas
shapefile
traceback
glob
re
```

### Running analyser scripts and command line options
There are several command line options available for analyser scripts, depending on if they are dealing with workshops or instructors. See below for details.
```
$ python analyse_workshops.py -h
usage: analyse_workshops.py [-h] [-w WORKSHOPS_FILE]

optional arguments:
  -h, --help            show this help message and exit
  -w WORKSHOPS_FILE, --workshops_file WORKSHOPS_FILE
                        An absolute path to the workshops CSV file to
                        analyse/map
```
```
$ python analyse_instructors.py -h
usage: analyse_instructors.py [-h] [-i INSTRUCTORS_FILE]

optional arguments:
  -h, --help            show this help message and exit
  -i INSTRUCTORS_FILE, --instructors_file INSTRUCTORS_FILE
                        An absolute path to instructors CSV file to
                        analyse/map
```
If you do not specify the files with data to analyse (via `-w` or `-i` options), the scripts will just look for the latest workshop or instructor files found in `data/raw` folder.

## Carpentry workshops and instructors mapper scripts

The project contains 2 python mapper scripts - `map_workshops.py` and `map_instructors.py` - to map the data from the extraction phase.

Mapper scripts generate various interactive maps embedded in HTML files and store them in `data/maps` folders. Map types generated include:
* map of markers (each location is a marker on a map)
* map of clustered markers (nearby markers are clustered but can be zoomed in and out of)
* choropleth map (over UK regions only)
* heatmap

### Mapper scripts' dependencies 
The following libraries are required by the mapper scripts, so you will have to install them prior to running it (e.g. via `pip install`).
```
json
matplotlib
numpy
pandas
shapefile
traceback
glob
re
```

### Running mapper scripts and command line options

*Note that mapping instructors only makes sense for UK instructors at the moment, we we only have geodata for UK institutions.*

There are several command line options available for both analyser and mapper scripts, depending on if they are dealing with workshops or instructors. See below for details.
```
$ python map_workshops.py -h
usage: map_workshops.py [-h] [-w WORKSHOPS_FILE]

optional arguments:
  -h, --help            show this help message and exit
  -w WORKSHOPS_FILE, --workshops_file WORKSHOPS_FILE
                        an absolute path to the workshops CSV file to map
```
```
$ python map_instructors.py -h
usage: map_instructors.py [-h] [-i INSTRUCTORS_FILE]

optional arguments:
  -h, --help            show this help message and exit
  -i INSTRUCTORS_FILE, --instructors_file INSTRUCTORS_FILE
                        an absolute path to instructors CSV file to analyse
```
If you do not specify the files with data to analyse (via `-w` or `-i` options), the scripts will just look for the latest workshop or instructor files found in `data/raw` folder.
### Example maps

*Map of clustered markers (UK instructor affiliations 2018-01-14)*

Little orange circles indicate single markers and the numbered clusters indicate the number of markers in each (green show smaller clusters, moving towards bigger yellow clusters). In an interactive version of the map, these can be clicked and zoomed into to expand and reveal the individual markers.

![map of clustered markers](https://github.com/softwaresaved/carpentry-workshops-instructors-extractor/raw/develop/map_clustered_instructor_affiliations_carpentry-instructors_GB_2018-01-14.png)

*Map of markers (UK instructor affiliations 2018-01-14)*

![map of markers](https://github.com/softwaresaved/carpentry-workshops-instructors-extractor/raw/develop/map_instructor_affiliations_carpentry-instructors_GB_2018-01-14.png)

*Choropleth map (UK instructor affiliations 2018-01-14)*

![choropleth map](https://github.com/softwaresaved/carpentry-workshops-instructors-extractor/raw/develop/choropleth_map_instructors_per_UK_regions_carpentry-instructors_GB_2018-01-14.png)

*Heatmap (UK instructor affiliations 2018-01-14)*

![heatmap](https://github.com/softwaresaved/carpentry-workshops-instructors-extractor/raw/develop/heatmap_instructor_affiliations_carpentry-instructors_GB_2018-01-14.png)