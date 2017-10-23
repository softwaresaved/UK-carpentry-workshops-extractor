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
findFile = [filename for filename in os.listdir(dirP + '/data/workshops')
            if filename.startswith("carpentry-workshops_") and filename.endswith('.csv')]
try:
    len(findFile)!=0
except FileNotFoundError:
    print("The file you were looking for is not found.")
        
## Create a spreadsheet
name_file = re.sub('\.csv$', '', findFile[-1])
excel_file = 'analysis_' + name_file + '.xlsx'
writer = pd.ExcelWriter(dirP + '/data/workshops/' + excel_file , engine='xlsxwriter')
writerClear = pd.ExcelWriter(dirP + '/data/workshops/' + name_file + '.xlsx', engine='xlsxwriter')

## Load and upload non anonymized data to Google Drive
##data_all = pd.read_csv(dirP + '/data/workshops/' + findFile[-1])
##data_all.to_excel(writerClear, sheet_name='Workshops_Data')
##writerClear.save()
##upload_data = drive.CreateFile({"parents": [{"kind": "drive#fileLink",
##                                             "id": "0B6P79ipNuR8EdDFraGgxMFJaaVE"}],
##                                'title': findFile[-1]})
##upload_data.SetContentFile(dirP + '/data/workshops/' + name_file + '.xlsx')
##upload_data.Upload({'convert': True})
##print("Document Uploaded to Google Drive.")

## Loads data without personal information
data_workshops = pd.read_csv(dirP + '/data/workshops/' + findFile[-1],
                             usecols=['start', 'tags', 'venue',
                                      'number_of_attendees'])
data_workshops = pd.DataFrame(data_workshops)

## Put the anonymized data into one spreadsheet tab
data_workshops.to_excel(writer, sheet_name='Anonymized_Data')

## Change SWC, WiSE to just SWC
data_workshops.tags.replace(['SWC, WiSE'], ['SWC'], inplace=True)

## Transform earliest-badge-awarded to just year
data_workshops['start'] = pd.to_datetime(
    data_workshops['start'])

data_workshops['start'] = data_workshops[
    'start'].dt.year

## Create corresponding tables and graphs and write to excel
## Number of Workshops per Year
year_table = data_workshops.groupby(['start']).size()

year_table.to_excel(writer, sheet_name='Work_per_Year')

workbook  = writer.book
worksheet = writer.sheets['Work_per_Year']

chart1 = workbook.add_chart({'type': 'column'})

chart1.add_series({
    'categories': ['Work_per_Year', 1, 0, len(year_table.index), 0],
    'values': ['Work_per_Year', 1, 1, len(year_table.index), 1],
    'gap': 2,
})

chart1.set_y_axis({'major_gridlines': {'visible': False}})
chart1.set_legend({'position': 'none'})
chart1.set_x_axis({'name': 'Year of the Workshop'})
chart1.set_y_axis({'name': 'Number of Workshops', 'major_gridlines': {'visible': False}})
chart1.set_title ({'name': 'Number of Workshops per Year'})

worksheet.insert_chart('D2', chart1)

## Number of Workshops per Institution
venue_table = data_workshops.groupby(['venue']).size()

venue_table.to_excel(writer, sheet_name='Work_per_Inst')

workbook  = writer.book
worksheet = writer.sheets['Work_per_Inst']

chart2 = workbook.add_chart({'type': 'column'})

chart2.add_series({
    'categories': ['Work_per_Inst', 1, 0, len(venue_table.index), 0],
    'values': ['Work_per_Inst', 1, 1, len(venue_table.index), 1],
    'gap': 2,
})

chart2.set_y_axis({'major_gridlines': {'visible': False}})
chart2.set_legend({'position': 'none'})
chart2.set_x_axis({'name': 'Institution Location'})
chart2.set_y_axis({'name': 'Number of Workshops', 'major_gridlines': {'visible': False}})
chart2.set_title ({'name': 'Number of Workshops per Institution'})

