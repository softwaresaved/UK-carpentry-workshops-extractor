import pandas as pd
import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import argparse
import sys
import json
import gmaps
import config

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

# GOOGLE_DRIVE_DIR_ID = "0B6P79ipNuR8EdDFraGgxMFJaaVE"


def load_data_from_csv(csv_file, columns=None):
    """
    Loads data from a CSV file into a dataframe with an optional list of columns to load.
    """
    df = pd.read_csv(csv_file, usecols=columns)
    return pd.DataFrame(df)


def google_drive_authentication():
    """
    Authentication to a Google Drive account
    """
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    return drive


def google_drive_upload(file, drive, parents_list, convert):
    """
    Upload a file to a folder in Google Drive
    """
    gfile = drive.CreateFile({'parents': parents_list,
                              'title': os.path.basename(file)})
    gfile.SetContentFile(file)
    gfile.Upload({'convert': convert})


def parse_command_line_paramters():
    parser = argparse.ArgumentParser()
    if "workshop" in os.path.basename(sys.argv[0]): # e.g. the name of the script is 'analyse_workshops'
        parser.add_argument('-w', '--workshops_file', type=str, default=None,
                            help='an absolute path to the workshops CSV file to analyse/map')
    elif "instructor" in os.path.basename(sys.argv[0]):
        parser.add_argument('-i', '--instructors_file', type=str, default=None,
                            help='an absolute path to instructors CSV file to analyse/map')
    else:
        print("You are possibly not invoking the correct python script - analyse_workshops.py or analyse_instructors.py.")
        exit(1)

    parser.add_argument('-gid', '--google_drive_dir_id', type=str,
                        help='ID of a Google Drive directory where to upload the analyses and map files to')
    args = parser.parse_args()
    return args


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
    df.to_excel(writer, sheet_name=sheet_name, index = False)
    return writer

def drop_null_values_from_columns(df, column_list):
    for column in column_list:
        df = df.dropna(subset=[column])
    return df

def fix_UK_academic_institutions_names(df):
    """
    Fix names of academic institutions to be the official names, so we can cross reference them with their geocodes later on.
    """
    df.loc[df.institution == 'Imperial College London', 'institution'] = 'Imperial College of Science, Technology and Medicine'
    df.loc[df.institution == 'Queen Mary University of London', 'institution'] = 'Queen Mary and Westfield College, University of London'
    df.loc[df.institution == 'Aberystwyth University', 'institution'] = 'Prifysgol Aberystwyth'
    return df

def remove_stopped_workshops(df, tag_list):
    for tag in tag_list:
        df = df[df.tags != tag]
    return df

def get_UK_non_academic_institutions_coords():
    """
    Return coordinates for UK institutions that are not high education providers
    (so are not in the official academic institutions list), but appear in AMY as affiliations of UK instructors.
    This list needs to be periodically updated as more non-academic affiliations appear in AMY.
    """
    non_academic_UK_institutions_coords = json.load(open(CURRENT_DIR + '/UK-non-academic-institutions-geodata.json'))
    return pd.DataFrame(non_academic_UK_institutions_coords)

def insert_institutions_geocoordinates(df, affiliations_geocoordinates_df):
    # Insert latitude and longitude for affiliations, by looking up the all_uk_institutions_coords_df
    idx = df.columns.get_loc("institution")  # index of column where 'institution' is kept
    df.insert(loc=idx + 1,
                                       column='latitude',
                                       value=df['institution'])  # copy values from 'institution' column and insert to the right
    df.insert(loc=idx + 2,
                                       column='longitude',
                                       value=df['institution'])  # copy values from 'institution' column and insert to the right
    # replace with the affiliation's latitude and longitude coordinates
    df['latitude'] = df['latitude'].map(
        affiliations_geocoordinates_df.set_index('VIEW_NAME')['LATITUDE'])
    df['longitude'] = df['longitude'].map(
        affiliations_geocoordinates_df.set_index('VIEW_NAME')['LONGITUDE'])

    return df


def get_center(coords_df):

    # Extract longitude and latitude columns from the dataframe
    coords = coords_df[['LATITUDE', 'LONGITUDE']]
    tuples = [tuple(coords) for coords in coords.values]
    x, y = zip(*tuples)

    ## Find center
    center = (max(x) + min(x)) / 2., (max(y) + min(y)) / 2.

    return center


def generate_heatmap(df):
    gmaps.configure(api_key=config.api_key)

    lat_list = []
    long_list = []
    for index, row in df.iterrows():
        long_list.append(row['longitude'])
        lat_list.append(row['latitude'])

    locations = zip(lat_list, long_list)

    ## Resize the map to fit the whole screen.
    map = gmaps.Map(height='100vh', layout={'height': '100vh'})

    map.add_layer(gmaps.heatmap_layer(locations))

    return map


def generate_circles_map(df):
    """
    Generates a map from the dataframe where bigger dots indicate bigger counts for a location's geocoordinates.
    """
    gmaps.configure(api_key=config.api_key)

    ## Calculate the values for the circle scalling in the map.
    max_value = df['count'].max()
    min_value = df['count'].min()
    grouping = (max_value - min_value) / 3
    second_value = min_value + grouping
    third_value = second_value + grouping

    ## Create lists that will hold the found values.
    names_small = []
    locations_small = []

    names_medium = []
    locations_medium = []

    names_large = []
    locations_large = []

    ## Iterate through the dataframe to find the information needed to fill
    ## the lists.
    for index, row in df.iterrows():
        long_coords = df['longitude']
        lat_coords = df['latitude']
        if not long_coords.empty and not lat_coords.empty:
            if row['count'] >= min_value and row['count'] < second_value:
                locations_small.append((lat_coords.iloc[index], long_coords.iloc[index]))
                names_small.append(row['institution'] + ': ' + str(row['count']))
            elif row['count'] >= second_value and row['count'] < third_value:
                locations_medium.append((lat_coords.iloc[index], long_coords.iloc[index]))
                names_medium.append(row['institution'] + ': ' + str(row['count']))
            elif row['count'] >= third_value and row['count'] <= max_value:
                locations_large.append((lat_coords.iloc[index], long_coords.iloc[index]))
                names_large.append(row['institution'] + ': ' + str(row['count']))
        else:
            print('For institution "' + row[
                'affiliation'] + '" we either have not got coordinates or it is not the official name of an UK '
                                 'academic institution. Skipping it ...\n')

    ## Add the different markers to different layers corresponding to the
    ## different amounts of instructors per affiliation.
    symbol_layer_small = gmaps.symbol_layer(locations_small, fill_color="#ff6600", stroke_color="#ff6600",
                                            scale=3, display_info_box=True, info_box_content=names_small)
    symbol_layer_medium = gmaps.symbol_layer(locations_medium, fill_color="#ff6600", stroke_color="#ff6600",
                                             scale=6, display_info_box=True, info_box_content=names_medium)
    symbol_layer_large = gmaps.symbol_layer(locations_large, fill_color="#ff6600", stroke_color="#ff6600",
                                            scale=8, display_info_box=True, info_box_content=names_large)

    ## Resize the map to fit the whole screen.
    map = gmaps.Map(height='100vh', layout={'height': '100vh'})

    ## Add all the layers to the map.
    map.add_layer(symbol_layer_small)
    map.add_layer(symbol_layer_medium)
    map.add_layer(symbol_layer_large)

    return map