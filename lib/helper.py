import pandas as pd
import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import argparse


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
    parser.add_argument('-w', '--workshops_file', type=str, default=None,
                        help='an absolute path to the workshops file to analyse')
    parser.add_argument('-i', '--instructors_file', type=str, default=None,
                        help='an absolute path to instructors file to analyse')
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
    df.to_excel(writer, sheet_name=sheet_name)
    return writer
