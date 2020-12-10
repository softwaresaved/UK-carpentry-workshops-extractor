import pandas as pd
import numpy as np
import os
import argparse
import json
import datetime
import re
import folium
from folium.plugins import MarkerCluster
from folium.plugins import HeatMap
from shapely.geometry import shape, Point
import traceback
import getpass
import tldextract

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

UK_REGIONS_FILE = CURRENT_DIR + '/UK-regions.json'
UK_AIRPORTS_REGIONS_FILE = CURRENT_DIR + '/UK-airports_regions.csv'  # Extracted on 2017-10-16 from https://en.wikipedia.org/wiki/List_of_airports_in_the_United_Kingdom_and_the_British_Crown_Dependencies

NORMALISED_INSTITUTIONS_DICT_JSON = CURRENT_DIR + '/venue-normalised_institutions-dictionary.json'
NORMALISED_INSTITUTIONS_DICT = json.load(open(NORMALISED_INSTITUTIONS_DICT_JSON))

UK_ACADEMIC_INSTITUTIONS_CSV = CURRENT_DIR + '/UK-academic-institutions.csv'  # Extracted on 2017-10-27 from http://learning-provider.data.ac.uk/
HESA_ACADEMIC_PROVIDERS_CSV = CURRENT_DIR + "/HESA_UK_higher_education_providers.csv"

UK_NON_ACADEMIC_INSTITUTIONS_CSV = CURRENT_DIR + '/UK-non-academic-institutions.csv'
ALL_UK_INSTITUTIONS_CSV = CURRENT_DIR + '/all-institutions.csv' # merged academic and non-academic institutions
ALL_UK_INSTITUTIONS_DF = pd.read_csv(ALL_UK_INSTITUTIONS_CSV, encoding="utf-8")

# UK_AIRPORTS_REGIONS_DF = pd.read_csv(UK_AIRPORTS_REGIONS_FILE, encoding="utf-8")
UK_REGIONS = json.load(open(UK_REGIONS_FILE), encoding="utf-8")
UK_AIRPORTS = pd.read_csv(UK_AIRPORTS_REGIONS_FILE, encoding="utf-8")

WORKSHOP_TYPE = ["SWC", "DC", "LC", "TTT"]
WORKSHOP_SUBTYPE = ['Pilot', "Circuits"]
STOPPED_WORKSHOP_STATUS = ['stalled', 'cancelled', 'unresponsive']
INSTRUCTOR_BADGES = ["swc-instructor", "dc-instructor", "lc-instructor", "trainer"]

COUNTRIES_FILE = CURRENT_DIR + "/countries.json"


def get_countries(countries_file):
    countries = None
    if os.path.isfile(countries_file):
        with open(countries_file, 'r') as stream:
            try:
                countries = json.load(stream)
            except Exception as exc:
                print("An error occurred while reading countries JSON file " + countries_file)
                print(traceback.format_exc())
    else:
        print("Countries JSON file does not exist " + countries_file)
    return countries


COUNTRIES = get_countries(COUNTRIES_FILE)


def get_uk_non_academic_institutions_from_csv():
    """
    Return names and coordinates for UK institutions that are not high education providers
    (so are not in the official academic institutions list), but appear in data as host institutions or
     affiliations of UK instructors.
    This list needs to be periodically updated as more non-academic affiliations appear Carpentries' records.
    """
    uk_academic_institutions_geodata_df = pd.read_csv(UK_NON_ACADEMIC_INSTITUTIONS_CSV, encoding="utf-8")
    return pd.DataFrame(uk_academic_institutions_geodata_df)


def get_uk_academic_institutions():
    uk_academic_institutions_df = pd.read_csv(UK_ACADEMIC_INSTITUTIONS_CSV, encoding="utf-8",
                                              usecols=['VIEW_NAME', 'LONGITUDE', 'LATITUDE'])
    return uk_academic_institutions_df


# UK_ACADEMIC_INSTITUTIONS_DF = get_uk_academic_institutions()
# ALL_UK_INSTITUTIONS_DF2 = UK_ACADEMIC_INSTITUTIONS_DF.append(get_uk_non_academic_institutions())


