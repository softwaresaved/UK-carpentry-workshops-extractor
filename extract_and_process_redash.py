import traceback
import os
import sys
import re
import datetime
import io
import requests
import pandas as pd
import lib.helper as helper


sys.path.append('/lib')

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = CURRENT_DIR + '/data'
RAW_DATA_DIR = DATA_DIR + '/raw'
PROCESSED_DATA_DIR = DATA_DIR + '/processed'
LIB_DATA_DIR = CURRENT_DIR + '/lib'

REDASH_CREDENTIALS_FILE = CURRENT_DIR + '/redash_login.yml'

if not os.path.exists(RAW_DATA_DIR):
    os.makedirs(RAW_DATA_DIR)

if not os.path.exists(PROCESSED_DATA_DIR):
    os.makedirs(PROCESSED_DATA_DIR)

# Carpentries Redash system
REDASH_API_WORKSHOPS_QUERY_URL = "http://redash.carpentries.org/api/queries/234/results.csv"
REDASH_API_INSTRUCTORS_QUERY_URL = "http://redash.carpentries.org/api/queries/243/results.csv"

REDASH_API_KEY = "gqMCK5SWYXH4B52zUFmVaf15rN3nArKoJlPHkGg8"

UK_AIRPORTS_REGIONS_FILE = CURRENT_DIR + '/lib/UK-airports_regions.csv'
UK_AIRPORTS = pd.read_csv(UK_AIRPORTS_REGIONS_FILE, encoding="utf-8")


