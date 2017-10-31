import os
import re
import pandas as pd
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


DIR_PATH = os.path.dirname(os.path.realpath(__file__))
findFile = [filename for filename in os.listdir(DIR_PATH + '/data/instructors')
            if filename.startswith("carpentry-instructors_") and filename.endswith('.csv')]
if not findFile:
  print('No file was found.')  
else:
    DATA = findFile[-1]
    NAME_FILE = re.sub('\.csv$', '', DATA.strip())

def load_data_without_personal_info(filename,dirP):
    """
    Loads data without personal information into a dataframe
    """                
    df = pd.read_csv(dirP + '/data/instructors/' + filename,
                               usecols=['country_code','nearest_airport_name',
                                        'nearest_airport_code', 'affiliation',
                                        'instructor-badges',
                                        'swc-instructor-badge-awarded',
                                        'dc-instructor-badge-awarded',
                                        'trainer-badge-awarded',
                                        'earliest-badge-awarded',
                                        'number_of_workshops_taught'])
    return pd.DataFrame(df)

def remove_null_values(df):
    """
    Removes null values for affiliation and country_code
    """ 
    df = df.dropna(subset=['country_code'])
    df = df.dropna(subset=['affiliation'])
    return df

def transform_earliest_badge_year(df):
    """
    Transform earliest-badge-awarded to just year
    """ 
    df['earliest-badge-awarded'] = pd.to_datetime(df['earliest-badge-awarded'])
    df['earliest-badge-awarded'] = df['earliest-badge-awarded'].dt.year
    return df    

def create_spreadsheet(name_file,dirP,df):
    """
    Create the spreadsheet to input resulting data analysis
    and put anonymized data in a spreadsheet tab
    """
    excel_file = 'analysis_' + name_file + '.xlsx'
    writer = pd.ExcelWriter(dirP + '/data/instructors/' + excel_file , engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Anonymized_Data')
    return excel_file, writer

def number_people_per_nearest_airport(df,writer):
    """
    Create corresponding tables and graphs and write to the spreadsheet
    Number of People per nearest_airport_code
    """
    city_table = df.groupby(['nearest_airport_code']).size()
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

def transform_airports_regions(dirP,df):
    """
    Transform the corresponding airport into their respective uk region
    in a new dataframe
    """
    regions_excel = pd.ExcelFile(dirP + './lib/UK-regions-airports.xlsx')
    regions = regions_excel.parse('UK-regions-airports')
    dict_Regions = area_dict = dict(zip(regions['Airport_code'],
                                    regions['UK_region']))
    data_instructors_region = df.copy()
    data_instructors_region['nearest_airport_code'].replace(dict_Regions, inplace=True)
    return data_instructors_region
    
def number_people_per_region(df,writer):
    """
    Create corresponding tables and graphs and write to the spreadsheet
    Number of People per region
    """
    region_table = df.groupby(['nearest_airport_code']).size()
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

def number_people_per_year(df,writer):
    """
    Create corresponding tables and graphs and write to the spreadsheet
    Number of people per year of earliest badge
    """
    year_table = df.groupby(['earliest-badge-awarded']).size()
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

def create_ReadMe_tab(name_file,filename,writer):
    """
    Create the ReadMe tab in the spreadsheet
    """             
    dateExtract = name_file.split("_")
    textExtract = "Data in sheet " + filename + " was extracted on " + dateExtract[2] + " using Ruby script from https://github.com/softwaresaved/carpentry-workshops-instructors-extractor"
    textInfo = "It contains info on certified Carpentry instructors in the UK."

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
    upload_excel.SetContentFile(dirP + '/data/instructors/' + excel_file)
    upload_excel.Upload({'convert': True})

def google_drive_upload_non_anonymized(filename,dirP,name_file):
    """
    Upload non anonymized data to google drive
    """
    writerClear = pd.ExcelWriter(dirP + '/data/instructors/' + name_file + '.xlsx', engine='xlsxwriter')
    data_all = pd.read_csv(dirP + '/data/instructors/' + filename)
    data_all.to_excel(writerClear, sheet_name='Instructors_Data')
    writerClear.save()
    upload_data = drive.CreateFile({'parents': [{'kind': 'drive#fileLink',
                                                 'id': '0B6P79ipNuR8EdDFraGgxMFJaaVE'}],
                                    'title': filename})
    upload_data.SetContentFile(dirP + '/data/instructors/' + name_file + '.xlsx')
    upload_data.Upload({'convert': True})

def main():
    """
    Main function
    """
    data_instructors = load_data_without_personal_info(DATA,DIR_PATH)
    data_instructors = remove_null_values(data_instructors)
    data_instructors = transform_earliest_badge_year(data_instructors)

    excel_file = create_spreadsheet(NAME_FILE,DIR_PATH,data_instructors)[0]
    writer = create_spreadsheet(NAME_FILE,DIR_PATH,data_instructors)[1]

    number_people_per_nearest_airport(data_instructors,writer)

    data_instructors_region = transform_airports_regions(DIR_PATH,data_instructors)
    number_people_per_region(data_instructors_region,writer)

    number_people_per_year(data_instructors_region,writer)

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
