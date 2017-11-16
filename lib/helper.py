import pandas as pd
import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

#GOOGLE_DRIVE_DIR_ID = "0B6P79ipNuR8EdDFraGgxMFJaaVE"


def load_workshops_data(csv_file, columns=None):
    """
    Loads data from the CSV file with workshops into a dataframe with an optional list of columns to load.
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

