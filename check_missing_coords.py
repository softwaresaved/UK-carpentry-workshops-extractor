import os
import pandas as pd
import numpy as np

## Upload excel file of uk institutions
dirP = os.path.dirname(os.path.realpath(__file__))
try:
    findFile = dirP + '/lib/UK-academic-institutions-geodata.xlsx'
except FileNotFoundError:
    print("The file you were looking for is not found.")

## Transform excel into dataframe
excel_file = pd.ExcelFile(findFile)
df = excel_file.parse('UK-academic-institutions')

## Transform missing values into empty strings
df = df.replace(np.nan, '', regex=True)

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

## Create a new spreasheet
##new_excel_file = dirP + '/lib/UK-academic-institutions-geodata_missing.xlsx'
##writer = pd.ExcelWriter(new_excel_file , engine='xlsxwriter')

## Include new dataframe in the spreadsheet
##df.to_excel(writer, sheet_name='UK-academic-institutions')
##writer.save()

## Print missing institutions and the ones who we added to the spreadsheet
print('The institutions missing are: ' + str(list_institutions))
##print('The coordinates for the following institutions were added to the spreadsheet: '
##      + str(list_institutions_included))
