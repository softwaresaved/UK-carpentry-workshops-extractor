import pandas as pd
import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

GOOGLE_DRIVE_DIR_ID = "0B6P79ipNuR8EdDFraGgxMFJaaVE"


def load_workshop_data(csv_file):
    """
    Loads data from the CSV file with workshops into a dataframe
    """
    df = pd.read_csv(csv_file)
    return pd.DataFrame(df)

def google_drive_authentication():
    """
    Authentication to the google drive account
    """
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    return drive


def google_drive_upload(file, drive, dir_id, parameter,variable,boolean):
    """
    Upload a file to Google drive
    """
    upload_excel = drive.CreateFile({'parents': [{parameter:variable,
                                                  'id': dir_id }], #'0B6P79ipNuR8EdDFraGgxMFJaaVE'
                                     'title': os.path.basename(file)})
    upload_excel.SetContentFile(file)
    upload_excel.Upload({'convert': boolean})

