import os
import re
import pandas as pd
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
findFile = [filename for filename in os.listdir(DIR_PATH + '/data/workshops')
            if filename.startswith("carpentry-workshops_") and filename.endswith('.csv')]
if not findFile:
  print('No file was found.')  
else:
    DATA = findFile[-1]
    NAME_FILE = re.sub('\.csv$', '', DATA.strip())
    

def load_data_without_personal_info(filename,dirP):
    """
    Loads data without personal information into a dataframe
    """                
    df = pd.read_csv(dirP + '/data/workshops/' + findFile[-1],
                                 usecols=['start', 'tags', 'venue',
                                          'number_of_attendees'])
    return pd.DataFrame(df)
        
def transform_start(df):
    """
    Transform start to just year
    """ 
    df['start'] = pd.to_datetime(df['start'])
    df['start'] = df['start'].dt.year
    return df

def transform_SWCWISE_SWC(df):
    """
    Transform start to just year
    """
    df.tags.replace(['SWC, WiSE'], ['SWC'], inplace=True)
    return df

def create_spreadsheet(name_file,dirP,df):
    """
    Create the spreadsheet to input resulting data analysis
    and put anonymized data in a spreadsheet tab
    """
    excel_file = 'analysis_' + name_file + '.xlsx'
    writer = pd.ExcelWriter(dirP + '/data/workshops/' + excel_file , engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Anonymized_Data')
    return excel_file, writer

def number_workshops_per_year(df,writer):
    """
    Create corresponding tables and graphs and write to the spreadsheet
    Number of Workshops per Year
    """
    year_table = df.groupby(['start']).size()

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

def number_workshops_per_venue(df,writer):
    """
    Create corresponding tables and graphs and write to the spreadsheet
    Number of Workshops per Venue
    """
    venue_table = df.groupby(['venue']).size()

    venue_table.to_excel(writer, sheet_name='Work_per_Venue')

    workbook  = writer.book
    worksheet = writer.sheets['Work_per_Venue']

    chart2 = workbook.add_chart({'type': 'column'})

    chart2.add_series({
        'categories': ['Work_per_Venue', 1, 0, len(venue_table.index), 0],
        'values': ['Work_per_Venue', 1, 1, len(venue_table.index), 1],
        'gap': 2,
    })

    chart2.set_y_axis({'major_gridlines': {'visible': False}})
    chart2.set_legend({'position': 'none'})
    chart2.set_x_axis({'name': 'Institution Location'})
    chart2.set_y_axis({'name': 'Number of Workshops', 'major_gridlines': {'visible': False}})
    chart2.set_title ({'name': 'Number of Workshops per Venue'})

    worksheet.insert_chart('D2', chart2)

def number_workshops_per_type(df,writer):
    """
    Create corresponding tables and graphs and write to the spreadsheet
    Number of workshops per Type
    """
    type_table = df.groupby(['tags']).size()

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

def number_workshops_per_venue_year(df,writer):
    """
    Create corresponding tables and graphs and write to the spreadsheet
    Number of Workshops per Venue and Year
    """
    venue_year_table = df.groupby(['venue','start']).size().to_frame()
    venue_year_table = venue_year_table.pivot_table(index='venue',columns = 'start')

    venue_year_table.to_excel(writer, sheet_name='Work_per_VenueYear')

    workbook  = writer.book
    worksheet = writer.sheets['Work_per_VenueYear']

    chart4 = workbook.add_chart({'type': 'column'})

    ranged = range(1,len(venue_year_table.columns)+1)

    for number in ranged:
        chart4.add_series({
            'name' : ['Work_per_VenueYear', 1, number],
            'categories': ['Work_per_VenueYear', 3, 0, len(venue_year_table.index)+2, 0],
            'values': ['Work_per_VenueYear', 3, number, len(venue_year_table.index)+2, number],
            'gap': 2,
        })

    chart4.set_y_axis({'major_gridlines': {'visible': False}})
    chart4.set_x_axis({'name': 'Institution Location'})
    chart4.set_y_axis({'name': 'Number of Workshops', 'major_gridlines': {'visible': False}})
    chart4.set_title ({'name': 'Number of Workshops per Venue and Year'})

    worksheet.insert_chart('I2', chart4)

def number_workshops_per_type_year(df,writer):
    """
    Create corresponding tables and graphs and write to the spreadsheet
    Number of workshops per Type and Year
    """
    type_year_table = df.groupby(['tags','start']).size().to_frame()
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

def number_attendees_per_year(df,writer):
    """
    Create corresponding tables and graphs and write to the spreadsheet
    Number of attendees per year
    """
    attendees_year_table = df.groupby(['start'])['number_of_attendees'].sum().to_frame()

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

def number_attendees_per_type(df,writer):
    """
    Create corresponding tables and graphs and write to the spreadsheet
    Number of attendees per type
    """
    attendees_type_table = df.groupby(['tags'])['number_of_attendees'].sum().to_frame()

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

def number_attendees_per_type_year(df,writer):
    """
    Create corresponding tables and graphs and write to the spreadsheet
    Number of attendees per type and year
    """
    type_year_attend_table = df.groupby(['tags','start'])['number_of_attendees'].sum().to_frame()
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

def create_ReadMe_tab(name_file,filename,writer):
    """
    Create the ReadMe tab in the spreadsheet
    """             
    dateExtract = name_file.split("_")
    textExtract = "Data in sheet " + filename + " was extracted on " + dateExtract[2] + " using Ruby script from https://github.com/softwaresaved/carpentry-workshops-instructors-extractor"
    textInfo = "It contains info on UK Carpentry workshop in that went ahead or will go ahead/are in planning as of the date it was run on."

    workbook  = writer.book
    worksheet = workbook.add_worksheet('ReadMe')
    worksheet.write(0, 0, textExtract)
    worksheet.write(2, 0, textInfo)

def save_spreadsheet(writer):
    writer.save()
    
def google_drive_authentication():
    """
    Authentication to the google drive account
    """
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    return drive

def google_drive_upload(excel_file,drive):
    """
    Upload spreadsheet resulting analysis spreadsheet to google drive
    """
    upload_excel = drive.CreateFile({'parents': [{'kind': 'drive#fileLink',
                                                  'id': '0B6P79ipNuR8EdDFraGgxMFJaaVE'}],
                                     'title': excel_file})
    upload_excel.SetContentFile(dirP + '/data/workshops/' + excel_file)
    upload_excel.Upload({'convert': True})

def google_drive_upload_non_anonymized(filename,dirP,name_file):
    """
    Upload non anonymized data to google drive
    """
    writerClear = pd.ExcelWriter(dirP + '/data/workshops/' + name_file + '.xlsx', engine='xlsxwriter')
    data_all = pd.read_csv(dirP + '/data/workshops/' + filename)
    data_all.to_excel(writerClear, sheet_name='Workshops_Data')
    writerClear.save()
    upload_data = drive.CreateFile({'parents': [{'kind': 'drive#fileLink',
                                                 'id': '0B6P79ipNuR8EdDFraGgxMFJaaVE'}],
                                    'title': filename})
    upload_data.SetContentFile(dirP + '/data/workshops/' + name_file + '.xlsx')
    upload_data.Upload({'convert': True})



def main():
    """
    Main function
    """
    data_workshops = load_data_without_personal_info(DATA,DIR_PATH)
    data_workshops = transform_start(data_workshops)
    data_workshops = transform_SWCWISE_SWC(data_workshops)

    excel_file = create_spreadsheet(NAME_FILE,DIR_PATH,data_workshops)[0]
    writer = create_spreadsheet(NAME_FILE,DIR_PATH,data_workshops)[1]

    number_workshops_per_year(data_workshops,writer)
    number_workshops_per_venue(data_workshops,writer)
    number_workshops_per_type(data_workshops,writer)
    number_workshops_per_venue_year(data_workshops,writer)
    number_workshops_per_type_year(data_workshops,writer)

    number_attendees_per_year(data_workshops,writer)
    number_attendees_per_type(data_workshops,writer)
    number_attendees_per_type_year(data_workshops,writer)

    print("Analysis Complete.")
    
    create_ReadMe_tab(NAME_FILE,DATA,writer)

    save_spreadsheet(writer)
    print("Spreadsheet Saved.")


##    drive = google_drive_authentication()
##    google_drive_upload(excel_file,drive)
##    print('Analysis spreadsheet uploaded to Google Drive.')
##    google_drive_upload_non_anonymized(DATA,DIR_PATH,NAME_FILE)
##    print('Non anonymized data uploaded to Google Drive.')

if __name__ == '__main__':
    main()