def parse_command_line_parameters_amy():
    parser = argparse.ArgumentParser()
    # parser.add_argument("-c", "--country_code", type=str,
    #                     help="ISO-3166-1 two-letter country_code code or leave blank for all countries")
    parser.add_argument("-u", "--username", type=str, help="Username to login to AMY")
    parser.add_argument("-p", "--password", type=str, nargs='?', default=argparse.SUPPRESS,
                        help="Password to log in to AMY - you will be prompted for it (please do not enter your "
                             "password on the command line even though it is possible)")
    parser.add_argument("-rw", "--raw_workshops_file", type=str, default=None,
                        help="File path where raw workshop data extracted from AMY will be saved in CSV format. "
                             "If omitted, data will be saved to data/raw/ directory and named with the current date.")

    parser.add_argument("-pw", "--processed_workshops_file", type=str, default=None,
                        help="File path where processed workshop data will be saved in CSV format. "
                             "If omitted, data will be saved to data/processed/ directory and named with the current date.")

    parser.add_argument("-ri", "--raw_instructors_file", type=str, default=None,
                        help="File path where raw instructors data extracted from AMY will be saved in CSV format. "
                             "If omitted, data will be saved to data/raw/ directory and named with the current date.")

    parser.add_argument("-pi", "--processed_instructors_file", type=str, default=None,
                        help="File path where processed instructors data will be saved in CSV format. "
                             "If omitted, data will be saved to data/processed/ directory and named with the current date.")
    args = parser.parse_args()
    if hasattr(args, "password"):  # if the -p switch was set - ask user for a password but do not echo it
        if args.password is None:
            args.password = getpass.getpass(prompt='Enter AMY password: ')
    else:
        setattr(args, 'password',
                None)  # the -p switch was not used - add the password argument 'manually' but set it to None
    return args


def parse_command_line_parameters_redash():
    parser = argparse.ArgumentParser()

    parser.add_argument("-rw", "--raw_workshops_file", type=str, default=None,
                        help="File path where raw workshop data extracted from REDASH will be saved in CSV format. "
                             "If omitted, data will be saved to data/raw/ directory and named with the current date.")

    parser.add_argument("-pw", "--processed_workshops_file", type=str, default=None,
                        help="File path where processed workshop data will be saved in CSV format. "
                             "If omitted, data will be saved to data/processed/ directory and named with the current date.")

    parser.add_argument("-ri", "--raw_instructors_file", type=str, default=None,
                        help="File path where raw instructors data extracted from REDASH will be saved in CSV format. "
                             "If omitted, data will be saved to data/raw/ directory and named with the current date.")

    parser.add_argument("-pi", "--processed_instructors_file", type=str, default=None,
                        help="File path where processed instructors data will be saved in CSV format. "
                             "If omitted, data will be saved to data/processed/ directory and named with the current date.")

    args = parser.parse_args()
    return args


def parse_command_line_parameters_analyses():
    parser = argparse.ArgumentParser()
    required_args = parser.add_argument_group('required named arguments')
    required_args.add_argument("-in", "--input_file", type=str, default=None, required=True,
                               help="The path to the input data CSV file to analyse.")
    parser.add_argument("-out", "--output_file", type=str, default=None,
                        help="File path where data analyses will be saved in xslx Excel format. "
                             "If omitted, the Excel file will be saved to "
                             "data/analyses/ directory and will be named as 'analysed_<INPUT_FILE_NAME>'.")
    args = parser.parse_args()
    return args


def parse_command_line_parameters_maps():
    parser = argparse.ArgumentParser()
    required_args = parser.add_argument_group('required named arguments')
    required_args.add_argument("-in", "--input_file", type=str, default=None, required=True,
                               help="The path to the input data CSV file to map.")
    args = parser.parse_args()
    return args


def extract_workshop_type(workshop_tags):
    """
    Extract workshop type from a list of workshop tags. Tags contain a mix of workshop status and workshop types.
    :param workshop_tags: list of tags
    :return: workshop type (e.g. "SWC", "DC", "LC" or "TTT", or "" if none of the recognised tags is found)
    """

    # If we have the list passed as a string instead - convert to a list first
    if isinstance(workshop_tags, str):
        workshop_tags = workshop_tags.split(",")

    tags = list(set(workshop_tags) & set(WORKSHOP_TYPE))  # intersection of 2 sets
    if len(tags) > 0:  # non-empty list?
        return tags[0]
    else:
        return ""


def extract_workshop_subtype(workshop_tags):
    """
    Extract workshop subtype from a list of workshop tags. Tags contain a mix of workshop status and workshop types.
    :param workshop_tags: list of tags
    :return: workshop type (e.g. "Circuits", "Pilot", or "" if none of the recognised tags is found)
    """

    # If we have the list passed as a string instead - convert to a list first
    if isinstance(workshop_tags, str):
        workshop_tags = workshop_tags.split(",")

    tags = list(set(workshop_tags) & set(WORKSHOP_SUBTYPE))  # intersection of 2 sets
    if len(tags) > 0:  # non-empty list?
        return tags[0]
    else:
        return ""


def extract_workshop_status(workshop_tags):
    """
    Extract workshop status from a list of workshop tags. Tags contain a mix of workshop status and workshop type.
    :param workshop_tags: list of tags
    :return: workshop status (e.g. one of 'stalled', 'cancelled', 'unresponsive' or "" if none of the recognised tags
    is found)
    """

    # If we have the list passed as a string instead - convert to a list first
    if isinstance(workshop_tags, str):
        workshop_tags = workshop_tags.split(",")

    # Is this a stopped workshop?
    is_stopped = list(set(workshop_tags) & set(STOPPED_WORKSHOP_STATUS))
    if len(is_stopped) > 0:  # non-empty list?
        return is_stopped[0]  # return the first STOPPED_WORKSHOP_STATUS tag found
    else:
        return ""