def main():
    """
    Main function
    """

    args = helper.parse_command_line_parameters_redash()

    if args.raw_workshops_file:
        raw_workshops_file = args.raw_workshops_file
    else:
        raw_workshops_file = RAW_DATA_DIR + "/redash_raw_carpentry_workshops_UK" + "_" + datetime.datetime.today().strftime('%Y-%m-%d') + ".csv"

    if args.processed_workshops_file:
        processed_workshops_file = args.processed_workshops_file
    else:
        processed_workshops_file = PROCESSED_DATA_DIR + "/redash_processed_carpentry_workshops_UK" + "_" + datetime.datetime.today().strftime('%Y-%m-%d') + ".csv"

    if args.raw_instructors_file:
        raw_instructors_file = args.raw_instructors_file
    else:
        raw_instructors_file = RAW_DATA_DIR + "/redash_raw_carpentry_instructors_UK" + "_" + datetime.datetime.today().strftime('%Y-%m-%d') + ".csv"

    if args.processed_instructors_file:
        processed_instructors_file = args.processed_instructors_file
    else:
        processed_instructors_file = PROCESSED_DATA_DIR + "/redash_processed_carpentry_instructors_UK" + "_" + datetime.datetime.today().strftime(
            '%Y-%m-%d') + ".csv"

    ############################ Extract workshop data from Carpentries redash ########################

    print("\nExtracting workshops from: " + REDASH_API_WORKSHOPS_QUERY_URL)
    # Get workshop data as returned by a predefined query within Carpentries Redash system (cached results are returned
    # from the last time Redash ran the query, currently set to run every day)
    workshops = get_csv_data_redash(REDASH_API_WORKSHOPS_QUERY_URL, REDASH_API_KEY)
    print("\n####### Extracted " + str(workshops.index.size) + " workshops. #######\n")

    # Save raw workshop data
    workshops.to_csv(raw_workshops_file, encoding="utf-8", index=False)
    print("Saved raw Carpentry workshop data to "+ raw_workshops_file + "\n")

    ############################ Process workshop data ########################
    # Process the workshop data a bit to get it ready for further analyses and mapping

    # Convert column "tags" from a string to a list of strings
    idx = workshops.columns.get_loc("tags")
    workshops.insert(loc=idx, column='tags_list', value=workshops["tags"])
    workshops["tags_list"] = workshops["tags"].str.split(',')

    # Extract workshop type ('SWC', 'DC', 'LC', 'TTT'), subtype ('Circuits', 'Pilot'),
    # and status ('cancelled', 'unresponsive', 'stalled') from the list of workshop tags and add as new columns
    idx = workshops.columns.get_loc("tags_list")
    workshops.insert(loc=idx, column='workshop_type',
                        value=workshops["tags_list"])
    workshops["workshop_type"] = workshops["tags_list"].map(helper.extract_workshop_type, na_action="ignore")

    idx = workshops.columns.get_loc("workshop_type") + 1
    workshops.insert(loc=idx, column='workshop_subtype', value=workshops["tags_list"])
    workshops["workshop_subtype"] = workshops["tags_list"].map(helper.extract_workshop_subtype, na_action="ignore")

    idx = workshops.columns.get_loc("workshop_subtype") + 1
    workshops.insert(loc=idx, column='workshop_status', value=workshops["tags_list"])
    workshops["workshop_status"] = workshops["tags_list"].map(helper.extract_workshop_status, na_action="ignore")

    # Insert countries where workshops were held based on country_code
    idx = workshops.columns.get_loc("country_code")
    workshops.insert(loc=idx, column='country', value=workshops["country_code"])
    countries = pd.read_csv("lib/country_codes.csv", encoding="utf-8", keep_default_na=False)  # keep_default_na prevents Namibia "NA" being read as NaN!
    countries_mapping = dict(countries[['country_code', 'country_name']].values)
    workshops['country'] = workshops['country_code'].map(countries_mapping, na_action="ignore")

    # Extract hosts' domains from host URIs
    idx = workshops.columns.get_loc("organiser_web_domain") + 1
    workshops.insert(loc=idx, column='organiser_top_level_web_domain', value=workshops["organiser_web_domain"])
    workshops["organiser_top_level_web_domain"] = workshops["organiser_web_domain"].map(lambda domain: extract_top_level_domain(domain),na_action="ignore")

    # Add UK region for a workshop based on its geocoordinates as a new column
    idx = workshops.columns.get_loc("country") + 1
    workshops.insert(loc=idx, column='region', value=workshops["country_code"])
    workshops['region'] = workshops.apply(lambda x: helper.get_uk_region(latitude=x['latitude'], longitude=x['longitude']), axis=1)
    print("\n###################\nGetting regions took a while but it has finished now.###################\n")

    # Add UK region for a workshop based on its organiser (lookup UK academic institutitons and HESA data) as a new column
    uk_academic_institutions = pd.read_csv(LIB_DATA_DIR + "/UK-academic-institutions.csv", encoding="utf-8")
    hesa_UK_higher_education_providers = pd.read_csv(LIB_DATA_DIR + "/HESA_UK_higher_education_providers.csv", encoding="utf-8")
    hesa_UK_higher_education_providers_region_mapping = dict(hesa_UK_higher_education_providers[['UKPRN', 'Region']].values)  # create a dict for lookup
    uk_academic_institutions['top_level_web_domain'] = uk_academic_institutions['WEBSITE_URL'].apply(lambda x: x.strip("http://www.").strip("/"))  # strip 'http://www' from domain
    uk_academic_institutions['region'] = uk_academic_institutions['UKPRN'].map(hesa_UK_higher_education_providers_region_mapping, na_action="ignore")
    uk_academic_institutions_region_mapping = dict(uk_academic_institutions[['top_level_web_domain', 'region']].values)  # create a dict for lookup

    idx = workshops.columns.get_loc("organiser_country_code") + 1
    workshops.insert(loc=idx, column='organiser_region', value=workshops["organiser_top_level_web_domain"])
    workshops['organiser_region'] = workshops['organiser_region'].map(uk_academic_institutions_region_mapping, na_action="ignore")

    # Get normalised and common names for UK academic institutions, if exist, by mapping to UK higher education providers
    uk_academic_institutions_normalised_names_mapping = dict(uk_academic_institutions[['top_level_web_domain', 'PROVIDER_NAME']].values)  # create a dict for lookup
    uk_academic_institutions_common_names_mapping = dict(uk_academic_institutions[['top_level_web_domain', 'VIEW_NAME']].values)  # create a dict for lookup

    # Insert normalised (official) name for organiser
    idx = workshops.columns.get_loc("organiser_country_code") + 1
    workshops.insert(loc=idx, column='organiser_normalised_name', value=workshops["organiser_web_domain"])
    workshops['organiser_normalised_name'] = workshops['organiser_normalised_name'].map(uk_academic_institutions_normalised_names_mapping, na_action="ignore")

    # Insert common name for organiser
    workshops.insert(loc=idx + 1, column='organiser_common_name', value=workshops["organiser_web_domain"])
    workshops['organiser_common_name'] = workshops['organiser_common_name'].map(uk_academic_institutions_common_names_mapping, na_action="ignore")

    # Extract workshop year from its slug and add as a new column
    idx = workshops.columns.get_loc("start") + 1
    workshops.insert(loc=idx, column='year', value=workshops["start"])
    workshops["year"] = workshops["start"].map(lambda date: datetime.datetime.strptime(date, "%Y-%m-%d").year,na_action="ignore")

    # Extract workshop scientific domains from a string to a list
    idx = workshops.columns.get_loc("workshop_domains")
    workshops.insert(loc=idx, column='workshop_domains_list', value=workshops["workshop_domains"])
    workshops["workshop_domains_list"] = workshops["workshop_domains"].str.split(':')

    # Save the processed workshop data
    workshops.to_csv(processed_workshops_file, encoding="utf-8", index=False)
    print("Saved processed Carpentry workshop data to "+ processed_workshops_file +"\n")

    ############################ Extract and process instructor data ########################

    print("\nExtracting workshops from: " + REDASH_API_INSTRUCTORS_QUERY_URL)
    # Get instructor data as returned by a predefined query within Carpentries Redash system (cached results are returned
    # from the last time Redash ran the query, currently set to run every 2 weeks)
    instructors = get_csv_data_redash(REDASH_API_INSTRUCTORS_QUERY_URL, REDASH_API_KEY)
    print("\n####### Extracted " + str(instructors.index.size) + " instructors. #######\n")

    # Save raw instructor data
    instructors.to_csv(raw_instructors_file, encoding="utf-8", index=False)
    print("Saved raw Carpentry workshop data to " + raw_instructors_file + "\n")

    # Process the instructor data a bit to get it ready for further analyses and mapping

    # Insert normalised/official names for institutions (for UK academic institutions)
    print("\nInserting normalised name for instructors' affiliations/institutions...\n")
    instructors = helper.insert_normalised_institution(instructors, "institution")

    # Insert latitude, longitude pairs for instructors' institutions
    print("\nInserting geocoordinates for instructors' affiliations/institutions...\n")
    instructors = helper.insert_institutional_geocoordinates(instructors, "normalised_institution", "latitude", "longitude")

    # Insert UK regional info based on instructors's affiliations
    print("\nInserting regions for instructors' affiliations/institutions...\n")
    idx = instructors.columns.get_loc("institution") + 1
    instructors.insert(loc=idx, column='institutional_region', value=instructors["institution"])
    instructors['region'] = instructors.apply(lambda x: helper.get_uk_region(latitude=x['latitude'], longitude=x['longitude']), axis=1)
    print("\nGetting regions for institutions took a while but it has finished now.\n")

    # Insert UK regional info based on nearest airport
    print("\nInserting regions for instructors based on nearest airport...\n")
    instructors.merge(UK_AIRPORTS[["airport_code", "region"]], how="left")
    instructors.rename({"region" : "airport_region"}, inplace=True)

    # Save the processed instructor data
    instructors.to_csv(processed_instructors_file, encoding="utf-8", index=False)
    print("Saved processed Carpentry instructor data to " + processed_instructors_file + "\n")

