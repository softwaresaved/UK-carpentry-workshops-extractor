import requests
import pandas
import datetime
import yaml
import traceback
import json
import sys
import os

sys.path.append('/lib')
import lib.helper as helper

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0",
    "Accept": "application/json",
}

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = CURRENT_DIR + '/data'
RAW_DATA_DIR = DATA_DIR + '/raw'
AMY_CREDENTIALS_FILE = CURRENT_DIR + '/amy_login.yml'

if not os.path.exists(RAW_DATA_DIR):
    os.makedirs(RAW_DATA_DIR)

AMY_PUBLISHED_WORKSHOPS_API_URL = "https://amy.software-carpentry.org/api/v1/events/published"  # 'Published' workshops are those that went ahead or are likely to go ahead (i.e. have country_code, address, start date, end date, latitude and longitude, etc.)
AMY_PERSONS_API_URL = "https://amy.software-carpentry.org/api/v1/persons/"
AMY_AIRPORTS_API_URL = "https://amy.software-carpentry.org/api/v1/airports/"

AIRPORTS_FILE = DATA_DIR + "/airports.csv"

COUNTRIES_FILE = CURRENT_DIR + "/lib/countries.json"

WORKSHOP_TYPES = ["SWC", "DC", "LC", "TTT"]
STOPPED_WORKSHOP_TYPES = ['stalled', 'cancelled']  # , 'unresponsive']

def get_countries(countries_file):
    countries = None
    if os.path.isfile(countries_file):
        with open(countries_file, 'r') as stream:
            try:
                countries = json.load(stream)
            except Exception as exc:
                print ("An error occurred while reading countries JSON file " + countries_file)
                print(traceback.format_exc())
    else:
        print ("Countries JSON file does not exist " + countries_file)
    return countries


COUNTRIES = get_countries(COUNTRIES_FILE)


def main():
    """
    Main function
    """

    args = helper.parse_command_line_parameters(["-c", "-u", "-p"])

    url_parameters = {
        "country": None, # by default we look for workshops in all countries
        "is_instructor": "true"
    }

    if args.country_code is not None:
        url_parameters["country"] = args.country_code

    if args.username is None and args.password is None:
        args.username, args.password = get_credentials(AMY_CREDENTIALS_FILE)

    workshops = get_workshops(url_parameters, args.username, args.password)
    print("Extracted " + str(workshops.index.size) + " workshops.")
    workshops_file = RAW_DATA_DIR + "/carpentry-workshops" + ("_" + url_parameters["country"] if url_parameters["country"] is not None else "") + "_" + datetime.datetime.today().strftime(
        '%Y-%m-%d') + ".csv"
    workshops.to_csv(workshops_file, encoding = "utf-8", index = False)
    print("Saved workshops to " + workshops_file)

    instructors = get_instructors(url_parameters, args.username, args.password)
    print("Extracted " + str(instructors.index.size) + " instructors.")
    instructors_file = RAW_DATA_DIR + "/carpentry-instructors" + ("_" + url_parameters["country"] if url_parameters["country"] is not None else "") + "_" + datetime.datetime.today().strftime(
        '%Y-%m-%d') + ".csv"
    instructors.to_csv(instructors_file, encoding = "utf-8", index = False)
    print("Saved instructors to " + instructors_file)


def get_workshops(url_parameters=None, username=None, password=None):
    """
    Get 'published' Carpentry workshop events from AMY. 'Published' workshops are those that went ahead or are likely to go ahead (i.e. have country_code, address, start date, end date, latitude and longitude, etc.)
    :param url_parameters: URL parameters to filter results, e.g. by country.
    :param username: AMY username used to authenticate the user accessing AMY's API
    :param password: AMY password to authenticate the user accessing AMY's API
    :return: published workshops as Pandas DataFrame
    """
    print("Extracting workshops from AMY ...")
    # Response is a JSON list of objects containing all published workshops
    response = requests.get(AMY_PUBLISHED_WORKSHOPS_API_URL, headers=HEADERS, auth=(username, password),
                            params=url_parameters)

    workshops = []
    if response.status_code == 200:
        workshops = response.json()

    # We can translate a list of JSON objects/dictionaries directly into a DataFrame
    workshops_df = pandas.DataFrame(workshops,
                                    columns=["slug", "start", "end", "humandate", "venue", "address",
                                             "latitude", "longitude", "tags", "url", "contact", "eventbrite_id", "country"])

    idx = workshops_df.columns.get_loc("country")
    workshops_df.insert(loc=idx, column='country_code',
              value=workshops_df["country"])
    workshops_df["country"] = workshops_df["country_code"].map(lambda country_code: get_country(country_code), na_action = "ignore")

    # Extract workshop type and add as a new column
    workshops_df["workshop_type"] = workshops_df["tags"].map(extract_workshop_type, na_action="ignore")

    # Remove workshops that have been stopped
    workshops_df = workshops_df[workshops_df["workshop_type"].isin(WORKSHOP_TYPES)]

    # Extract workshop year and add as a new column
    workshops_df["year"] = workshops_df["start"].map(lambda date: datetime.datetime.strptime(date, "%Y-%m-%d").year, na_action="ignore")

    return workshops_df