worksheet.insert_chart('D2', chart2)

## Number of workshops per type
type_table = data_workshops.groupby(['tags']).size()

type_table.to_excel(writer, sheet_name='Work_per_Type')

workbook  = writer.book
worksheet = writer.sheets['Work_per_Type']

chart3 = workbook.add_chart({'type': 'column'})

chart3.add_series({
    'categories': ['Work_per_Type', 1, 0, len(type_table.index), 0],
    'values': ['Work_per_Type', 1, 1, len(type_table.index), 1],
    'gap': 2,
})

chart3.set_y_axis({'major_gridlines': {'visible': False}})
chart3.set_legend({'position': 'none'})
chart3.set_x_axis({'name': 'Type of Workshop'})
chart3.set_y_axis({'name': 'Number of Workshops', 'major_gridlines': {'visible': False}})
chart3.set_title ({'name': 'Number of Workshops per Type'})

worksheet.insert_chart('D2', chart3)

## Number of Workshops per Institution and Year
venue_year_table = data_workshops.groupby(['venue','start']).size().to_frame()
venue_year_table = venue_year_table.pivot_table(index='venue',columns = 'start')

venue_year_table.to_excel(writer, sheet_name='Work_per_IntYear')

workbook  = writer.book
worksheet = writer.sheets['Work_per_IntYear']

chart4 = workbook.add_chart({'type': 'column'})

ranged = range(1,len(venue_year_table.columns)+1)

for number in ranged:
    chart4.add_series({
        'name' : ['Work_per_IntYear', 1, number],
        'categories': ['Work_per_IntYear', 3, 0, len(venue_year_table.index)+2, 0],
        'values': ['Work_per_IntYear', 3, number, len(venue_year_table.index)+2, number],
        'gap': 2,
    })

chart4.set_y_axis({'major_gridlines': {'visible': False}})
chart4.set_x_axis({'name': 'Institution Location'})
chart4.set_y_axis({'name': 'Number of Workshops', 'major_gridlines': {'visible': False}})
chart4.set_title ({'name': 'Number of Workshops per Institution per Year'})

worksheet.insert_chart('I2', chart4)

## Number of workshops per Type and Year
type_year_table = data_workshops.groupby(['tags','start']).size().to_frame()
type_year_table = type_year_table.pivot_table(index='tags',columns = 'start')

type_year_table.to_excel(writer, sheet_name='Work_per_TypeYear')

workbook  = writer.book
worksheet = writer.sheets['Work_per_TypeYear']

chart5 = workbook.add_chart({'type': 'column'})

ranged = range(1,len(type_year_table.columns)+1)

for number in ranged:
    chart5.add_series({
        'name' : ['Work_per_TypeYear', 1, number],
        'categories': ['Work_per_TypeYear', 3, 0, len(type_year_table.index)+2, 0],
        'values': ['Work_per_TypeYear', 3, number, len(type_year_table.index)+2, number],
        'gap': 2,
    })

chart5.set_y_axis({'major_gridlines': {'visible': False}})
chart5.set_x_axis({'name': 'Type of Workshop'})
chart5.set_y_axis({'name': 'Number of Workshops', 'major_gridlines': {'visible': False}})
chart5.set_title ({'name': 'Number of Workshops per Type per Year'})

worksheet.insert_chart('I2', chart5)

## Number of attendees per year
attendees_year_table = data_workshops.groupby([
    'start'])['number_of_attendees'].sum().to_frame()

attendees_year_table.to_excel(writer, sheet_name='Attend_per_Year')

workbook  = writer.book
worksheet = writer.sheets['Attend_per_Year']

chart6 = workbook.add_chart({'type': 'column'})

ranged = range(1,len(attendees_year_table.columns)+1)

for number in ranged:
    chart6.add_series({
        'categories': ['Attend_per_Year', 1, 0, len(attendees_year_table.index), 0],
        'values': ['Attend_per_Year', 1, 1, len(attendees_year_table.index), 1],
        'gap': 2,
    })

