import pandas as pd
import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import argparse
import sys


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
    df.loc[df.affiliation == 'Imperial College London', 'affiliation'] = 'Imperial College of Science, Technology and Medicine'
    df.loc[df.affiliation == 'Queen Mary University of London', 'affiliation'] = 'Queen Mary and Westfield College, University of London'
    return df

def remove_stalled_workshops(df, tag_list):
    for tag in tag_list:
        df = df[df.tags != tag]
    return df

def get_UK_non_academic_institutions_coords():
    """
    Return coordinates for non UK academic institutions that we know appear in AMY for affiliations of UK instructors.
    This list needs to be periodically updated as more non-academic affiliations appear in AMY.
    """
    non_academic_UK_institutions_coords = [
        {'VIEW_NAME': 'Wellcome Trust Sanger Institute', 'LONGITUDE': 0.18558740000003127, 'LATITUDE': 52.0797171},
        {'VIEW_NAME': 'Earlham Institute', 'LONGITUDE': 1.2189869000000044, 'LATITUDE': 52.6217407},
        {'VIEW_NAME': 'Arriva Group', 'LONGITUDE': -1.4335148000000117, 'LATITUDE': 54.86353090000001},
        {'VIEW_NAME': 'Delcam Ltd', 'LONGITUDE': -1.8450110999999652, 'LATITUDE': 52.46245099999999},
        {'VIEW_NAME': 'Met Office', 'LONGITUDE': -3.472338000000036, 'LATITUDE': 50.72742100000001},
        {'VIEW_NAME': 'Thales', 'LONGITUDE': -2.185189799999989, 'LATITUDE': 53.3911872},
        {'VIEW_NAME': 'The John Innes Centre', 'LONGITUDE': 1.2213810000000649, 'LATITUDE': 52.622271},
        {'VIEW_NAME': 'Climate Code Foundation', 'LONGITUDE': -1.52900139999997, 'LATITUDE': 53.3143842},
        {'VIEW_NAME': 'Kew Royal Botanic Gardens', 'LONGITUDE': -0.2955729999999903, 'LATITUDE': 51.4787438},
        {'VIEW_NAME': 'The Sainsbury Laboratory', 'LONGITUDE': 1.2228880000000117, 'LATITUDE': 52.622316},
        {'VIEW_NAME': 'James Hutton Institute', 'LONGITUDE': -2.158366000000001, 'LATITUDE': 57.133131},
        {'VIEW_NAME': 'Aberystwyth University', 'LONGITUDE': -4.0659220000000005, 'LATITUDE': 52.417776},
        {'VIEW_NAME': 'Daresbury Laboratory', 'LONGITUDE': -2.6399344000000156, 'LATITUDE': 53.34458119999999},
        {'VIEW_NAME': 'Owen Stephens Consulting', 'LONGITUDE': -1.520078900000044, 'LATITUDE': 52.28519050000001},
        {'VIEW_NAME': 'Public Health England', 'LONGITUDE': -0.10871080000003985, 'LATITUDE': 51.50153030000001},
        {'VIEW_NAME': 'IBM', 'LONGITUDE': -0.1124157000000423, 'LATITUDE': 51.5071586},
        {'VIEW_NAME': 'Media Molecule', 'LONGITUDE': -0.5756398999999419, 'LATITUDE': 51.2355975},
        {'VIEW_NAME': 'BBC', 'LONGITUDE': -0.226846, 'LATITUDE': 51.510025},
        {'VIEW_NAME': 'Culham Centre for Fusion Energy', 'LONGITUDE': -1.2305023999999776, 'LATITUDE': 51.6588505},
        {'VIEW_NAME': 'Digital Greenwich', 'LONGITUDE': 0.006866500000000997, 'LATITUDE': 51.5007361},
        {'VIEW_NAME': 'National Oceanography Centre', 'LONGITUDE': -1.3945247000000336, 'LATITUDE': 50.8928051},
        {'VIEW_NAME': 'Natural History Museum', 'LONGITUDE': -0.17636719999995876, 'LATITUDE': 51.49671499999999},
        {'VIEW_NAME': 'Rutherford Appleton Laboratory', 'LONGITUDE': -1.3159226000000217, 'LATITUDE': 51.5726621},
        {'VIEW_NAME': 'SAP', 'LONGITUDE': -0.44502220000003945, 'LATITUDE': 51.44902499999999},
        {'VIEW_NAME': 'The Francis Crick Institute', 'LONGITUDE': -0.12875610000003235, 'LATITUDE': 51.5315844}]

    return pd.DataFrame(non_academic_UK_institutions_coords)


def get_center(coords_df):

    # Extract longitude and latitude columns from the dataframe
    coords = coords_df[['LATITUDE', 'LONGITUDE']]
    tuples = [tuple(coords) for coords in coords.values]
    x, y = zip(*tuples)

    ## Find center
    center = (max(x) + min(x)) / 2., (max(y) + min(y)) / 2.

    return center
