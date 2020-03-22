import traceback
import os
import sys
import re
import datetime
import requests
import yaml
import pandas
import lib.helper as helper


sys.path.append('/lib')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0",
    "Accept": "application/json",
}

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = CURRENT_DIR + '/data'
RAW_DATA_DIR = DATA_DIR + '/raw'
PROCESSED_DATA_DIR = DATA_DIR + '/processed'
AMY_CREDENTIALS_FILE = CURRENT_DIR + '/amy_login.yml'

if not os.path.exists(RAW_DATA_DIR):
    os.makedirs(RAW_DATA_DIR)

if not os.path.exists(PROCESSED_DATA_DIR):
    os.makedirs(PROCESSED_DATA_DIR)

AMY_API_ROOT = "https://amy.carpentries.org/api/v1"
AMY_EVENTS_API_URL = AMY_API_ROOT + "/events/"
AMY_PERSONS_API_URL = AMY_API_ROOT + "/persons/"
AMY_AIRPORTS_API_URL = AMY_API_ROOT + "/airports/"

AIRPORTS_FILE = DATA_DIR + "/airports.csv"


def main():
    """
    Main function
    """

    args = helper.parse_command_line_parameters_amy()

    #
    # if args.country_code is not None:
    #     url_parameters["country"] = args.country_code

    if args.username is None and args.password is None:
        args.username, args.password = get_credentials(AMY_CREDENTIALS_FILE)

    if args.raw_workshops_file:
        raw_workshops_file = args.raw_workshops_file
    else:
        raw_workshops_file = RAW_DATA_DIR + "/amy_raw_carpentry_workshops_UK" + "_" + datetime.datetime.today().strftime('%Y-%m-%d') + ".csv"

    if args.processed_workshops_file:
        processed_workshops_file = args.processed_workshops_file
    else:
        processed_workshops_file = PROCESSED_DATA_DIR + "/amy_processed_carpentry_workshops_UK" + "_" + datetime.datetime.today().strftime('%Y-%m-%d') + ".csv"

    if args.raw_instructors_file:
        raw_instructors_file = args.raw_instructors_file
    else:
        raw_instructors_file = RAW_DATA_DIR + "/amy_raw_carpentry_instructors_UK" + "_" + datetime.datetime.today().strftime('%Y-%m-%d') + ".csv"

    if args.processed_instructors_file:
        processed_instructors_file = args.processed_instructors_file
    else:
        processed_instructors_file = PROCESSED_DATA_DIR + "/amy_processed_carpentry_instructors_UK" + "_" + datetime.datetime.today().strftime('%Y-%m-%d') + ".csv"

    if args.username is None or args.password is None:
        print("Either username or password were not provided - cannot authenticate with AMY - exiting.")
    else:
        # Get and process workshop data
        url_parameters = {
            "country": "GB"
        }
        # workshops_df = get_workshops_amy(url_parameters, args.username, args.password)
        #
        # # Save raw workshop data
        # workshops_df.to_csv(raw_workshops_file, encoding="utf-8", index=False)
        # print("Saved a total of " + str(workshops_df.index.size) + " workshops to " + raw_workshops_file + "\n\n")
        #
        # workshops_df = helper.process_workshops(workshops_df)
        #
        # # Save processed workshop data
        # workshops_df.to_csv(processed_workshops_file, encoding="utf-8", index=False)
        # print("Saved processed workshops to " + processed_workshops_file + "\n\n")

        # Get and process instructor data
        instructors_df = get_instructors_amy(url_parameters, args.username, args.password)
        # Save raw instructor data
        instructors_df.to_csv(raw_instructors_file, encoding="utf-8", index=False)
        print("Saved a total of " + str(instructors_df.index.size) + " instructors to " + raw_instructors_file)

        instructors_df = helper.process_instructors(instructors_df)
        # Save processed instructors data
        instructors_df.to_csv(processed_instructors_file, encoding="utf-8", index=False)
        print("Saved processed instructors to " + processed_instructors_file + "\n\n")


