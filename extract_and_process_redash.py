import traceback
import os
import sys
import datetime
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
    workshops_df = get_csv_data_redash(REDASH_API_WORKSHOPS_QUERY_URL, REDASH_API_KEY)
    print("\n####### Extracted " + str(workshops_df.index.size) + " workshops. #######\n")

    # Save raw workshop data
    workshops_df.to_csv(raw_workshops_file, encoding="utf-8", index=False)
    print("Saved raw Carpentry workshop data to "+ raw_workshops_file + "\n")

    ############################ Process workshop data ########################
    # Process the workshop data a bit to get it ready for further analyses and mapping

    # Convert column "tags" from a string to a list of strings
    workshops_df["tags"] = workshops_df["tags"].str.split(',')

    # Extract workshop scientific domains from a string to a list
    workshops_df["workshop_domains"] = workshops_df["workshop_domains"].str.split(':')

    workshops_df = helper.process_workshops(workshops_df)

    # Save the processed workshop data
    workshops_df.to_csv(processed_workshops_file, encoding="utf-8", index=False)
    print("Saved processed Carpentry workshop data to "+ processed_workshops_file +"\n")

    ############################ Extract and process instructor data ########################

    print("\nExtracting workshops from: " + REDASH_API_INSTRUCTORS_QUERY_URL)
    # Get instructor data as returned by a predefined query within Carpentries Redash system (cached results are returned
    # from the last time Redash ran the query, currently set to run every 2 weeks)
    instructors_df = get_csv_data_redash(REDASH_API_INSTRUCTORS_QUERY_URL, REDASH_API_KEY)
    print("\n####### Extracted " + str(instructors_df.index.size) + " instructors. #######\n")

    # Save raw instructor data
    instructors_df.to_csv(raw_instructors_file, encoding="utf-8", index=False)
    print("Saved raw Carpentry workshop data to " + raw_instructors_file + "\n")

    # Process the instructor data a bit to get it ready for further analyses and mapping

    # Insert normalised/official names for institutions (for UK academic institutions)
    print("\nInserting normalised name for instructors' affiliations/institutions...\n")
    instructors_df = helper.insert_normalised_institution(instructors_df, "institution")

    # Insert latitude, longitude pairs for instructors' institutions
    print("\nInserting geocoordinates for instructors' affiliations/institutions...\n")
    instructors_df = helper.insert_institutional_geocoordinates(instructors_df, "normalised_institution", "latitude", "longitude")

    # Insert UK regional info based on instructors's affiliations
    print("\nInserting regions for instructors' affiliations/institutions...\n")
    idx = instructors_df.columns.get_loc("institution") + 1
    instructors_df.insert(loc=idx, column='institutional_region', value=instructors_df["institution"])
    instructors_df['region'] = instructors_df.apply(lambda x: helper.get_uk_region(latitude=x['latitude'], longitude=x['longitude']), axis=1)
    print("\nGetting regions for institutions took a while but it has finished now.\n")

    # Insert UK regional info based on nearest airport
    print("\nInserting regions for instructors based on nearest airport...\n")
    instructors_df.merge(UK_AIRPORTS[["airport_code", "region"]], how="left")
    instructors_df.rename({"region" : "airport_region"}, inplace=True)

    # Save the processed instructor data
    instructors_df.to_csv(processed_instructors_file, encoding="utf-8", index=False)
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


if __name__ == '__main__':
    main()