def is_stopped(workshop_tags):
    """
    :param workshop_tags: list of tags
    :return: True if workshop_tags contain one of the STOPPED_WORKSHOP_STATUS tags, else False
    """

    # Is this a stopped workshop?
    stopped_tags = list(set(workshop_tags) & set(STOPPED_WORKSHOP_STATUS))
    if len(stopped_tags) > 0:  # non-empty list?
        return True
    else:
        return False


def get_country(country_code):
    """
    :param country_code: 2-letter ISO Alpha 2 country code, e.g. 'GB' for United Kingdom
    :return: country's common name
    """
    # print("country_code: " + country_code)
    return next((country["name"]["common"] for country in COUNTRIES if country["cca2"] == country_code), None)


def process_workshops(workshops_df):
    """
    :param workshops_df: dataframe with raw workshop data to be processed a bit for further analyses and mapping
    :return: dataframe with processed workshop data
    """

    # Extract workshop year from its slug and add as a new column
    idx = workshops_df.columns.get_loc("start")
    workshops_df.insert(loc=idx, column='year', value=workshops_df["start"])
    workshops_df["year"] = workshops_df["start"].map(lambda date: datetime.datetime.strptime(date, "%Y-%m-%d").year,
                                                     na_action="ignore")

    # Extract workshop type ('SWC', 'DC', 'LC', 'TTT'), subtype ('Circuits', 'Pilot'),
    # and status ('cancelled', 'unresponsive', 'stalled') from the list of workshop tags and add as new columns
    idx = workshops_df.columns.get_loc("tags")
    workshops_df.insert(loc=idx, column='workshop_type',
                        value=workshops_df["tags"])
    workshops_df["workshop_type"] = workshops_df["tags"].map(extract_workshop_type, na_action="ignore")

    workshops_df.insert(loc=idx + 1, column='workshop_subtype', value=workshops_df["tags"])
    workshops_df["workshop_subtype"] = workshops_df["tags"].map(extract_workshop_subtype, na_action="ignore")

    workshops_df.insert(loc=idx + 2, column='workshop_status', value=workshops_df["tags"])
    workshops_df["workshop_status"] = workshops_df["tags"].map(extract_workshop_status, na_action="ignore")

    # Drop all stopped workshops
    stopped_workshops = workshops_df[(workshops_df['workshop_status'].isin(STOPPED_WORKSHOP_STATUS))]
    workshops_df.drop(stopped_workshops.index, inplace=True)

    # Insert countries where workshops were held based on country_code
    idx = workshops_df.columns.get_loc("country_code")
    workshops_df.insert(loc=idx, column='country', value=workshops_df["country_code"])
    countries = pd.read_csv("lib/country_codes.csv", encoding="utf-8",
                            keep_default_na=False)  # keep_default_na prevents Namibia "NA" being read as NaN!
    countries_mapping = dict(countries[['country_code', 'country_name']].values)
    workshops_df['country'] = workshops_df['country_code'].map(countries_mapping, na_action="ignore")

    # Extract hosts' top level Web domains from host URIs or host web domains, depending which column we have
    if "organiser_web_domain" in workshops_df.columns:
        idx = workshops_df.columns.get_loc("organiser_web_domain") + 1
        workshops_df.insert(loc=idx, column='organiser_top_level_web_domain',
                            value=workshops_df["organiser_web_domain"])
        workshops_df["organiser_top_level_web_domain"] = workshops_df["organiser_web_domain"].apply(
            lambda x: tldextract.extract(x).domain + '.' + tldextract.extract(x).suffix)
    elif "organiser_uri" in workshops_df.columns:
        # Extract hosts' web domains from host URIs
        idx = workshops_df.columns.get_loc("organiser_uri") + 1
        workshops_df.insert(loc=idx, column='organiser_top_level_web_domain', value=workshops_df["organiser_uri"])
        workshops_df["organiser_top_level_web_domain"] = workshops_df["organiser_uri"].map(
            lambda uri: extract_top_level_domain_from_uri(uri),
            na_action="ignore")  # extract host's top-level domain from URIs like 'https://amy.carpentries.org/api/v1/organizations/earlham.ac.uk/'

    # Get data for UK institutions to lookup
    all_institutions_regions_dict = dict(ALL_UK_INSTITUTIONS_DF[['top_level_web_domain', 'region']].values)  # create a dict for lookup

    # Get regions for workshops
    # First try by workshop (latitude, longitude) as workshop (host) location may not match organiser location
    print("Getting regions for host institutions based on polygon data...")
    idx = workshops_df.columns.get_loc("country") + 1
    workshops_df.insert(loc=idx, column='region', value=np.nan)
    workshops_df['region'] = workshops_df.apply(
        lambda x: get_uk_region(latitude=x['latitude'], longitude=x['longitude'], institution=x['organiser'])
        if (pd.notna(x['longitude']) and x['longitude'] not in [0,-1])
        else np.nan, axis=1
    )
    # For all rows where region is null, map by organiser_top_level_web_domain to find region
    print("Getting regions for host institutions based on organiser_top_level_web_domain...")
    regions_from_institution = workshops_df[workshops_df['region'].isna()]['organiser_top_level_web_domain'].map(all_institutions_regions_dict)
    workshops_df['region'].update(regions_from_institution) # update regions in place (indexes will match)
    print("Workshops with no region: ")
    print(workshops_df[workshops_df['region'].isna()]['organiser'])

    # Get normalised (official) and common names for UK academic institutions, if exist
    uk_academic_institutions_normalised_names_dict = dict(
        ALL_UK_INSTITUTIONS_DF[['top_level_web_domain', 'normalised_name']].values)  # create a dict for lookup
    uk_academic_institutions_common_names_mapping = dict(
        ALL_UK_INSTITUTIONS_DF[['top_level_web_domain', 'common_name']].values)  # create a dict for lookup

    # Insert normalised (official) name for organiser
    idx = workshops_df.columns.get_loc("organiser_top_level_web_domain") + 1
    workshops_df.insert(loc=idx, column='organiser_normalised_name',
                        value=workshops_df["organiser_top_level_web_domain"])
    workshops_df['organiser_normalised_name'] = workshops_df['organiser_normalised_name'].map(
        uk_academic_institutions_normalised_names_dict, na_action="ignore")

    # Insert common name for organiser
    workshops_df.insert(loc=idx + 1, column='organiser_common_name',
                        value=workshops_df["organiser_top_level_web_domain"])
    workshops_df['organiser_common_name'] = workshops_df['organiser_common_name'].map(
        uk_academic_institutions_common_names_mapping, na_action="ignore")

    return workshops_df