def get_workshops_amy(url_parameters=None, username=None, password=None):
    """
    Get Carpentry workshop events from AMY.
    :param url_parameters: URL parameters to filter results, e.g. by country.
    :param username: AMY username used to authenticate the user accessing AMY's API
    :param password: AMY password to authenticate the user accessing AMY's API
    :return: workshops as Pandas DataFrame
    """
    print("\nExtracting workshops from AMY for country: " + (url_parameters["country"] if url_parameters["country"] is not None else "ALL"))
    try:
        # Response is a JSON list of objects containing all published workshops
        response = requests.get(AMY_EVENTS_API_URL, headers=HEADERS, auth=(username, password),
                                params=url_parameters)
        response.raise_for_status()  # check if a request was successful
        workshops_df = []
        print("Total workshops expected: " + str(response.json()["count"]))
        next_url = response.json()["next"]
        print("Getting paged workshop data from " + AMY_EVENTS_API_URL)
        workshops_df = response.json()["results"]  # a list extracted from JSON response
        while next_url is not None:
            response = requests.get(next_url, headers=HEADERS, auth=(username, password))
            response.raise_for_status()  # check if a request was successful
            print("Getting paged workshop data from " + str(next_url))
            next_url = response.json()["next"]
            workshops_df.extend(response.json()["results"])

        # Translate a list of JSON objects/dictionaries directly into a DataFrame
        workshops_df = pandas.DataFrame(workshops_df,
                                        columns=["slug", "start", "end", "attendance", "country", "host", "venue",
                                                 "address", "latitude", "longitude", "tags", "website_url"
                                                 # "contact",
                                                 # "tasks"
                                                 ])

        workshops_df.rename(columns={"country": "country_code", "host": "organiser_uri"}, inplace=True)
        print(workshops_df.columns)
        # print("\n####### Extracted " + str(
        #     workshops_df.index.size) + " workshops; extracting additional workshop instructors info ... #######\n")
        # # Get instructors for workshops
        # workshops_df["instructors"] = workshops_df["tasks"].map(
        #     lambda tasks_url: extract_workshop_instructors(tasks_url, username, password), na_action="ignore")
        # print(workshops_df)

        return workshops_df
    except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as ex:
        # Catastrophic error occurred or HTTP request was not successful for some
        # reason (e.g. status code 4XX or 5XX was returned)
        print("Ops - something went wrong when getting workshops data from AMY...")
        print(ex.format_exc())
        sys.exit(1)


