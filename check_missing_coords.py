import os
import pandas as pd
import numpy as np

DIR_PATH = os.path.dirname(os.path.realpath(__file__))

FILE_NAME = DIR_PATH + '/lib/UK-academic-institutions-geodata.xlsx'

def create_excel_file_dataframe(filename):
    """
    Creates a dataframe for the corresponding excel file.
    """
    try:
        excel_file = pd.ExcelFile(filename)
        return excel_file.parse('UK-academic-institutions')
    except FileNotFoundError:
        print('The file you were looking for is not found.')
        
def transform_missing_values(df):
    """
    Replaces missing nan values for empty strings.
    """
    return df.replace(np.nan, '', regex=True)

def add_missing_coordinates(df):
    """
    Adds missing know coordinates and makes a list of the institutions
    that have missing coordinates.
    """
    ## Missing known coordinates
    miss_coords = [["The Queen's University of Belfast", -5.9348, 54.5839],
                   ["St Mary's University College", -5.9613, 54.592],
                   ['University of Ulster', -6.6725, 55.1468],
                   ['Stranmillis University College', -5.9352, 54.5733]]

    ## Missing institutions names
    list_institutions = []
    list_institutions_included = []

    ## Check for missing data in coordinates and add missing coords
    for index, row in df.iterrows():
        if row['LONGITUDE']=='':
            list_institutions.append(row['VIEW_NAME'])
            for each in miss_coords:
                if each[0] not in list_institutions_included:
                    list_institutions_included.append(each[0])
                if each[0] == row['VIEW_NAME']:
                    df.set_value(index,'LONGITUDE',each[1])
                    df.set_value(index,'LATITUDE',each[2])
                    
    return df, list_institutions, list_institutions_included

def create_spreadsheet(dirP,df):
    """
    Create a new excel file with the missing known coordinates added.
    """
    new_excel_file = dirP + '/lib/UK-academic-institutions-geodata_missing.xlsx'
    writer = pd.ExcelWriter(new_excel_file , engine='xlsxwriter')

    df.to_excel(writer, sheet_name='UK-academic-institutions')
    writer.save()

def main():
    """
    Main function
    """
    df = create_excel_file_dataframe(FILE_NAME)
    df = transform_missing_values(df)
    df = add_missing_coordinates(df)[0]

    create_spreadsheet(DIR_PATH,df)
    
    print('The institutions missing are: ' + str(add_missing_coordinates(df)[1]))
    print('The coordinates for the following institutions were added to the spreadsheet: '
          + str(add_missing_coordinates(df)[2]))

if __name__ == '__main__':
    main()