def process_instructors(instructors_df):
    """
    :param instructors_df: dataframe with raw instructor data to be processed a bit for further analyses and mapping
    :return: dataframe with processed instructor data
    """

    idx = instructors_df.columns.get_loc("country_code")
    instructors_df.insert(loc=idx, column='country',
                          value=instructors_df["country_code"])
    instructors_df["country"] = instructors_df["country"].map(lambda country_code: get_country(country_code),
                                                              na_action="ignore")

    # Insert normalised/official names for UK academic institutions
    print("\nInserting normalised name for instructors' affiliations/institutions...\n")
    instructors_df = insert_normalised_institution(instructors_df, "institution")
    print("Instructors with no normalised institutional name: ")
    print(instructors_df[instructors_df['normalised_institution'].isna()][['institution', 'normalised_institution']])

    # Insert latitude, longitude pairs for instructors' institutions
    print("\nInserting geocoordinates for instructors' affiliations/institutions...\n")
    instructors_df = insert_institutional_geocoordinates(instructors_df, "normalised_institution", "latitude",
                                                         "longitude")

    # Get regions for instructors' institutions
    # First try to lookup by institutions' normalised name, if we have it
    print("Getting regions for instructors' institutions based on normalised names...")
    instructors_df = insert_institutional_region(instructors_df)
    # If we do not have institution normalised name to get the region, see if we have the nearest airport
    # info and try to get the region like that
    print("Instructors with no region based on institutional data: ")
    print(instructors_df[instructors_df['region'].isna()]['institution'])
    print("Inserting regions for instructors based on the nearest airport...")
    # For all rows where region is null, map by airport_code to find region
    uk_airports_dict = dict(UK_AIRPORTS[["airport_code", "region"]].values)
    regions_from_airport = instructors_df[instructors_df['region'].isna()]['airport_code'].map(
        uk_airports_dict)
    instructors_df['region'].update(regions_from_airport)  # update regions in place (indexes will match)
    print("Instructors with no region: ")
    print(instructors_df[instructors_df['region'].isna()]['institution'])

    # Extract dates when instructors badges were awarded from list
    if "badges_dates" in instructors_df.columns:
        idx = instructors_df.columns.get_loc("badges_dates")
        i = 1
        for badge in INSTRUCTOR_BADGES:
            instructors_df.insert(loc=idx + i, column=badge, value=instructors_df["badges"])
            instructors_df[badge] = pd.to_datetime(
                instructors_df.apply(lambda x: get_badge_date(badge=badge, badges=x['badges'], dates=x['badges_dates']),
                                     axis=1))
            i = i + 1

        instructors_df.insert(loc=idx + i, column='earliest_badge_awarded',
                              value=instructors_df[INSTRUCTOR_BADGES].min(axis=1))
        instructors_df["earliest_badge_awarded"] = pd.to_datetime(instructors_df["earliest_badge_awarded"])
        instructors_df.insert(loc=idx + i + 1, column='year_earliest_badge_awarded',
                              value=instructors_df["earliest_badge_awarded"].dt.year.fillna(0.0).astype(int))

    # # Create a dictionary of taught_workshops (a list of workshop slugs where instructor taught) and
    # # taught_workshop_dates (a list of corresponding dates for those workshops) and save into a new column
    # idx = instructors_df.columns.get_loc("taught_workshops")
    # instructors_df.insert(loc=idx, column='workshops', value=instructors_df["taught_workshops"])
    # instructors_df['workshops'] = instructors_df.apply(lambda x: create_dict(x['taught_workshops'], x['taught_workshop_dates']), axis=1)

    # Create a dictionary of {year: number_taught_workshops_per_year} per instructor and save into a new column
    idx = instructors_df.columns.get_loc("taught_workshops")
    instructors_df.insert(loc=idx + 2, column='taught_workshops_per_year', value=instructors_df["taught_workshops"])
    instructors_df['taught_workshops_per_year'] = instructors_df['taught_workshop_dates'].apply(
        lambda x: workshops_per_year_dict(x))

    # For some reason Redash returns some people who are not instructors that have empty 'earliest_badge_awarded' field!
    # This has been fixed in the query that gets the raw data from Redash!
    # instructors_df = instructors_df.dropna(subset=['earliest_badge_awarded'])

    return instructors_df