def get_instructors_amy(url_parameters=None, username=None, password=None):
    """
    Get Carpentry instructors registered in AMY.
    :param url_parameters: URL parameters to filter results, e.g. by country.
    :param username: AMY username used to authenticate the user accessing AMY's API
    :param password: AMY password to authenticate the user accessing AMY's API
    :return: instructors as Pandas DataFrame
    """
    print("\nExtracting instructors from AMY for country: " + (url_parameters["country"] if url_parameters["country"] is not None else "ALL"))
    url_parameters.update({"is_instructor": "true"})

    # Response is a JSON object containing paged result with info on total
    # number of all results and pointers to previous and next page of results,
    # as well as a list of results for the current page
    try:
        response = requests.get(AMY_PERSONS_API_URL, headers=HEADERS, auth=(username, password),
                                params=url_parameters)
        response.raise_for_status()  # check if a request was successful
        persons = []
        print("Total instructors expected: " + str(response.json()["count"]))
        next_url = response.json()["next"]
        print("Getting paged instructor data from " + AMY_PERSONS_API_URL)
        persons = response.json()["results"]  # a list of persons (instructors) extracted from JSON response
        while next_url is not None:
            response = requests.get(next_url, headers=HEADERS, auth=(username, password))
            response.raise_for_status()  # check if a request was successful
            print("Getting paged instructor data from " + str(next_url))
            next_url = response.json()["next"]
            persons.extend(response.json()["results"])

        # Translate a list of JSON objects/dictionaries directly into a DataFrame
        instructors_df = pandas.DataFrame(persons,
                                          columns=[  # "personal", "middle", "family", "email", "gender",
                                              "affiliation",
                                              "country",
                                              "awards", "badges", "domains",
                                              # "github", "orcid", "twitter",
                                              # "url", "username", "publish_profile", "tasks",
                                              "lessons",
                                              # "may_contact", "notes",
                                              "airport"])

        print("\n####### Extracted " + str(
            instructors_df.index.size) + " instructors; extracting additional instructors info ... #######\n")

        instructors_df.rename(columns={"affiliation": "institution", "country" : "country_code"}, inplace=True)

        airports_df = get_airports(None, username, password)  # Get all airports
        airports_dict = get_airports_dict(airports_df)  # airports as a dictionary for easier mapping

        # 'airport' field contains URIs like 'https://amy.carpentries.org/api/v1/airports/MAN/'
        # so we need to extract the 3-letter airport code out of it (e.g. 'MAN') and then use it to find
        # airport's name, longitude and latitude
        instructors_df["airport_code"] = instructors_df["airport"].map(extract_airport_code)
        instructors_df["airport"] = instructors_df["airport_code"].map(
            lambda airport_code: airports_dict[airport_code][1],
            na_action="ignore") # replace the airport URI with the airport name
        instructors_df["airport_latitude"] = instructors_df["airport_code"].map(
            lambda airport_code: airports_dict[airport_code][2], na_action="ignore")
        instructors_df["airport_longitude"] = instructors_df["airport_code"].map(
            lambda airport_code: airports_dict[airport_code][3], na_action="ignore")

        # Extract year when instructor badges were awarded and add them as new columns
        swc_instructor_badge_awarded = []
        dc_instructor_badge_awarded = []
        lc_instructor_badge_awarded = []
        trainer_badge_awarded = []
        year_earliest_instructor_badge_awarded = []
        for awards_uri in instructors_df["awards"]:
            print("Getting instructor's badges from " + awards_uri)
            response = requests.get(awards_uri, headers=HEADERS, auth=(username, password))
            response.raise_for_status()  # check if the request was successful
            awards = response.json()

            swc_instructor_badge_awarded_date = next(
                (award["awarded"] for award in awards if award["badge"] == "swc-instructor"), None)
            dc_instructor_badge_awarded_date = next(
                (award["awarded"] for award in awards if award["badge"] == "dc-instructor"), None)
            lc_instructor_badge_awarded_date = next(
                (award["awarded"] for award in awards if award["badge"] == "lc-instructor"), None)
            trainer_badge_awarded_date = next((award["awarded"] for award in awards if award["badge"] == "trainer"), None)

            swc_instructor_badge_awarded.append(swc_instructor_badge_awarded_date)
            dc_instructor_badge_awarded.append(dc_instructor_badge_awarded_date)
            lc_instructor_badge_awarded.append(lc_instructor_badge_awarded_date)
            trainer_badge_awarded.append(trainer_badge_awarded_date)

            dates = [swc_instructor_badge_awarded_date, dc_instructor_badge_awarded_date,
                     lc_instructor_badge_awarded_date, trainer_badge_awarded_date]
            dates = filter(None, dates)
            dates = map(lambda date: datetime.datetime.strptime(date, "%Y-%m-%d"), dates)

            year_earliest_instructor_badge_awarded.append(sorted(dates)[0].year if dates != [] else None)

        idx = instructors_df.columns.get_loc("badges")
        instructors_df.insert(loc=idx + 1, column='swc-instructor', value=swc_instructor_badge_awarded)
        instructors_df.insert(loc=idx + 2, column='dc-instructor', value=dc_instructor_badge_awarded)
        instructors_df.insert(loc=idx + 3, column='lc-instructor', value=lc_instructor_badge_awarded)
        instructors_df.insert(loc=idx + 4, column='trainer', value=trainer_badge_awarded)
        instructors_df.insert(loc=idx + 5, column='year_earliest_instructor_badge_awarded', value=year_earliest_instructor_badge_awarded)
        instructors_df.drop(["awards"], axis=1, inplace=True) # We do not need this column any more

        return instructors_df

    except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as ex:
        # Catastrophic error occurred or HTTP request was not successful for
        # some reason (e.g. status code 4XX or 5XX was returned)
        print("Ooops - something went wrong when getting instructors data from AMY...")
        print(ex.format_exc())
        sys.exit(1)


