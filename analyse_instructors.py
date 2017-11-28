import os
import re
import pandas as pd
import sys
import glob
import traceback

sys.path.append('/lib')
import lib.helper as helper

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
INSTRUCTOR_DATA_DIR = CURRENT_DIR + '/data/instructors/'
UK_AIRPORTS_REGIONS_FILE = CURRENT_DIR + '/lib/UK-regions-airports.xlsx'

def insert_earliest_badge_year(df):
    """
    Insert the earliest-badge-awarded-year column using the date in the 'earliest-badge-awarded' column in YYYY-MM-DD format
    """
    idx = df.columns.get_loc('earliest-badge-awarded') # index of column 'earliest-badge-awarded'
    earliest_badge_awarded_years = pd.to_datetime(df['earliest-badge-awarded']).dt.year # get the year from the date in YYYY-MM-DD format
    df.insert(loc=idx + 1, column='earliest-badge-awarded-year', value=earliest_badge_awarded_years) # insert to the right of the column 'earliest-badge-awarded'
    return df

def insert_airport_region(df):
    """
    Insert the new column that corresponds to the UK region for the nearest_airport.
    """
    regions_excel_file = pd.ExcelFile(UK_AIRPORTS_REGIONS_FILE)
    regions = regions_excel_file.parse('UK-regions-airports')
    airports_regions_dict = dict(zip(regions['Airport_code'],
                                    regions['UK_region']))

    idx = df.columns.get_loc('nearest_airport_code') # index of column 'nearest_airport_code'
    df.insert(loc=idx + 1, column='nearest_airport_UK_region', value=df.nearest_airport_code) # copy values from 'nearest_airport_code' column and insert to the right of the column 'nearest_airport_code'
    df['nearest_airport_UK_region'].replace(airports_regions_dict, inplace=True) # replace the airport with its UK region
    return df

def instructors_nearest_airport_analysis(df, writer):
    """
    Number of people per nearest_airport_code - create the corresponding table and graph and write to the spreadsheet.
    """
    city_table = pd.core.frame.DataFrame({'count': df.groupby(['nearest_airport_name']).size()}).reset_index()
    city_table.to_excel(writer, sheet_name='instructors_airports', index = False)

    workbook  = writer.book
    worksheet = writer.sheets['instructors_airports']

    chart1 = workbook.add_chart({'type': 'column'})

    chart1.add_series({
        'categories': ['instructors_airports', 1, 0, len(city_table.index), 0],
        'values': ['instructors_airports', 1, 1, len(city_table.index), 1],
        'gap': 2,
    })

    chart1.set_y_axis({'major_gridlines': {'visible': False}})
    chart1.set_legend({'position': 'none'})
    chart1.set_x_axis({'name': 'Nearest airport (code)'})
    chart1.set_y_axis({'name': 'Number of instructors', 'major_gridlines': {'visible': False}})
    chart1.set_title ({'name': 'Instructors per (nearest) airport'})

    worksheet.insert_chart('D2', chart1)

    return city_table
    
def instructors_per_UK_region_analysis(df, writer):
    """
    Number of instructors per UK region - create corresponding tables and graphs and write to the spreadsheet.
    """
    region_table = pd.core.frame.DataFrame({'count': df.groupby(['nearest_airport_UK_region']).size()}).reset_index()
    region_table.to_excel(writer, sheet_name='instructors_per_region', index = False)

    workbook  = writer.book
    worksheet = writer.sheets['instructors_per_region']

    chart2 = workbook.add_chart({'type': 'column'})

    chart2.add_series({
        'categories': ['instructors_per_region', 1, 0, len(region_table.index), 0],
        'values': ['instructors_per_region', 1, 1, len(region_table.index), 1],
        'gap': 2,
    })

    chart2.set_y_axis({'major_gridlines': {'visible': False}})
    chart2.set_legend({'position': 'none'})
    chart2.set_x_axis({'name': 'Region of the UK'})
    chart2.set_y_axis({'name': 'Number of instructors', 'major_gridlines': {'visible': False}})
    chart2.set_title ({'name': 'Number of instructors per UK region'})

    worksheet.insert_chart('D2', chart2)

    return region_table

