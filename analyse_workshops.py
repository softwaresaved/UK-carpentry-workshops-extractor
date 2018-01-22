import os
import re
import pandas as pd
import numpy
import traceback
import json
import glob
import sys

sys.path.append('/lib')
import lib.helper as helper

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
WORKSHOP_DATA_DIR = CURRENT_DIR + '/data/workshops/'
WORKSHOP_TYPES = ["SWC", "DC", "TTT", "LC"]
VENUE_INSTITUTIONS_DICT_FILE = CURRENT_DIR + '/lib/venue_institution_dictionary.json'


def insert_year(df):
    """
    Extract the workshop year from the date in YYYY-MM-DD format found
    in the 'start' column and insert it in a new column 'year'.
    """
    idx = df.columns.get_loc('start')  # index of column 'start'
    workshop_years = pd.to_datetime(df['start']).dt.year  # get the year from the date in YYYY-MM-DD format
    df.insert(loc=idx + 2, column='year', value=workshop_years)  # insert to the right of the column 'start'
    return df


def insert_workshop_type(df):
    """
    Extract workshop type from workshop tags (in column 'tags') and insert it in a new column 'workshop_type'.
    """
    # Index of column 'tags' which contains a list tags for a workshop
    # (we are just looking to detect one of SWC, DC, LC or TTT)
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
            workshop_types.append('Unknown')

    df.insert(loc=idx + 1, column='workshop_type', value=workshop_types)  # insert to the right of the column 'tags'
    return df


def insert_workshop_institution(df):
    """
    Find workshop institution by looking it up workshop venue in a yaml file and insert it in a new column 'institution'.
    """
    # Index of column 'venue', right of which we want to insert the new column
    idx = df.columns.get_loc("venue")

    workshop_institutions_dict = json.load(open(VENUE_INSTITUTIONS_DICT_FILE))

    workshop_institutions = []
    for venue in df['venue']:
        institution = workshop_institutions_dict.get(venue.strip(), "Unknown")
        workshop_institutions.append(institution)
        if institution == "Unknown":
            print('For workshop venue "' + venue + '" we do not have the institution information. ' +
                  'Setting the institution to "Unknown" ...\n')

    df.insert(loc=idx + 1, column='institution',
              value=workshop_institutions)  # insert to the right of the column 'venue'
    return df


def workshops_per_year_analysis(df, writer):
    """
    Number of workshops per year - create the corresponding table and graphs and write to the spreadsheet.
    """
    workshops_per_year_table = pd.core.frame.DataFrame(
        {'number_of_workshops': df.groupby(['year']).size()}).reset_index()
    workshops_per_year_table.to_excel(writer, sheet_name='workshops_per_year', index=False)

    workbook = writer.book
    worksheet = writer.sheets['workshops_per_year']

    chart1 = workbook.add_chart({'type': 'column'})

    chart1.add_series({
        'categories': ['workshops_per_year', 1, 0, len(workshops_per_year_table.index), 0],
        'values': ['workshops_per_year', 1, 1, len(workshops_per_year_table.index), 1],
        'gap': 2,
    })

    chart1.set_y_axis({'major_gridlines': {'visible': False}})
    chart1.set_legend({'position': 'none'})
    chart1.set_x_axis({'name': 'Year'})
    chart1.set_y_axis({'name': 'Number of workshops', 'major_gridlines': {'visible': False}})
    chart1.set_title({'name': 'Number of workshops per year'})

    worksheet.insert_chart('I2', chart1)

    return workshops_per_year_table


def workshops_per_institution_analysis(df, writer):
    """
    Number of workshops per institution - create the corresponding table and graph and write to the spreadsheet.
    """
    # Remove rows with 'Unknown' value for the institution
    df = df[df.institution != 'Unknown']

    institution_table = pd.core.frame.DataFrame(
        {'number_of_workshops': df.groupby(['institution']).size().sort_values()}).reset_index()

    institution_table.to_excel(writer, sheet_name='workshops_per_institution', index=False)

    workbook = writer.book
    worksheet = writer.sheets['workshops_per_institution']

    chart = workbook.add_chart({'type': 'column'})

    chart.add_series({
        'categories': ['workshops_per_institution', 1, 0, len(institution_table.index), 0],
        'values': ['workshops_per_institution', 1, 1, len(institution_table.index), 1],
        'gap': 2,
    })

    chart.set_y_axis({'major_gridlines': {'visible': False}})
    chart.set_legend({'position': 'none'})
    chart.set_x_axis({'name': 'Institution'})
    chart.set_y_axis({'name': 'Number of workshops', 'major_gridlines': {'visible': False}})
    chart.set_title({'name': 'Number of workshops per institution'})

    worksheet.insert_chart('I2', chart)

    return institution_table


