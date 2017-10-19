import os
import re
import pandas as pd
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

## Gogle Drive Authentication
##gauth = GoogleAuth()
##gauth.LocalWebserverAuth()
##drive = GoogleDrive(gauth)

## Find the file to be loaded and check if exists
dirP = os.path.dirname(os.path.realpath(__file__))
findFile = [filename for filename in os.listdir(dirP + '/data/instructors')
            if filename.startswith("carpentry-instructors_") and filename.endswith('.csv')]
try:
    len(findFile)!=0
except FileNotFoundError:
    print("The file you were looking for is not found.")

## Create a spreadsheet
name_file = re.sub('\.csv$', '', findFile[-1]).strip()
excel_file = 'analysis_' + name_file + '.xlsx'
writer = pd.ExcelWriter(dirP + '/data/instructors/' + excel_file , engine='xlsxwriter')
writerClear = pd.ExcelWriter(dirP + '/data/instructors/' + name_file + '.xlsx', engine='xlsxwriter')

## Load and upload non anonymized data to Google Drive
##data_all = pd.read_csv(dirP + '/data/instructors/' + findFile[-1])
##data_all.to_excel(writerClear, sheet_name='Instructors_Data')
##writerClear.save()
##upload_data = drive.CreateFile({'parents': [{'kind': 'drive#fileLink',
##                                             'id': '0B6P79ipNuR8EdDFraGgxMFJaaVE'}],
##                                'title': findFile[-1]})
##upload_data.SetContentFile(dirP + '/data/instructors/' + name_file + '.xlsx')
##upload_data.Upload({'convert': True})
##print("Document Uploaded to Google Drive.")

## Loads data without personal information
data_instructors = pd.read_csv(dirP + '/data/instructors/' + findFile[-1],
                               usecols=['country_code','nearest_airport_name',
                                        'nearest_airport_code', 'affiliation',
                                        'instructor-badges',
                                        'swc-instructor-badge-awarded',
                                        'dc-instructor-badge-awarded',
                                        'trainer-badge-awarded',
                                        'earliest-badge-awarded',
                                        'number_of_workshops_taught'])

data_instructors = pd.DataFrame(data_instructors)

## Removes null values for affiliation and country_code
data_instructors = data_instructors.dropna(subset=['country_code'])
data_instructors = data_instructors.dropna(subset=['affiliation'])

## Put the anonymized data into one spreadsheet tab
data_instructors.to_excel(writer, sheet_name='Anonymized_Data')

## Transform earliest-badge-awarded to just year
data_instructors['earliest-badge-awarded'] = pd.to_datetime(
    data_instructors['earliest-badge-awarded'])

data_instructors['earliest-badge-awarded'] = data_instructors[
    'earliest-badge-awarded'].dt.year

## Create corresponding tables and graphs and write to the spreadsheet
## Number of People per nearest_airport_code
city_table = data_instructors.groupby(['nearest_airport_code']).size()

city_table.to_excel(writer, sheet_name='Inst_per_Airport')

workbook  = writer.book
worksheet = writer.sheets['Inst_per_Airport']

chart1 = workbook.add_chart({'type': 'column'})

chart1.add_series({
    'categories': ['Inst_per_Airport', 1, 0, len(city_table.index), 0],
    'values': ['Inst_per_Airport', 1, 1, len(city_table.index), 1],
    'gap': 2,
})

chart1.set_y_axis({'major_gridlines': {'visible': False}})
chart1.set_legend({'position': 'none'})
chart1.set_x_axis({'name': 'Nearest Airport Code'})
chart1.set_y_axis({'name': 'Number of Instructors', 'major_gridlines': {'visible': False}})
chart1.set_title ({'name': 'Number of Instructors per Nearest Airport'})

worksheet.insert_chart('D2', chart1)

##Region Conversions of the existing Airports
regions_excel = pd.ExcelFile('./lib/UK-regions-airports.xlsx')
regions = regions_excel.parse('UK-regions-airports')
dict_Regions = area_dict = dict(zip(regions['Airport_code'],
                                    regions['UK_region']))

data_instructors_region = data_instructors.copy()
data_instructors_region['nearest_airport_code'].replace(dict_Regions, inplace=True)

## Number of People per region
region_table = data_instructors_region.groupby(['nearest_airport_code']).size()

region_table.to_excel(writer, sheet_name='Inst_per_Region')

workbook  = writer.book
worksheet = writer.sheets['Inst_per_Region']

chart2 = workbook.add_chart({'type': 'column'})

chart2.add_series({
    'categories': ['Inst_per_Region', 1, 0, len(region_table.index), 0],
    'values': ['Inst_per_Region', 1, 1, len(region_table.index), 1],
    'gap': 2,
})

chart2.set_y_axis({'major_gridlines': {'visible': False}})
chart2.set_legend({'position': 'none'})
chart2.set_x_axis({'name': 'Region of the UK'})
chart2.set_y_axis({'name': 'Number of Instructors', 'major_gridlines': {'visible': False}})
chart2.set_title ({'name': 'Number of Instructors per Region'})

worksheet.insert_chart('D2', chart2)

## Number of people per year of earliest badge
year_table = data_instructors.groupby(['earliest-badge-awarded']).size()

year_table.to_excel(writer, sheet_name='Inst_per_Year')

workbook  = writer.book
worksheet = writer.sheets['Inst_per_Year']

chart3 = workbook.add_chart({'type': 'column'})

chart3.add_series({
    'categories': ['Inst_per_Year', 1, 0, len(year_table.index), 0],
    'values': ['Inst_per_Year', 1, 1, len(year_table.index), 1],
    'gap': 2,
})

chart3.set_y_axis({'major_gridlines': {'visible': False}})
chart3.set_legend({'position': 'none'})
chart3.set_x_axis({'name': 'Date of the earliest badge awarded'})
chart3.set_y_axis({'name': 'Number of Instructors', 'major_gridlines': {'visible': False}})
chart3.set_title ({'name': 'Number of Instructors per Year'})

worksheet.insert_chart('D2', chart3)

##Create ReadMe tab
dateExtract = name_file.split("_")
textExtract = "Data in sheet " + findFile[-1] + " was extracted on " + dateExtract[2] + " using Ruby script from https://github.com/softwaresaved/carpentry-workshops-instructors-extractor."
textInfo = "It contains info on certified Carpentry instructors in the UK."

workbook  = writer.book
worksheet = workbook.add_worksheet('ReadMe')
worksheet.write(0, 0, textExtract)
worksheet.write(2, 0, textInfo)

writer.save()
print("Spreadsheet Saved.")

## Upload the spreadsheet into Google Drive
##upload_excel = drive.CreateFile({'parents': [{'kind': 'drive#fileLink',
##                                              'id': '0B6P79ipNuR8EdDFraGgxMFJaaVE'}],
##                                 'title': excel_file})
##upload_excel.SetContentFile(dirP + '/data/instructors/' + excel_file)
##upload_excel.Upload({'convert': True})
##print("Document Uploaded to Google Drive.")