chart6.set_y_axis({'major_gridlines': {'visible': False}})
chart6.set_legend({'position': 'none'})
chart6.set_x_axis({'name': 'Year of the Workshop'})
chart6.set_y_axis({'name': 'Number of Attendees', 'major_gridlines': {'visible': False}})
chart6.set_title ({'name': 'Number of Attendees per Year'})

worksheet.insert_chart('I2', chart6)

## Number of attendees per type
attendees_type_table = data_workshops.groupby([
    'tags'])['number_of_attendees'].sum().to_frame()

attendees_type_table.to_excel(writer, sheet_name='Attend_per_Type')

workbook  = writer.book
worksheet = writer.sheets['Attend_per_Type']

chart7 = workbook.add_chart({'type': 'column'})

ranged = range(1,len(attendees_type_table.columns)+1)

for number in ranged:
    chart7.add_series({
        'categories': ['Attend_per_Type', 1, 0, len(attendees_type_table.index), 0],
        'values': ['Attend_per_Type', 1, 1, len(attendees_type_table.index), 1],
        'gap': 2,
    })

chart7.set_y_axis({'major_gridlines': {'visible': False}})
chart7.set_legend({'position': 'none'})
chart7.set_x_axis({'name': 'Type of the Workshop'})
chart7.set_y_axis({'name': 'Number of Attendees', 'major_gridlines': {'visible': False}})
chart7.set_title ({'name': 'Number of Attendees per Type of Workshop'})

worksheet.insert_chart('I2', chart7)

## Number of attendees per type and year
type_year_attend_table = data_workshops.groupby(['tags','start'])['number_of_attendees'].sum().to_frame()
type_year_attend_table = type_year_attend_table.pivot_table(index='tags',columns = 'start')

type_year_attend_table.to_excel(writer, sheet_name='Attend_per_TypeYear')

workbook  = writer.book
worksheet = writer.sheets['Attend_per_TypeYear']

chart8 = workbook.add_chart({'type': 'column'})

ranged = range(1,len(type_year_attend_table.columns)+1)

for number in ranged:
    chart8.add_series({
        'name' : ['Attend_per_TypeYear', 1, number],
        'categories': ['Attend_per_TypeYear', 3, 0, len(type_year_attend_table.index)+2, 0],
        'values': ['Attend_per_TypeYear', 3, number, len(type_year_attend_table.index)+2, number],
        'gap': 2,
    })

chart8.set_y_axis({'major_gridlines': {'visible': False}})
chart8.set_x_axis({'name': 'Type of Workshop'})
chart8.set_y_axis({'name': 'Number of Attendees', 'major_gridlines': {'visible': False}})
chart8.set_title ({'name': 'Number of Attendees per Type per Year'})

worksheet.insert_chart('I2', chart8)

##Create ReadMe tab
dateExtract = name_file.split("_")
textExtract = "Data in sheet " + findFile[-1] + " was extracted on " + dateExtract[2] + " using Ruby script from https://github.com/softwaresaved/carpentry-workshops-instructors-extractor."
textInfo = "It contains info on UK Carpentry workshop in that went ahead or will go ahead/are in planning as of the date it was run on."

workbook  = writer.book
worksheet = workbook.add_worksheet('ReadMe')
worksheet.write(0, 0, textExtract)
worksheet.write(2, 0, textInfo)

writer.save()
print("Spreadsheet Saved")

## Put the excel into Google drive
##test_file = drive.CreateFile({"parents": [{"kind": "drive#fileLink",
##                                           "id": "0B6P79ipNuR8EdDFraGgxMFJaaVE"}],
##                              'title': excel_file})
##test_file.SetContentFile(dirP + '/data/workshops/' + excel_file)
##test_file.Upload({'convert': True})
##print("Document Uploaded to Google Drive.")
