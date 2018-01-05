import pandas as pd
import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import argparse
import sys
import json

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
    df.loc[df.affiliation == 'Imperial College London', 'affiliation'] = 'Imperial College of Science, Technology and Medicine'
    df.loc[df.affiliation == 'Queen Mary University of London', 'affiliation'] = 'Queen Mary and Westfield College, University of London'
    df.loc[df.affiliation == 'Aberystwyth University', 'affiliation'] = 'Prifysgol Aberystwyth'
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


def get_center(coords_df):

    # Extract longitude and latitude columns from the dataframe
    coords = coords_df[['LATITUDE', 'LONGITUDE']]
    tuples = [tuple(coords) for coords in coords.values]
    x, y = zip(*tuples)

    ## Find center
    center = (max(x) + min(x)) / 2., (max(y) + min(y)) / 2.

    return center