def workshops_per_year_dict(taught_workshop_dates):
    """
    Counts number of workshops taught for each year the person was actively teaching.
    :param taught_workshops:
    :param taught_workshop_dates:
    :return: a dictionary like {year : number_taught_workshops_per_year}
    """
    # Create a list of years for a list of dates (passed as one long string)
    if taught_workshop_dates == "" or taught_workshop_dates is None or taught_workshop_dates is np.nan:
        return None

    taught_workshop_years = []
    for date in str(taught_workshop_dates).split(','):
        try:
            d = datetime.datetime.strptime(date, '%Y-%m-%d').date().year
        except ValueError:
            # Try the US date format with date before month - some slugs wrongly use this
            d = datetime.datetime.strptime(date, '%Y-%d-%m').date().year
        except Exception as exc:  # anything else
            print("An error occurred while parsing date from slug: " + date)
            print(traceback.format_exc())
            continue
        taught_workshop_years.append(d)

    counts = dict()
    for i in taught_workshop_years:
        counts[i] = counts.get(i, 0) + 1
    return counts


def earliest_date(dates_string):
    """
    :param dates_string: sting representing a list of dates
    :return:
    """
    if dates_string is None or dates_string is np.nan:
        return None
    dates_string_list = str(dates_string).split(',')
    # Convert to a list of dates
    dates_list = [datetime.datetime.strptime(date, '%Y-%m-%d').date() for date in dates_string_list]
    return min(dates_list)


def latest_date(dates_string):
    """
    :param dates_string: sting representing a list of dates
    :return:
    """
    if dates_string is None or dates_string is np.nan:
        return None
    dates_string_list = str(dates_string).split(',')
    # Convert to a list of dates
    dates_list = [datetime.datetime.strptime(date, '%Y-%m-%d').date() for date in dates_string_list]
    return max(dates_list)


def create_dict(list_a, list_b):
    if list_a is None or list_a is np.nan:
        return None
    d = dict(zip(str(list_a).split(','), str(list_b).split(',')))
    return json.dumps(d)


def get_badge_date(badge, badges, dates):
    """
    For a given badge name, return the date it was awarded.
    :param badge: Instructor badge name.
    :param badges: List of all badges awarded.
    :param dates: List of dates the badges were awarded, order of dates corresponds to the order of badges in badges list.
    :return: For a given badge name, return the date it was awarded or None is no such badge was awarded.
    """
    if badges is None or badges == [] or dates is None or dates == []:
        return None

    # Find index of badge in badges list
    try:
        index = badges.index(badge)
        return dates[index]
    except ValueError:
        return None


def create_readme_tab(writer, readme_text):
    """
    Create the README tab in the spreadsheet.
    """
    workbook = writer.book
    worksheet = workbook.add_worksheet('README')
    worksheet.write(0, 0, readme_text)


def create_excel_analyses_spreadsheet(file, df, sheet_name):
    """
    Create an Excel spreadsheet to save the dataframe and various analyses and graphs.
    """
    writer = pd.ExcelWriter(file, engine='xlsxwriter')
    df.to_excel(writer, sheet_name=sheet_name, index=False)
    return writer


