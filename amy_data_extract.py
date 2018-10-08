import requests
import pandas
import datetime
import yaml
import traceback

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

def main():
    """
    Main function
    """

    args = helper.parse_command_line_paramters()

    url_parameters = {
        "country": None, # by default we are for workshops in all countries
        "is_instructor": "true"
    }

    if args.country_code is not None:
        url_parameters["country"] = args.country_code

    if args.username is None and args.password is None:
        args.username, args.password = read_credentials(AMY_CREDENTIALS_FILE)

    workshops = get_workshops(url_parameters, args.username, args.password)
    print("Extracted " + str(workshops.index.size) + " workshops.")
    workshops_file = RAW_DATA_DIR + "/raw_carpentry-workshops" + ("_" + url_parameters["country"] if url_parameters["country"] is not None else "") + "_" + datetime.datetime.today().strftime(
        '%Y-%m-%d') + ".csv"
    workshops.to_csv(workshops_file, encoding = "utf-8")
    print("Saved workshops to " + workshops_file)

    # url_parameters["is_instructor"] = "true"  # We are interested in instructors only
    instructors = get_instructors(url_parameters, args.username, args.password)
    print("Extracted " + str(instructors.index.size) + " instructors.")
    instructors_file = RAW_DATA_DIR + "/raw_carpentry-instructors" + ("_" + url_parameters["country"] if url_parameters["country"] is not None else "") + "_" + datetime.datetime.today().strftime(
        '%Y-%m-%d') + ".csv"
    instructors.to_csv(instructors_file, encoding = "utf-8")
    print("Saved instructors to " + workshops_file)


def get_workshops(url_parameters=None, username=None, password=None):
    """
    Get 'published' Carpentry workshop events from AMY. 'Published' workshops are those that went ahead or are likely to go ahead (i.e. have country_code, address, start date, end date, latitude and longitude, etc.)
    :param url_parameters: URL parameters to filter results, e.g. by country.
    :param username: AMY username used to authenticate the user accessing AMY
    :param password: AMY password to authenticate the user accessing AMY
    :return: published workshops as Pandas DataFrame
    """
    # Response is a JSON list of objects containing all published workshops
    response = requests.get(AMY_PUBLISHED_WORKSHOPS_API_URL, headers=HEADERS, auth=(username, password),
                            params=url_parameters)

    workshops = []
    if response.status_code == 200:
        workshops = response.json()

    # We can translate a list of JSON objects/dictionaries directly into a DataFrame
    workshops_df = pandas.DataFrame(workshops)

    #Filter workshops by country - this should be done via URL parameters in the call to the AMY API but it is not implemented in the API yet
    # so we filter them out here
    if url_parameters["country"] is not None:
        workshops_df = workshops_df.loc[workshops_df["country"] == url_parameters["country"]]

    return workshops_df


def get_instructors(url_parameters=None, username=None, password=None):
    """
    Get Carpentry instructors registered in AMY.
    :param url_parameters: URL parameters to filter results, e.g. by country.
    :param username: AMY username used to authenticate the user accessing AMY
    :param password: AMY password to authenticate the user accessing AMY
    :return: instructors as Pandas DataFrame
    """
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
    #
    # instructors = []
    # for person in persons:
    #     for badge in person["badges"]:
    #         if "instructor" in badge:
    #             instructors.expand(person)  # find instructors only
    # return pandas.load_json(instructors)

    # We can translate a list of JSON objects/dictionaries directly into a DataFrame
    instructors_df = pandas.DataFrame(persons)

    airports_df = get_airports(None, username, password) # Get all airports
    airports_dict = get_airports_dict(airports_df) # airports as a dictionary for easier mapping

    # Airport field contains URIs like 'https://amy.software-carpentry.org/api/v1/airports/MAN/' so we need to extract the 3-letter airport code out of it (e.g. 'MAN')
    instructors_df["airport_code"] = instructors_df["airport"].map(extract_airport_code)
    instructors_df["airport_name"] = instructors_df["airport_code"].map(lambda airport_code: airports_dict[airport_code][1], na_action = "ignore")
    instructors_df["airport_longitude"] = instructors_df["airport_code"].map(lambda airport_code: airports_dict[airport_code][2], na_action = "ignore")
    instructors_df["airport_latitude"] = instructors_df["airport_code"].map(lambda airport_code: airports_dict[airport_code][3], na_action = "ignore")
    instructors_df["country_code"] = instructors_df["airport_code"].map(lambda airport_code: airports_dict[airport_code][0] , na_action = "ignore")

    #Filter instructors by country - this should be done via URL parameters in the call to the AMY API but it is not implemented in the API yet
    # so we filter them out here
    if url_parameters is not None and url_parameters["country"] is not None:
        instructors_df = instructors_df[instructors_df["country_code"] == url_parameters["country"]]

    return instructors_df

def get_airports(url_parameters=None, username=None, password=None):

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
        airports_df.to_csv(AIRPORTS_FILE, encoding = "utf-8")
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
    Extract the 3-letter IATA airport code from str of the form of URI 'https://amy.software-carpentry.org/api/v1/airports/MAN/'
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

def read_credentials(file_path):

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

if __name__ == '__main__':
    main()