def get_airports(url_parameters=None, username=None, password=None):
    """
    Gets airport info (for a country) from AMY
    :param url_parameters: URL parameter dictionary to use when querying AMY (e.g. airports per country)
    :param username: username used to access AMY's API
    :param password: password used to access AMY's API
    :return:
    """

    try:
        response = requests.get(AMY_AIRPORTS_API_URL, headers=HEADERS, auth=(username, password),
                                params=url_parameters)
        response.raise_for_status()  # check if a request was successful
        airports = []
        next_url = response.json()["next"]
        airports = response.json()["results"]  # a list extracted from JSON response
        while next_url is not None:
            response = requests.get(next_url, headers=HEADERS, auth=(username, password))
            response.raise_for_status()  # check if a request was successful
            next_url = response.json()["next"]
            airports.extend(response.json()["results"])

        # We can translate a list of JSON objects/dictionaries directly into a DataFrame
        airports_df = pandas.DataFrame(airports)

        # Save them to file in the case they are not available online on-demand for some reason.
        # Overwrite the old airports with more up-to-date data.
        airports_df.to_csv(AIRPORTS_FILE, encoding="utf-8", index=False)

    except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as ex:
        # Catastrophic error occured or HTTP request was not successful for
        # some reason (e.g. status code 4XX or 5XX was returned)
        print("Ooops - something went wrong when getting airport data from AMY...")
        print(ex.format_exc())
        print("Loading airports data from a local file " + AIRPORTS_FILE + "...")
        # Load data from the saved airports file
        airports_df = pandas.read_csv(AIRPORTS_FILE, encoding="utf-8")

    # Filter airports by country - this should be done via URL parameters in the call to the AMY API
    # but it is not implemented in the API yet so we filter them out here
    if url_parameters is not None and url_parameters["country"] is not None and url_parameters[
        "country"].lower != "all":
        airports_df = airports_df.loc[airports_df["country"] == url_parameters["country"]]
    return airports_df


def extract_airport_code(uri):
    """
    Extract the 3-letter IATA airport code from the URI (e.g. the last 3 letters from 'https://amy.carpentries.org/api/v1/airports/MAN/')
    :param uri: Airport URI string
    :return: 3-letter airport code extracted from the str
    """
    if uri is not None:
        i = uri.rfind("/")
        if i != -1:
            return uri[i - 3: i]
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
                amy_credentials_yaml = yaml.load(stream, Loader=yaml.FullLoader)
            except yaml.YAMLError as exc:
                print("An error occurred while reading AMY credentials YAML file ...")
                print(traceback.format_exc())

        username = amy_credentials_yaml["amy_credentials"]["username"]
        password = amy_credentials_yaml["amy_credentials"]["password"]
    else:
        print("AMY credentials YAML file does not exist " + file_path)
    return username, password


def extract_workshop_instructors(workshop_tasks_url, username, password):
    instructors_urls = []
    instructors = []
    try:
        # Get the tasks, then extract all person URLs who were "instructors"
        response = requests.get(workshop_tasks_url, auth=(username, password))
        response.raise_for_status()  # check if a request was successful
        print("Getting workshop instructors from " + workshop_tasks_url)
        tasks = response.json()["results"]
        instructors_urls = [task['person'] for task in tasks if task['role'] == 'instructor']

        # Follow each of the instructors' URLs and extract their names
        for instructors_url in instructors_urls:
            response = requests.get(instructors_url, auth=(username, password))
            response.raise_for_status()  # check if a request was successful
            instructor = response.json()
            instructor_name = instructor["personal"] + " " + instructor["middle"] + " " + instructor["family"]
            instructors.append(re.sub(" +", " ", instructor_name))
    except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as ex:
        # Catastrophic error occured or HTTP request was not successful
        # for some reason (e.g. status code 4XX or 5XX was returned)
        print("Ooops - something went wrong when getting instructors that taught at a workshop from AMY...")
        # Ignore - we still have workshop data to look at, just log this error
        print(ex.format_exc())
    return instructors


if __name__ == '__main__':
    main()