def insert_normalised_institution(df, non_normalised_institution_column):
    """
    Fix names of UK institutions to be the official names, so we can cross reference them with their geocodes later on.
    Use column 'institution' and create new column 'normalised_institution' based off it. For institutions that we do
    not have normalised names, just keep it as is.
    """

    # Get the index of column 'venue'/'institution/affiliation' (with non-normalised workshop venue or instructor's
    # institution/affiliation), right to which we want to insert the new column containing normalised institution name
    idx = df.columns.get_loc(non_normalised_institution_column)
    df.insert(
        loc=idx + 1, column='normalised_institution',
        value=df[non_normalised_institution_column]
    )  # insert to the right of the column 'venue'/'institution/affiliation'
    df["normalised_institution"] = df["normalised_institution"].map(
        get_normalised_institution_name, na_action="ignore"
    )
    return df


def get_normalised_institution_name(non_normalised_institution_name):

    # First look up in normalised names dictionary (for non-academic institutions and odd spellings of
    # academic institutions or sub-departments that need to be mapped to the top-level institution)
    normalised_institution_name = NORMALISED_INSTITUTIONS_DICT.get(
        non_normalised_institution_name,
        non_normalised_institution_name
    )  # default to the original name if not found
    return normalised_institution_name.upper()


def insert_institutional_geocoordinates(df, institution_column_name, latitude_column_name, longitude_column_name):
    # Insert latitude and longitude for institutions, by looking up the ALL_UK_INSTITUTIONS_DF
    idx = df.columns.get_loc(institution_column_name)  # index of column where (normalised) institution is kept
    df.insert(loc=idx + 1,
              column=latitude_column_name,
              value=None)
    df.insert(loc=idx + 2,
              column=longitude_column_name,
              value=None)
    # replace with the institution's latitude and longitude coordinates
    df[latitude_column_name] = df[institution_column_name].str.upper().map(
        ALL_UK_INSTITUTIONS_DF.set_index("normalised_name")['latitude'])
    df[longitude_column_name] = df[institution_column_name].str.upper().map(
        ALL_UK_INSTITUTIONS_DF.set_index("normalised_name")['longitude'])
    return df


def insert_institutional_region(df):
    # Insert region info
    idx = df.columns.get_loc('country_code')  # index of column where country_code is kept
    df.insert(loc=idx + 1,
              column='region',
              value=np.nan)
    df["region"] = df["normalised_institution"].str.upper().map(
        ALL_UK_INSTITUTIONS_DF.set_index("normalised_name")['region'])
    return df


def get_uk_region(latitude, longitude, institution):
    """
    Lookup UK region given the (latitude, longitude) coordinates.
    """
    if ~pd.isna(latitude) and ~pd.isna(longitude):
        # print("Looking up region for geocoordinates: (" + str(latitude) + ", " + str(
        #     longitude) + ") for institution: '" + str(institution) + "'")
        point = Point(longitude, latitude)
        for feature in UK_REGIONS['features']:
            polygon = shape(feature['geometry'])
            if polygon.contains(point):
                return(feature['properties']['NAME'])
    print("Could not find UK region for " + str(institution) + " (" + str(latitude) + ", " + str(longitude) +
          ") from polygon data")
    return np.nan


def extract_top_level_domain_from_string(domain):
    """
    Extract host's top level domain from strings like 'cmist.manchester.ac.uk' to 'manchester.ac.uk'.
    top level domain 'manchester.ac.uk'.
    :param domain
    :return:
    """
    domain_parts = list(filter(None, re.split("(.+?)\.", domain)))
    if len(domain_parts) >= 3:
        domain_parts = domain_parts[-3:]  # Get the last 3 elements of the list only
    top_level_domain = ''.join((x + '.') for x in domain_parts)  # join parts with '.' in between
    top_level_domain = top_level_domain[:-1]  # remove the extra '.' at the end after joining
    return top_level_domain


def extract_top_level_domain_from_uri(uri):
    """
    Extract host's top level domain from URIs like 'https://amy.carpentries.org/api/v1/organizations/earlham.ac.uk/' to 'earlham.ac.uk'.
    When subdomains are used, as in 'https://amy.carpentries.org/api/v1/organizations/cmist.manchester.ac.uk/' we are only interested in
    top level domain 'manchester.ac.uk'.
    :param uri: URI like 'https://amy.carpentries.org/api/v1/organizations/earlham.ac.uk/'
    :return: top level domain like 'earlham.ac.uk'
    """
    host = list(filter(None, re.split("(.+?)/", uri)))[-1]  # Get the host from the URI first
    # Now just get the top level domain of the host
    domain_parts = list(filter(None, re.split("(.+?)\.", host)))
    if len(domain_parts) >= 3:
        domain_parts = domain_parts[-3:]  # Get the past 3 elements of the list only
    top_level_domain = ''.join((x + '.') for x in domain_parts)  # join parts with '.' in between
    top_level_domain = top_level_domain[:-1]  # remove the extra '.' at the end after joining
    return top_level_domain


