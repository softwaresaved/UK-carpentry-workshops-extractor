import os
import re
import pandas as pd
import numpy
import traceback
import glob
import sys

sys.path.append('/lib')
import lib.helper as helper

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
WORKSHOP_DATA_DIR = CURRENT_DIR + '/data/workshops/'
WORKSHOP_TYPES = ["SWC", "DC", "TTT", "LC"]
STALLED_WORKSHOP_TYPES = ['stalled', 'cancelled', 'unresponsive']


def insert_start_year(df):
    """
    Insert the start year column using the date in the 'start' column in YYYY-MM-DD format
    """
    idx = df.columns.get_loc('start')  # index of column 'start'
    start_years = pd.to_datetime(df['start']).dt.year  # get the year from the date in YYYY-MM-DD format
    df.insert(loc=idx + 1, column='start_year', value=start_years)  # insert to the right of the column 'start'
    return df


def insert_workshop_type(df):
    """
    Extract workshop type from tags.
    """
    # index of column 'tags' which contains a list tags for a workshop (we are just looking to detect one of SWC, DC or TTT)
    idx = df.columns.get_loc("tags")

    df['tags'].apply(str)
    workshop_types = []
    for tag in df['tags']:
        if WORKSHOP_TYPES[0] in tag:
            workshop_types.append(WORKSHOP_TYPES[0])
        elif WORKSHOP_TYPES[1] in tag:
            workshop_types.append(WORKSHOP_TYPES[1])
        elif WORKSHOP_TYPES[2] in tag:
            workshop_types.append(WORKSHOP_TYPES[2])
        elif WORKSHOP_TYPES[3] in tag:
            workshop_types.append(WORKSHOP_TYPES[3])
        else:
            workshop_types.append('unkown')


    df.insert(loc=idx + 1, column='workshop_type', value=workshop_types)  # insert to the right of the column 'tags'
    return df


def workshop_years_analysis(df, writer):
    """
    Number of workshops per year - create corresponding tables and graphs and write to the spreadsheet.
    """
    workshops_per_year_table = pd.core.frame.DataFrame({'count': df.groupby(['start_year']).size()}).reset_index()

    workshops_per_year_table.to_excel(writer, sheet_name='workshops_per_year')

    workbook = writer.book
    worksheet = writer.sheets['workshops_per_year']

    chart1 = workbook.add_chart({'type': 'column'})

    chart1.add_series({
        'categories': ['workshops_per_year', 1, 1, len(workshops_per_year_table.index), 1],
        'values': ['workshops_per_year', 1, 2, len(workshops_per_year_table.index), 2],
        'gap': 2,
    })

    chart1.set_y_axis({'major_gridlines': {'visible': False}})
    chart1.set_legend({'position': 'none'})
    chart1.set_x_axis({'name': 'Year'})
    chart1.set_y_axis({'name': 'Number of workshops', 'major_gridlines': {'visible': False}})
    chart1.set_title({'name': 'Number of workshops per year'})

    worksheet.insert_chart('I2', chart1)

    return workshops_per_year_table


def workshops_venue_analysis(df, writer):
    """
    Number of workshops per venue - create corresponding tables and graphs and write to the spreadsheet.
    Unfortunately, this is analysis does not give the true per institution analysis as venues are different for the same institution.
    """
    venue_table = pd.core.frame.DataFrame({'count': df.groupby(['venue']).size()}).reset_index()

    venue_table.to_excel(writer, sheet_name='workshop_venues')

    workbook = writer.book
    worksheet = writer.sheets['workshop_venues']

    chart2 = workbook.add_chart({'type': 'column'})

    chart2.add_series({
        'categories': ['workshop_venues', 1, 1, len(venue_table.index), 1],
        'values': ['workshop_venues', 1, 2, len(venue_table.index), 2],
        'gap': 2,
    })

    chart2.set_y_axis({'major_gridlines': {'visible': False}})
    chart2.set_legend({'position': 'none'})
    chart2.set_x_axis({'name': 'Venue'})
    chart2.set_y_axis({'name': 'Number of workshops', 'major_gridlines': {'visible': False}})
    chart2.set_title({'name': 'Number of workshops per venue'})

    worksheet.insert_chart('I2', chart2)

    return venue_table