def get_instructors(url_parameters=None, username=None, password=None):
    """
    Get Carpentry instructors registered in AMY.
    :param url_parameters: URL parameters to filter results, e.g. by country.
    :param username: AMY username used to authenticate the user accessing AMY's API
    :param password: AMY password to authenticate the user accessing AMY's API
    :return: instructors as Pandas DataFrame
    """
    print("Extracting instructors from AMY ...")
    # Response is a JSON object containing paged result with info on total number of all results and pointers to previous and next page of results,
    # as well as a list of results for the current page
    response = requests.get(AMY_PERSONS_API_URL, headers=HEADERS, auth=(username, password),
                            params=url_parameters)
    persons = []
    if response.status_code == 200:
        next_url = response.json()["next"]
        persons = response.json()["results"]  # a list extracted from JSON response
        while next_url is not None:
            response = requests.get(next_url, headers=HEADERS, auth=(username, password))
            if response.status_code == 200:
                next_url = response.json()["next"]
                persons.extend(response.json()["results"])

    # We can translate a list of JSON objects/dictionaries directly into a DataFrame
    instructors_df = pandas.DataFrame(persons,
                                      columns=["personal", "middle", "family", "email", "gender", "affiliation",
                                               "awards", "badges", "domains", "github", "orcid", "twitter",
                                               "url", "username", "publish_profile", "tasks", "lessons", "may_contact", "notes", "airport"])

    airports_df = get_airports(None, username, password) # Get all airports
    airports_dict = get_airports_dict(airports_df) # airports as a dictionary for easier mapping

    # Airport field contains URIs like 'https://amy.software-carpentry.org/api/v1/airports/MAN/' so we need to extract the 3-letter airport code out of it (e.g. 'MAN')
    instructors_df["airport_code"] = instructors_df["airport"].map(extract_airport_code)
    instructors_df["airport"] = instructors_df["airport_code"].map(lambda airport_code: airports_dict[airport_code][1], na_action = "ignore")
    instructors_df["airport_longitude"] = instructors_df["airport_code"].map(lambda airport_code: airports_dict[airport_code][2], na_action = "ignore")
    instructors_df["airport_latitude"] = instructors_df["airport_code"].map(lambda airport_code: airports_dict[airport_code][3], na_action = "ignore")
    instructors_df["country_code"] = instructors_df["airport_code"].map(lambda airport_code: airports_dict[airport_code][0] , na_action = "ignore")
    instructors_df["country"] = instructors_df["country_code"].map(lambda country_code: get_country(country_code), na_action = "ignore")

    # Extract year when instructor badges were awarded and add them as new columns
    swc_instructor_badge_awarded = []
    dc_instructor_badge_awarded = []
    lc_instructor_badge_awarded = []
    trainer_badge_awarded = []
    year_earliest_instructor_badge_awarded = []
    for awards_uri in instructors_df["awards"]:
        if response.status_code == 200:
            response = requests.get(awards_uri, headers=HEADERS, auth=(username, password))
            awards = response.json()

            swc_instructor_badge_awarded_date = next((award["awarded"] for award in awards if award["badge"] == "swc-instructor"), None)
            dc_instructor_badge_awarded_date = next((award["awarded"] for award in awards if award["badge"] == "dc-instructor"), None)
            lc_instructor_badge_awarded_date = next((award["awarded"] for award in awards if award["badge"] == "lc-instructor"), None)
            trainer_badge_awarded_date = next((award["awarded"] for award in awards if award["badge"] == "trainer"), None)

            swc_instructor_badge_awarded.append(swc_instructor_badge_awarded_date)
            dc_instructor_badge_awarded.append(dc_instructor_badge_awarded_date)
            lc_instructor_badge_awarded.append(lc_instructor_badge_awarded_date)
            trainer_badge_awarded.append(trainer_badge_awarded_date)

            dates = [swc_instructor_badge_awarded_date, dc_instructor_badge_awarded_date, lc_instructor_badge_awarded_date, trainer_badge_awarded_date]
            dates = filter(None, dates)
            dates = map(lambda date: datetime.datetime.strptime(date, "%Y-%m-%d"), dates)


            year_earliest_instructor_badge_awarded.append(sorted(dates)[0].year if dates != [] else None)

    instructors_df["swc-instructor-badge-awarded"] = pandas.Series(swc_instructor_badge_awarded).values
    instructors_df["dc-instructor-badge-awarded"] = pandas.Series(dc_instructor_badge_awarded).values
    instructors_df["lc-instructor-badge-awarded"] = pandas.Series(lc_instructor_badge_awarded).values
    instructors_df["trainer-badge-awarded"] = pandas.Series(trainer_badge_awarded).values
    instructors_df["year-earliest-instructor-badge-awarded"] = pandas.Series(year_earliest_instructor_badge_awarded).values

    return instructors_df