def merge_institution_data():
    hesa_uk_higher_education_providers = pd.read_csv(HESA_ACADEMIC_PROVIDERS_CSV, encoding="utf-8")
    hesa_uk_higher_education_providers_region_mapping = dict(
        hesa_uk_higher_education_providers[['UKPRN', 'Region']].values)  # create a dict for lookup

    uk_academic_institutions = pd.read_csv(UK_ACADEMIC_INSTITUTIONS_CSV,
                                           encoding="utf-8",
                                           usecols=['UKPRN','PROVIDER_NAME','VIEW_NAME','WEBSITE_URL',
                                                    'LONGITUDE','LATITUDE', 'STREET_NAME','TOWN','POSTCODE'])
    uk_academic_institutions['top_level_web_domain'] = uk_academic_institutions['WEBSITE_URL'].apply(
        lambda x: tldextract.extract(x).domain + '.' + tldextract.extract(x).suffix)
    # Join region info for academic provider from HESA data
    uk_academic_institutions['region'] = uk_academic_institutions['UKPRN'].map(
        hesa_uk_higher_education_providers_region_mapping, na_action="ignore")
    uk_academic_institutions.rename(
        columns={'PROVIDER_NAME': 'normalised_name', 'VIEW_NAME': 'common_name', 'LONGITUDE': 'longitude',
                 'LATITUDE': 'latitude'}, inplace=True)

    # Get non-academic institutions' data
    uk_non_academic_institutions = get_uk_non_academic_institutions_from_csv()  # data frame

    all_uk_institutions_data = pd.concat([uk_academic_institutions, uk_non_academic_institutions], ignore_index=True)
    all_uk_institutions_data['normalised_name'] = all_uk_institutions_data['normalised_name'].str.upper()
    all_uk_institutions_file = ALL_UK_INSTITUTIONS_CSV
    all_uk_institutions_data.to_csv(all_uk_institutions_file, encoding="utf-8")
    print("Merged academic and non-academic institutional data saved to " + all_uk_institutions_file)
    return all_uk_institutions_data


def get_center(df):
    # Extract longitude and latitude columns from the dataframe
    coords = df[['latitude', 'longitude']]
    tuples = [tuple(coords) for coords in coords.values]
    x, y = zip(*tuples)

    # Find center
    center = [(max(x) + min(x)) / 2., (max(y) + min(y)) / 2.]

    return center


def add_uk_regions_layer(map):
    # Load UK region information from a json file
    try:
        regions = json.load(open(UK_REGIONS_FILE, encoding='utf-8'))

        # Add to a layer
        folium.GeoJson(regions,
                       name='regions',
                       style_function=lambda feature: {
                           # 'fillColor': '#99ffcc',
                           'color': '#b7b7b7'
                       }).add_to(map)
        folium.LayerControl().add_to(map)
    except:
        print("An error occurred while reading the UK regions file: " + UK_REGIONS_FILE)
        print(traceback.format_exc())

    return map


def generate_heatmap(df):
    df.dropna(subset=["latitude", "longitude"], how="any", axis=0, inplace=True)
    center = get_center(df)

    heatmap = folium.Map(
        location=center,
        zoom_start=6,
        tiles='cartodbpositron')  # for a lighter map tiles='Mapbox Bright'

    lat_long = []
    for index, row in df.iterrows():
        lat_long.append([row['latitude'], row['longitude']])
    HeatMap(lat_long).add_to(heatmap)

    return heatmap


def generate_map_with_circular_markers(df):
    df.dropna(subset=["latitude", "longitude"], how="any", axis=0, inplace=True)
    center = get_center(df)

    map_with_markers = folium.Map(
        location=center,
        zoom_start=6,
        tiles='cartodbpositron')  # for a lighter map tiles='Mapbox Bright'

    for index, row in df.iterrows():
        print(str(index) + ": " + str(row['popup']))

        # iframe = branca.element.IFrame(html=row['description'], width=300, height=200)
        # popup = folium.Popup(iframe, max_width=500)

        popup = folium.Popup(str(row['popup']), parse_html=True)
        folium.CircleMarker(
            radius=3,
            location=[row['latitude'], row['longitude']],
            popup=popup,
            color='#ff6600',
            fill=True,
            fill_color='#ff6600').add_to(map_with_markers)

    return map_with_markers


def generate_map_with_clustered_markers(df):
    """
    Generates a map with clustered markers of a number of locations given in a dataframe.
    """
    df.dropna(subset=["latitude", "longitude"], how="any", axis=0, inplace=True)
    center = get_center(df)

    cluster_map = folium.Map(location=center, zoom_start=6,
                             tiles='cartodbpositron')  # for a lighter map tiles='Mapbox Bright'

    marker_cluster = MarkerCluster(name='workshops').add_to(cluster_map)

    for index, row in df.iterrows():
        popup = folium.Popup(str(row['popup']), parse_html=True)
        folium.CircleMarker(radius=5, location=[row['latitude'], row['longitude']], popup=popup, color='#ff6600',
                            fill=True, fill_color='#ff6600').add_to(marker_cluster)

    return cluster_map