def workshops_type_analysis(df, writer):
    """
    Number of workshops of different types - create corresponding tables and graphs and write to the spreadsheet.
    """
    type_table = pd.core.frame.DataFrame({'count': df.groupby(['workshop_type']).size()}).reset_index()

    type_table.to_excel(writer, sheet_name='workshop_types')

    workbook = writer.book
    worksheet = writer.sheets['workshop_types']

    chart3 = workbook.add_chart({'type': 'column'})

    chart3.add_series({
        'categories': ['workshop_types', 1, 1, len(type_table.index), 1],
        'values': ['workshop_types', 1, 2, len(type_table.index), 2],
        'gap': 2,
    })

    chart3.set_y_axis({'major_gridlines': {'visible': False}})
    chart3.set_legend({'position': 'none'})
    chart3.set_x_axis({'name': 'Workshop type'})
    chart3.set_y_axis({'name': 'Number of workshops', 'major_gridlines': {'visible': False}})
    chart3.set_title({'name': 'Workshops types'})

    worksheet.insert_chart('I2', chart3)

    return type_table


def number_workshops_per_venue_year(df, writer):
    """
    Create corresponding tables and graphs and write to the spreadsheet
    Number of Workshops per Venue and Year
    """
    venue_year_table = pd.core.frame.DataFrame({'count': df.groupby(['venue', 'start_year']).size()}).reset_index()
    venue_year_table = venue_year_table.pivot_table(index='venue', columns='start_year')

    venue_year_table.to_excel(writer, sheet_name='Work_per_VenueYear')

    workbook = writer.book
    worksheet = writer.sheets['Work_per_VenueYear']

    chart4 = workbook.add_chart({'type': 'column'})

    ranged = range(1, len(venue_year_table.columns) + 1)

    for number in ranged:
        chart4.add_series({
            'name': ['Work_per_VenueYear', 1, number],
            'categories': ['Work_per_VenueYear', 3, 0, len(venue_year_table.index) + 2, 0],
            'values': ['Work_per_VenueYear', 3, number, len(venue_year_table.index) + 2, number],
            'gap': 2,
        })

    chart4.set_y_axis({'major_gridlines': {'visible': False}})
    chart4.set_x_axis({'name': 'Institution Location'})
    chart4.set_y_axis({'name': 'Number of Workshops', 'major_gridlines': {'visible': False}})
    chart4.set_title({'name': 'Number of Workshops per Venue and Year'})

    worksheet.insert_chart('I2', chart4)

    return venue_year_table


def number_workshops_per_type_year(df, writer):
    """
    Create corresponding tables and graphs and write to the spreadsheet
    Number of workshops per Type and Year
    """
    type_year_table = df.groupby(['tags', 'start_year']).size().to_frame()
    type_year_table = type_year_table.pivot_table(index='tags', columns='start_year')

    type_year_table.to_excel(writer, sheet_name='work_per_TypeYear')

    workbook = writer.book
    worksheet = writer.sheets['work_per_TypeYear']

    chart5 = workbook.add_chart({'type': 'column'})

    ranged = range(1, len(type_year_table.columns) + 1)

    for number in ranged:
        chart5.add_series({
            'name': ['work_per_TypeYear', 1, number],
            'categories': ['work_per_TypeYear', 3, 0, len(type_year_table.index) + 2, 0],
            'values': ['work_per_TypeYear', 3, number, len(type_year_table.index) + 2, number],
            'gap': 2,
        })

    chart5.set_y_axis({'major_gridlines': {'visible': False}})
    chart5.set_x_axis({'name': 'Type of Workshop'})
    chart5.set_y_axis({'name': 'Number of Workshops', 'major_gridlines': {'visible': False}})
    chart5.set_title({'name': 'Number of Workshops per Type per Year'})

    worksheet.insert_chart('I2', chart5)

    return type_year_table