def instructors_per_year_analysis(df, writer):
    """
    Number of instructors over years - create corresponding tables and graphs and write to the spreadsheet.
    """
    year_table = pd.core.frame.DataFrame({'count': df.groupby(['earliest-badge-awarded-year']).size()}).reset_index()
    year_table.to_excel(writer, sheet_name='instructors_per_year', index = False)

    workbook  = writer.book
    worksheet = writer.sheets['instructors_per_year']

    chart3 = workbook.add_chart({'type': 'column'})

    chart3.add_series({
        'categories': ['instructors_per_year', 1, 0, len(year_table.index), 0],
        'values': ['instructors_per_year', 1, 1, len(year_table.index), 1],
        'gap': 2,
    })

    chart3.set_y_axis({'major_gridlines': {'visible': False}})
    chart3.set_legend({'position': 'none'})
    chart3.set_x_axis({'name': 'Year'})
    chart3.set_y_axis({'name': 'Number of instructors', 'major_gridlines': {'visible': False}})
    chart3.set_title ({'name': 'Number of instructors per year'})

    worksheet.insert_chart('D2', chart3)

    return year_table


def main():
    """
    Main function
    """
    args = helper.parse_command_line_paramters()

    if args.instructors_file:
        instructors_file = args.instructors_file
        print("The CSV spreadsheet with Carpentry instructors to be analysed: " + args.instructors_file)
    else:
        print("Trying to locate the latest CSV spreadsheet with Carpentry instructors to analyse in " + INSTRUCTOR_DATA_DIR)
        instructors_files = glob.glob(INSTRUCTOR_DATA_DIR + "carpentry-instructors_*.csv")
        instructors_files.sort(key=os.path.getctime) # order by creation date

        if not instructors_files[-1]: # get the last element
            print('No CSV file with Carpentry instructors found in ' + INSTRUCTOR_DATA_DIR + ". Exiting ...")
            sys.exit(1)
        else:
            instructors_file = instructors_files[-1]

    instructors_file_name = os.path.basename(instructors_file)
    instructors_file_name_without_extension = re.sub('\.csv$', '', instructors_file_name.strip())

    print('CSV file with carpentry instructors to analyse ' + instructors_file)

    try:
        instructors_df = helper.load_data_from_csv(instructors_file, ['country_code','nearest_airport_name',
                                        'nearest_airport_code', 'affiliation',
                                        'instructor-badges',
                                        'swc-instructor-badge-awarded',
                                        'dc-instructor-badge-awarded',
                                        'trainer-badge-awarded',
                                        'earliest-badge-awarded',
                                        'number_of_workshops_taught']) # anonymise - do not load emails or names or any other personal data
        instructors_df = helper.drop_null_values_from_columns(instructors_df, ['country_code', 'affiliation'])
        instructors_df = insert_earliest_badge_year(instructors_df)
        instructors_df = insert_airport_region(instructors_df)

        print('Creating the analyses Excel spreadsheet ...')
        instructors_analyses_excel_file = INSTRUCTOR_DATA_DIR + 'analysed_' + instructors_file_name_without_extension + '.xlsx'
        excel_writer = helper.create_excel_analyses_spreadsheet(instructors_analyses_excel_file, instructors_df, "carpentry_instructors")

        date = instructors_file_name_without_extension.split("_")  # Extract date from the file name in YYYY-MM-DD format
        helper.create_readme_tab(excel_writer, "Data in sheet 'carpentry_instructors' was extracted on " + date[
        2] + " using Ruby script from https://github.com/softwaresaved/carpentry-workshops-instructors-extractor. " \
             "It contains info on Carpentry instructors in a specified country (or all countries) recorded in the Carpentry's record keeping system AMY until the date it was extracted on. " \
            "Data has been anomimised (email and name info excluded) and " \
             +   "a new column 'earliest-badge-awarded-year' was added, which contains extracted year from column 'earliest-badge-awarded'.")

        instructors_nearest_airport_analysis(instructors_df, excel_writer)
        instructors_per_UK_region_analysis(instructors_df, excel_writer)
        instructors_per_year_analysis(instructors_df, excel_writer)

        excel_writer.save()
        print("Analyses of Carpentry instructors complete - results saved to " + instructors_analyses_excel_file + "\n")
    except Exception:
        print ("An error occurred while creating the analyses Excel spreadsheet ...")
        print(traceback.format_exc())
    else:
        if args.google_drive_dir_id:
            try:
                print("Uploading instructors analyses to Google Drive ...")
                drive = helper.google_drive_authentication()

                parents_list = [{'kind': 'drive#fileLink', 'id': args.google_drive_dir_id}]

                helper.google_drive_upload(instructors_file, drive, parents_list, True)
                print('Original instructors CSV spreadsheet ' + instructors_file + ' uploaded to Google Drive into folder with ID: ' + args.google_drive_dir_id)

                helper.google_drive_upload(instructors_analyses_excel_file, drive, parents_list, True)
                print('Instructor analyses Excel spreadsheet ' + instructors_analyses_excel_file + ' uploaded to Google Drive into folder with ID: ' + args.google_drive_dir_id)
            except Exception:
                print ("An error occurred while uploading instructor analyses to Google Drive ...")
                print(traceback.format_exc())


if __name__ == '__main__':
    main()