def workshop_types_analysis(df, writer):
    """
    Number of workshops of different type - create the corresponding table and graph and write to the spreadsheet.
    """
    workshop_types_table = pd.core.frame.DataFrame(
        {'number_of_workshops': df.groupby(['workshop_type']).size()}).reset_index()

    workshop_types_table.to_excel(writer, sheet_name='workshop_types', index=False)

    workbook = writer.book
    worksheet = writer.sheets['workshop_types']

    chart = workbook.add_chart({'type': 'column'})

    chart.add_series({
        'categories': ['workshop_types', 1, 0, len(workshop_types_table.index), 0],
        'values': ['workshop_types', 1, 1, len(workshop_types_table.index), 1],
        'gap': 2,
    })

    chart.set_y_axis({'major_gridlines': {'visible': False}})
    chart.set_legend({'position': 'none'})
    chart.set_x_axis({'name': 'Workshop type'})
    chart.set_y_axis({'name': 'Number of workshops', 'major_gridlines': {'visible': False}})
    chart.set_title({'name': 'Workshops types'})

    worksheet.insert_chart('I2', chart)

    return workshop_types_table


def workshops_per_institution_over_years_analysis(df, writer):
    """
    Number of workshops per institution over years - create the corresponding table and graph and write to the spreadsheet.
    """
    # Remove rows with 'Unknown' value for the institution
    df = df[df.institution != 'Unknown']

    institution_over_years_table = pd.core.frame.DataFrame(
        {'count': df.groupby(['institution', 'year']).size()}).reset_index()
    institution_over_years_table = institution_over_years_table.pivot_table(index='institution', columns='year')

    institution_over_years_table.to_excel(writer, sheet_name='workshops_per_institution_over_years')

    workbook = writer.book
    worksheet = writer.sheets['workshops_per_institution_over_years']

    chart = workbook.add_chart({'type': 'column'})

    ranged = range(1, len(institution_over_years_table.columns) + 1)

    for number in ranged:
        chart.add_series({
            'name': ['workshops_per_institution_over_years', 1, number],
            'categories': ['workshops_per_institution_over_years', 3, 0, len(institution_over_years_table.index) + 2,
                           0],
            'values': ['workshops_per_institution_over_years', 3, number, len(institution_over_years_table.index) + 2,
                       number],
            'gap': 2,
        })

    chart.set_y_axis({'major_gridlines': {'visible': False}})
    chart.set_x_axis({'name': 'Institution'})
    chart.set_y_axis({'name': 'Number of workshops', 'major_gridlines': {'visible': False}})
    chart.set_title({'name': 'Number of workshops per institution over years'})

    worksheet.insert_chart('I2', chart)

    return institution_over_years_table


def workshops_of_different_types_over_years_analysis(df, writer):
    """
    Number of workshops of different types over years - - create the corresponding table and graph and write to the spreadsheet.
    """
    workshop_types_over_years_table = pd.core.frame.DataFrame(
        {'number_of_workshops': df.groupby(['workshop_type', 'year']).size()}).reset_index()
    workshop_types_over_years_table = workshop_types_over_years_table.pivot_table(index='workshop_type', columns='year')

    workshop_types_over_years_table.to_excel(writer, sheet_name='different_ws_types_per_year')

    workbook = writer.book
    worksheet = writer.sheets['different_ws_types_per_year']

    chart = workbook.add_chart({'type': 'column'})

    ranged = range(1, len(workshop_types_over_years_table.columns) + 1)

    for number in ranged:
        chart.add_series({
            'name': ['different_ws_types_per_year', 1, number],
            'categories': ['different_ws_types_per_year', 3, 0, len(workshop_types_over_years_table.index) + 2, 0],
            'values': ['different_ws_types_per_year', 3, number, len(workshop_types_over_years_table.index) + 2,
                       number],
            'gap': 2,
        })

    chart.set_y_axis({'major_gridlines': {'visible': False}})
    chart.set_x_axis({'name': 'Workshop type'})
    chart.set_y_axis({'name': 'Number of workshops', 'major_gridlines': {'visible': False}})
    chart.set_title({'name': 'Number of workshops of different type over years'})

    worksheet.insert_chart('I2', chart)

    return workshop_types_over_years_table


def attendees_per_year_analysis(df, writer):
    """
    Number of workshop attendees per year - create the corresponding table and graph and write to the spreadsheet.
    """
    attendees_per_year_table = pd.core.frame.DataFrame(
        {'number_of_attendees': df.groupby(['year'])['number_of_attendees'].sum()}).reset_index()

    attendees_per_year_table.to_excel(writer, sheet_name='attendees_per_year', index=False)

    workbook = writer.book
    worksheet = writer.sheets['attendees_per_year']

    chart = workbook.add_chart({'type': 'column'})

    chart.add_series({
        'categories': ['attendees_per_year', 1, 0, len(attendees_per_year_table.index), 0],
        'values': ['attendees_per_year', 1, 1, len(attendees_per_year_table.index), 1],
        'gap': 2,
    })

    chart.set_y_axis({'major_gridlines': {'visible': False}})
    chart.set_legend({'position': 'none'})
    chart.set_x_axis({'name': 'Year'})
    chart.set_y_axis({'name': 'Number of attendees', 'major_gridlines': {'visible': False}})
    chart.set_title({'name': 'Number of attendees per year'})

    worksheet.insert_chart('I2', chart)

    return attendees_per_year_table