def attendees_per_year_analysis(df, writer):
    """
    Number of attendees per year - create corresponding tables and graphs and write to the spreadsheet.
    """
    attendees_year_table = pd.core.frame.DataFrame(
        {'number_of_attendees': df.groupby(['start_year'])['number_of_attendees'].sum()}).reset_index()

    attendees_year_table.to_excel(writer, sheet_name='attendees_per_year')

    workbook = writer.book
    worksheet = writer.sheets['attendees_per_year']

    chart6 = workbook.add_chart({'type': 'column'})

    chart6.add_series({
        'categories': ['attendees_per_year', 1, 1, len(attendees_year_table.index), 1],
        'values': ['attendees_per_year', 1, 2, len(attendees_year_table.index), 2],
        'gap': 2,
    })

    chart6.set_y_axis({'major_gridlines': {'visible': False}})
    chart6.set_legend({'position': 'none'})
    chart6.set_x_axis({'name': 'Year'})
    chart6.set_y_axis({'name': 'Number of attendees', 'major_gridlines': {'visible': False}})
    chart6.set_title({'name': 'Number of attendees per year'})

    worksheet.insert_chart('I2', chart6)

    return attendees_year_table


def attendees_per_workshop_type_analysis(df, writer):
    """
    Number of attendees per for various workshop type - create corresponding tables and graphs and write to the spreadsheet.
    """
    attendees_type_table = df.groupby(['workshop_type'])['number_of_attendees'].sum().to_frame()

    attendees_type_table.to_excel(writer, sheet_name='attendees_per_workshop_type')

    workbook = writer.book
    worksheet = writer.sheets['attendees_per_workshop_type']

    chart7 = workbook.add_chart({'type': 'column'})

    ranged = range(1, len(attendees_type_table.columns) + 1)

    for number in ranged:
        chart7.add_series({
            'categories': ['attendees_per_workshop_type', 1, 0, len(attendees_type_table.index), 0],
            'values': ['attendees_per_workshop_type', 1, 1, len(attendees_type_table.index), 1],
            'gap': 2,
        })

    chart7.set_y_axis({'major_gridlines': {'visible': False}})
    chart7.set_legend({'position': 'none'})
    chart7.set_x_axis({'name': 'Type of a workshop'})
    chart7.set_y_axis({'name': 'Number of attendees', 'major_gridlines': {'visible': False}})
    chart7.set_title({'name': 'Number of attendees per workshop type'})

    worksheet.insert_chart('I2', chart7)

    return attendees_type_table


def attendees_per_workshop_type_over_years_analysis(df, writer):
    """
    Number of attendees per type over years - create corresponding tables and graphs and write to the spreadsheet.
    """
    type_year_attend_table = df.groupby(['workshop_type', 'start_year'])['number_of_attendees'].sum().to_frame()
    type_year_attend_table = type_year_attend_table.pivot_table(index='workshop_type', columns='start_year')

    type_year_attend_table.to_excel(writer, sheet_name='attendees_workshop_type_years')

    workbook = writer.book
    worksheet = writer.sheets['attendees_workshop_type_years']

    chart8 = workbook.add_chart({'type': 'column'})

    ranged = range(1, len(type_year_attend_table.columns) + 1)

    for number in ranged:
        chart8.add_series({
            'name': ['attendees_workshop_type_years', 1, number],
            'categories': ['attendees_workshop_type_years', 3, 0, len(type_year_attend_table.index) + 2, 0],
            'values': ['attendees_workshop_type_years', 3, number, len(type_year_attend_table.index) + 2, number],
            'gap': 2,
        })

    chart8.set_y_axis({'major_gridlines': {'visible': False}})
    chart8.set_x_axis({'name': 'Workshop type'})
    chart8.set_y_axis({'name': 'Number of attendees', 'major_gridlines': {'visible': False}})
    chart8.set_title({'name': 'Number of attendees per type over years'})

    worksheet.insert_chart('I2', chart8)

    return type_year_attend_table