def get_csv_data_redash(query_results_url, api_key):
    """
    Get data in csv format from the Carpentries Redash system
    :param query_results_url: Redash query results URL.
    :param api_key: API key to access the query results
    :return: data in csv format as returned by the SQL query in Redash
    """
    try:
        # Response is a CSV data
        response = requests.get(query_results_url, params={"api_key": api_key})
        response.raise_for_status()  # check if request was successful
        data = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
        return data
    except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as ex:
        # Catastrophic error occurred or HTTP request was not successful for some
        # reason (e.g. status code 4XX or 5XX was returned)
        print("Ooops - something went wrong when getting data from Redash ...")
        print(ex.format_exc())
    except Exception as ex:
        print("Ooops - something went wrong when turning data into a DataFrame ...")
        print(ex.format_exc())


def extract_top_level_domain(domain):
    """
    Extract host's top level domain from strings like 'cmist.manchester.ac.uk' to 'manchester.ac.uk'.
    top level domain 'manchester.ac.uk'.
    :param domain
    :return:
    """

    domain_parts = list(filter(None, re.split("(.+?)\.", domain)))
    if len(domain_parts) >= 3:
        domain_parts = domain_parts[-3:]  # Get the last 3 elements of the list only
    top_level_domain = ''.join((x + '.') for x in domain_parts) # join parts with '.' in between
    top_level_domain = top_level_domain[:-1]    # remove the extra '.' at the end after joining
    return top_level_domain


if __name__ == '__main__':
    main()