def attendees_per_workshop_type_analysis(df, writer):
    """
    Number of attendees for various workshop types - create the corresponding table and graph and write to the spreadsheet.
    """
    attendees_per_workshop_type_table = pd.core.frame.DataFrame(
        {'number_of_attendees': df.groupby(['workshop_type'])['number_of_attendees'].sum()}).reset_index()

    attendees_per_workshop_type_table.to_excel(writer, sheet_name='attendees_per_workshop_type', index=False)

    workbook = writer.book
    worksheet = writer.sheets['attendees_per_workshop_type']

    chart = workbook.add_chart({'type': 'column'})

    chart.add_series({
        'categories': ['attendees_per_workshop_type', 1, 0, len(attendees_per_workshop_type_table.index), 0],
        'values': ['attendees_per_workshop_type', 1, 1, len(attendees_per_workshop_type_table.index), 1],
        'gap': 2,
    })

    chart.set_y_axis({'major_gridlines': {'visible': False}})
    chart.set_legend({'position': 'none'})
    chart.set_x_axis({'name': 'Type of a workshop'})
    chart.set_y_axis({'name': 'Number of attendees', 'major_gridlines': {'visible': False}})
    chart.set_title({'name': 'Number of attendees per workshop type'})

    worksheet.insert_chart('I2', chart)

    return attendees_per_workshop_type_table


def attendees_per_workshop_type_over_years_analysis(df, writer):
    """
    Number of attendees per workshop type over years - create the corresponding table and graph and write to the spreadsheet.
    """
    attendees_per_workshop_type_over_years_table = df.groupby(['workshop_type', 'year'])[
        'number_of_attendees'].sum().to_frame()
    attendees_per_workshop_type_over_years_table = attendees_per_workshop_type_over_years_table.pivot_table(
        index='workshop_type', columns='year')

    attendees_per_workshop_type_over_years_table.to_excel(writer, sheet_name='attendees_ws_types_per_year')

    workbook = writer.book
    worksheet = writer.sheets['attendees_ws_types_per_year']

    chart = workbook.add_chart({'type': 'column'})

    for i in range(1, len(attendees_per_workshop_type_over_years_table.columns) + 1):
        chart.add_series({
            'name': ['attendees_ws_types_per_year', 1, i],
            'categories': ['attendees_ws_types_per_year', 3, 0,
                           len(attendees_per_workshop_type_over_years_table.index) + 2, 0],
            'values': ['attendees_ws_types_per_year', 3, i, len(attendees_per_workshop_type_over_years_table.index) + 2,
                       i],
            'gap': 2,
        })

    chart.set_y_axis({'major_gridlines': {'visible': False}})
    chart.set_x_axis({'name': 'Workshop type'})
    chart.set_y_axis({'name': 'Number of attendees', 'major_gridlines': {'visible': False}})
    chart.set_title({'name': 'Number of attendees for different workshop types over years'})

    worksheet.insert_chart('I2', chart)

    return attendees_per_workshop_type_over_years_table


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
        workshops_files.sort(key=os.path.getctime)  # order files by creation date

        if not workshops_files:
            print('No CSV file with Carpentry workshops found in ' + WORKSHOP_DATA_DIR + ". Exiting ...")
            sys.exit(1)
        else:
            workshops_file = workshops_files[-1] # get the last file

    workshops_file_name = os.path.basename(workshops_file)
    workshops_file_name_without_extension = re.sub('\.csv$', '', workshops_file_name.strip())

    print('CSV file with Carpentry workshops to analyse ' + workshops_file)

    try:
        workshops_df = helper.load_data_from_csv(workshops_file)
        workshops_df = insert_year(workshops_df)
        workshops_df = insert_workshop_type(workshops_df)
        workshops_df = insert_workshop_institution(workshops_df)
        workshops_df = helper.remove_stopped_workshops(workshops_df)

        print('Creating the analyses Excel spreadsheet ...')
        workshop_analyses_excel_file = WORKSHOP_DATA_DIR + 'analysed_' + workshops_file_name_without_extension + '.xlsx'
        excel_writer = helper.create_excel_analyses_spreadsheet(workshop_analyses_excel_file, workshops_df,
                                                                "carpentry_workshops")

        date = workshops_file_name_without_extension.split("_")  # Extract date from the file name in YYYY-MM-DD format
        helper.create_readme_tab(excel_writer,
                                 "Data in sheet 'carpentry_workshops' was extracted on " + date[
                                     2] + " using Ruby script from https://github.com/softwaresaved/carpentry-workshops-instructors-extractor. " \
                                          "It contains info on Carpentry workshops in a specified country (or all countries) recorded in the Carpentry's record keeping system AMY until the date it was extracted on. " \
                                          "Added columns include 'year', extracted from column 'start' containing workshop start date, and 'workshop_type', extracted from column 'tags'.")

        workshops_per_year_analysis(workshops_df, excel_writer)
        workshops_per_institution_analysis(workshops_df, excel_writer)
        workshop_types_analysis(workshops_df, excel_writer)
        workshops_of_different_types_over_years_analysis(workshops_df, excel_writer)

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