def get_airports(url_parameters=None, username=None, password=None):
    """
    Gets airport info from AMY
    :param url_parameters: URL parameter dictionary to use when querying AMY (e.g. airports per country)
    :param username: username used to acces AMY's API
    :param password: password used to acces AMY's API
    :return:
    """

    response = requests.get(AMY_AIRPORTS_API_URL, headers=HEADERS, auth=(username, password),
                            params=url_parameters)

    airports = []
    try:
        if response.status_code == 200:
            next_url = response.json()["next"]
            airports = response.json()["results"]  # a list extracted from JSON response
            while next_url is not None:
                response = requests.get(next_url, headers=HEADERS, auth=(username, password))
                if response.status_code == 200:
                    next_url = response.json()["next"]
                    airports.extend(response.json()["results"])

            # We can translate a list of JSON objects/dictionaries directly into a DataFrame
            airports_df = pandas.DataFrame(airports)

            # Save them to file in the case they are not available online on-demand for some reason.
            # Overwrite the old airports with more up-to-date data.
            airports_df.to_csv(AIRPORTS_FILE, encoding = "utf-8", index = False)
        else:
            # Load data from the saved airports file
            airports_df = pandas.read_csv(AIRPORTS_FILE, encoding="utf-8")
    except Exception as exc:
        print ("An error occurred while getting airports data from AMY. Loading airports data from a local file " + AIRPORTS_FILE + "...")
        print(traceback.format_exc())
        # Load data from the saved airports file
        airports_df = pandas.read_csv(AIRPORTS_FILE, encoding = "utf-8")

    #Filter instructors by country - this should be done via URL parameters in the call to the AMY API but it is not implemented in the API yet
    # so we filter them out here
    if (url_parameters is not None and url_parameters["country"] is not None and url_parameters["country"].lower != "all"):
        airports_df = airports_df.loc[airports_df["country"] == url_parameters["country"]]

    return airports_df

def extract_airport_code(str):
    """
    Extract the 3-letter IATA airport code from the URI (e.g. the last 3 letters from 'https://amy.software-carpentry.org/api/v1/airports/MAN/')
    :param str: Airport URI string
    :return: 3-letter airport code extracted from the str
    """
    if str is not None:
        i = str.rfind("/")
        if i != -1:
            return str[i - 3 : i]
    return None

def get_airports_dict(airports_df):
    """
    :param airports_df: dataframe of airports, columns: ['country', 'fullname', 'iata', 'latitude', 'longitude']
    :return: dictionary of airports where column "iata" is the key and value is list ['country', 'fullname', 'latitude', 'longitude']
    """
    return airports_df.set_index('iata').transpose().to_dict('list')

def get_credentials(file_path):
    """
    Extract username and password from a YML file used for authentication with AMY
    :param file_path: YML file with credentials
    :return: username and password
    """
    username = None
    password = None

    if os.path.isfile(file_path):
        with open(file_path, 'r') as stream:
            try:
                amy_credentials_yaml = yaml.load(stream)
            except yaml.YAMLError as exc:
                print ("An error occurred while reading AMY credentials YAML file ...")
                print(traceback.format_exc())

        username = amy_credentials_yaml["amy_credentials"]["username"]
        password = amy_credentials_yaml["amy_credentials"]["password"]
    else:
        print ("AMY credentials YAML file does not exist " + file_path)

    return username, password

def get_country(country_code):
    '''
    :param country_code: 2-letter ISO Alpha 2 country code, e.g. 'GB' for United Kingdom
    :return: country's common name
    '''
    return next((country["name"]["common"] for country in COUNTRIES if country["cca2"] == country_code), None)

def extract_workshop_type(workshop_tags):
    """
    Extract workshop type from a list of workshop tag dictionaries.
    :param workshop_tags:
    :return: workshop type (e.g. "SWC", "DC", "LC" or "TTT")
    """
    tags = list(map(lambda tag: tag["name"], workshop_tags)) # Get the list of tags from the list of dictionaries

     # Is this a stopped workshop (it may not have a type in this case)?
    is_stopped = list(set(tags) & set(STOPPED_WORKSHOP_TYPES))

    workshop_tags = list(set(tags) & set(WORKSHOP_TYPES))

    if is_stopped != []:
        return is_stopped[0]
    elif workshop_tags != []:
        return workshop_tags[0]
    else:
        return ""

if __name__ == '__main__':
    main()