def generate_choropleth_map(df, regions, entity_type="workshops"):
    """
    Generates a choropleth map of the number of entities (instructors or workshops) that can be found
    in each UK region.
    """
    entities_per_region_df = pd.DataFrame({'count': df.groupby(['region']).size()}).reset_index()

    center = get_center(df)

    # Creates the threshold scale to be visualized in the map.
    scale_list = entities_per_region_df['count'].tolist()
    max_scale = max(scale_list)
    scale = int(max_scale / 5)
    threshold_scale = []
    for each in range(0, max_scale + 1, scale):
        threshold_scale.append(each)

    map = folium.Map(
        location=center,  # [54.00366, -2.547855],
        zoom_start=6,
        tiles='cartodbpositron')  # for a lighter map tiles='Mapbox Bright'

    folium.Choropleth(
        geo_data=regions,
        data=entities_per_region_df,
        columns=['region', 'count'],
        key_on='feature.properties.NAME',
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Number of ' + entity_type + ' per UK regions',
        threshold_scale=threshold_scale).add_to(map)

    # map.choropleth(
    #     geo_data=regions,
    #     data=entities_per_region_df,
    #     columns=['region', 'count'],
    #     key_on='feature.properties.NAME',
    #     fill_color='YlGn',
    #     fill_opacity=0.7,
    #     line_opacity=0.2,
    #     legend_name='Number of ' + entity_type + ' per UK regions',
    #     threshold_scale=threshold_scale)

    return map

# def generate_gmaps_heatmap(df):
#     gmaps.configure(api_key=config.api_key)
#
#     lat_list = []
#     long_list = []
#     for index, row in df.iterrows():
#         long_list.append(row['longitude'])
#         lat_list.append(row['latitude'])
#
#     locations = zip(lat_list, long_list)
#
#     ## Resize the map to fit the whole screen.
#     map = gmaps.Map(height='100vh', layout={'height': '100vh'})
#
#     map.add_layer(gmaps.heatmap_layer(locations))
#
#     return map

# def generate_gmaps_map_with_circular_markers(df):
#     """
#     Generates a map from the dataframe where bigger dots indicate bigger counts for a location's geocoordinates.
#     """
#     gmaps.configure(api_key=config.api_key)
#
#     ## Calculate the values for the circle scalling in the map.
#     max_value = df['count'].max()
#     min_value = df['count'].min()
#     grouping = (max_value - min_value) / 3
#     second_value = min_value + grouping
#     third_value = second_value + grouping
#
#     ## Create lists that will hold the found values.
#     names_small = []
#     locations_small = []
#
#     names_medium = []
#     locations_medium = []
#
#     names_large = []
#     locations_large = []
#
#     ## Iterate through the dataframe to find the information needed to fill
#     ## the lists.
#     for index, row in df.iterrows():
#         long_coords = df['longitude']
#         lat_coords = df['latitude']
#         if not long_coords.empty and not lat_coords.empty:
#             if row['count'] >= min_value and row['count'] < second_value:
#                 locations_small.append((lat_coords.iloc[index], long_coords.iloc[index]))
#                 names_small.append(row['normalised_institution'] + ': ' + str(row['count']))
#             elif row['count'] >= second_value and row['count'] < third_value:
#                 locations_medium.append((lat_coords.iloc[index], long_coords.iloc[index]))
#                 names_medium.append(row['normalised_institution'] + ': ' + str(row['count']))
#             elif row['count'] >= third_value and row['count'] <= max_value:
#                 locations_large.append((lat_coords.iloc[index], long_coords.iloc[index]))
#                 names_large.append(row['normalised_institution'] + ': ' + str(row['count']))
#         else:
#             print('For institution "' + row[
#                 'affiliation'] + '" we either have not got coordinates or it is not the official name of an UK '
#                                  'academic institution. Skipping it ...\n')
#
#     ## Add the different markers to different layers corresponding to the
#     ## different amounts of instructors per affiliation.
#     symbol_layer_small = gmaps.symbol_layer(locations_small, fill_color="#ff6600", stroke_color="#ff6600",
#                                             scale=3, display_info_box=True, info_box_content=names_small)
#     symbol_layer_medium = gmaps.symbol_layer(locations_medium, fill_color="#ff6600", stroke_color="#ff6600",
#                                              scale=6, display_info_box=True, info_box_content=names_medium)
#     symbol_layer_large = gmaps.symbol_layer(locations_large, fill_color="#ff6600", stroke_color="#ff6600",
#                                             scale=8, display_info_box=True, info_box_content=names_large)
#
#     ## Resize the map to fit the whole screen.
#     map = gmaps.Map(height='100vh', layout={'height': '100vh'})
#
#     ## Add all the layers to the map.
#     map.add_layer(symbol_layer_small)
#     map.add_layer(symbol_layer_medium)
#     map.add_layer(symbol_layer_large)
#
#     return map