def main():
    """
    Main function
    """
    args = helper.parse_command_line_paramters()

    if args.workshops_file:
        workshops_file = args.workshops_file
        print("The CSV spreadsheet with Carpentry workshops to be analysed: " + args.workshops_file)
    else:
        print("Trying to locate the latest CSV spreadsheet with Carpentry workshops to analyse in " + WORKSHOP_DATA_DIR)
        workshops_files = glob.glob(WORKSHOP_DATA_DIR + "carpentry-workshops_*.csv")
        workshops_files.sort(key=os.path.getctime)  # order by creation date

        if not workshops_files[-1]:  # get the last element
            print('No CSV file with Carpentry workshops found in ' + WORKSHOP_DATA_DIR + ". Exiting ...")
            sys.exit(1)
        else:
            workshops_file = workshops_files[-1]

    workshops_file_name = os.path.basename(workshops_file)
    workshops_file_name_without_extension = re.sub('\.csv$', '', workshops_file_name.strip())

    print('CSV file with Carpentry workshops to analyse ' + workshops_file)

    try:
        workshops_df = helper.load_data_from_csv(workshops_file)
        workshops_df = insert_start_year(workshops_df)
        workshops_df = insert_workshop_type(workshops_df)
        workshops_df = helper.remove_stalled_workshops(workshops_df,STALLED_WORKSHOP_TYPES)

        print('Creating the analyses Excel spreadsheet ...')
        workshop_analyses_excel_file = WORKSHOP_DATA_DIR + 'analysed_' + workshops_file_name_without_extension + '.xlsx'
        excel_writer = helper.create_excel_analyses_spreadsheet(workshop_analyses_excel_file, workshops_df, "carpentry_workshops")

        date = workshops_file_name_without_extension.split("_")  # Extract date from the file name in YYYY-MM-DD format
        helper.create_readme_tab(excel_writer,
                                 "Data in sheet 'carpentry_workshops' was extracted on " + date[
                                     2] + " using Ruby script from https://github.com/softwaresaved/carpentry-workshops-instructors-extractor. " \
                                          "It contains info on Carpentry workshops in a specified country (or all countries) recorded in the Carpentry's record keeping system AMY until the date it was extracted on. " \
                                          "Added columns include 'start_year', extracted from column 'start', and 'workshop_type', extracted from column 'tags'.")

        workshop_years_analysis(workshops_df, excel_writer)
        workshops_venue_analysis(workshops_df, excel_writer)
        workshops_type_analysis(workshops_df, excel_writer)
        ##number_workshops_per_venue_year(workshops_df, excel_writer)
        ##number_workshops_per_type_year(workshops_df, excel_writer)
        attendees_per_year_analysis(workshops_df, excel_writer)
        attendees_per_workshop_type_analysis(workshops_df, excel_writer)
        attendees_per_workshop_type_over_years_analysis(workshops_df, excel_writer)

        excel_writer.save()
        print("Analyses of Carpentry workshops complete - results saved to " + workshop_analyses_excel_file + "\n")
    except Exception:
        print ("An error occurred while creating the analyses Excel spreadsheet ...")
        print(traceback.format_exc())
    else:
        if args.google_drive_dir_id:
            try:
                print("Uploading workshops analyses to Google Drive ...")
                drive = helper.google_drive_authentication()

                parents_list = [{'kind': 'drive#fileLink', 'id': args.google_drive_dir_id}]

                helper.google_drive_upload(workshops_file, drive, parents_list, True)
                print(
                    'Original workshops CSV spreadsheet ' + workshops_file + ' uploaded to Google Drive into folder with ID: ' + args.google_drive_dir_id)

                helper.google_drive_upload(workshop_analyses_excel_file, drive, parents_list, True)
                print(
                    'Workshops analyses Excel spreadsheet ' + workshop_analyses_excel_file + ' uploaded to Google Drive into folder with ID: ' + args.google_drive_dir_id)
            except Exception:
                print ("An error occurred while uploading workshops analyses to Google Drive ...")
                print(traceback.format_exc())


if __name__ == '__main__':
    main()
