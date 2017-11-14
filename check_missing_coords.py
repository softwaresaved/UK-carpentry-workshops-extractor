import os
import pandas as pd
import numpy as np
import traceback
from openpyxl import load_workbook

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

UK_INSTITUTIONS_GEOCODES_FILE = CURRENT_DIR + '/lib/UK-academic-institutions-geodata.xlsx'

def load_geocodes(filename):
    """
    Creates a dataframe for the corresponding excel file.
    """
    excel_file = pd.ExcelFile(filename)
    return excel_file.parse('UK-academic-institutions')

def fix_missing_values(df):
    """
    Replaces missing nan values for empty strings.
    """
    return df.replace(np.nan, '', regex=True)

def add_missing_coordinates(df):
    """
    Adds missing known coordinates (geocodes - latitude and longitude pairs) and make a list of the institutions that have missing coordinates.
    """
    ## Known missing coordinates
    known_missing_coords = {
        "The Queen's University of Belfast" : [-5.9348, 54.5839],
        "St Mary's University College" : [-5.9613, 54.592],
        "University of Ulster" : [-6.6725, 55.1468],
        "Stranmillis University College" : [-5.9352, 54.5733]
    }

    ## Institutions with missing coordinates after fixing
    institutions_with_missing_coords = []

    ## Check for missing data in coordinates and add missing coords
    for index, row in df.iterrows():
        if row['LONGITUDE']=='':
            if row['VIEW_NAME'] in known_missing_coords.keys() :
                df.set_value(index,'LONGITUDE',  known_missing_coords[row['VIEW_NAME']][0])
                df.set_value(index,'LATITUDE', known_missing_coords[row['VIEW_NAME']][1])
                print("Fixing missing coordinates for " + row['VIEW_NAME'])
            else:
                institutions_with_missing_coords.append(row['VIEW_NAME'])

    if len(institutions_with_missing_coords) > 0:
        print('The institutions that are still missing the coordinates are: ' + str(institutions_with_missing_coords))

    return df

def save_geocodes(df, file):
    """
    Save dataframe to an Excel spreadsheet file.
    """
    book = load_workbook(file)
    writer = pd.ExcelWriter(file , engine='openpyxl')
    writer.book = book
    writer.sheets = dict((ws.title, ws) for ws in book.worksheets)

    df.to_excel(writer, sheet_name='UK-academic-institutions',index_label=False, index=False,)
    writer.save()

def main():
    """
    Main function
    """
    print('Checking institutions for missing coordinates (geocodes) ...')
    try:
        df = load_geocodes(UK_INSTITUTIONS_GEOCODES_FILE)
        df = fix_missing_values(df)
        df = add_missing_coordinates(df)
        save_geocodes(df, UK_INSTITUTIONS_GEOCODES_FILE)
    except FileNotFoundError:
        print('The Excel file with geocodes for the UK institutions ' + UK_INSTITUTIONS_GEOCODES_FILE + 'was not found.')
        print(traceback.format_exc())
    except Exception:
        print('Failed to write to the Excel file with geocodes for the UK institutions ' + UK_INSTITUTIONS_GEOCODES_FILE)
        print(traceback.format_exc())


if __name__ == '__main__':
    main()

