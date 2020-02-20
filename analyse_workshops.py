import os
import re
import pandas as pd
import numpy as np
import traceback
import glob
import sys
import datetime

sys.path.append('/lib')
import lib.helper as helper

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = CURRENT_DIR + '/data'
RAW_DATA_DIR = DATA_DIR + '/raw'
ANALYSES_DIR = DATA_DIR + "/analyses"


def main():
    """
    Main function
    """
    args = helper.parse_command_line_parameters_analyses()

    if args.input_file:
        workshops_file = args.input_file
    else:
        print("Trying to locate the latest CSV spreadsheet with Carpentry workshops to analyse in " + RAW_DATA_DIR)
        workshops_files = glob.glob(RAW_DATA_DIR + "/carpentry-workshops_*.csv")
        workshops_files.sort(key=os.path.getctime)  # order files by creation date

        if not workshops_files:
            print("No CSV file with Carpentry workshops found in " + RAW_DATA_DIR + ". Exiting ...")
            sys.exit(1)
        else:
            workshops_file = workshops_files[-1]  # get the last file

    workshops_file_name = os.path.basename(workshops_file)
    workshops_file_name_without_extension = re.sub('\.csv$', '', workshops_file_name.strip())

    print("CSV spreadsheet with Carpentry workshops to be analysed: " + workshops_file + "\n")

    try:
        workshops_df = pd.read_csv(workshops_file, encoding="utf-8")
        workshops_df.drop(labels=[  # "contact",
            "tasks"], axis=1, inplace=True)
        idx = workshops_df.columns.get_loc("longitude")
        workshops_df.insert(loc=idx + 1, column='region',
                            value=workshops_df["longitude"])
        workshops_df['region'] = workshops_df.apply(
            lambda x: helper.get_uk_region(latitude=x['latitude'],
                                           longitude=x['longitude']), axis=1)
        if not os.path.exists(ANALYSES_DIR):
            os.makedirs(ANALYSES_DIR)

        print('Creating the analyses Excel spreadsheet ...')
        if args.output_file:
            workshop_analyses_excel_file = args.output_file
        else:
            workshop_analyses_excel_file = ANALYSES_DIR + '/analysed_' + workshops_file_name_without_extension + '.xlsx'

        excel_writer = helper.create_excel_analyses_spreadsheet(workshop_analyses_excel_file, workshops_df,"carpentry_workshops")

        helper.create_readme_tab(excel_writer,
                                 "Data in sheet 'carpentry_workshops' contains Carpentry workshop data from " +
                                 workshop_analyses_excel_file + ". Analyses performed on " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") +
                                 ".")

        workshops_per_year_analysis(workshops_df, excel_writer)
        workshops_per_type_analysis(workshops_df, excel_writer)
        workshops_per_type_per_year_analysis(workshops_df, excel_writer)

        workshops_per_host_analysis(workshops_df, excel_writer)
        workshops_per_host_per_year_analysis(workshops_df, excel_writer)

        attendance_per_year_analysis(workshops_df, excel_writer)
        attendance_per_type_analysis(workshops_df, excel_writer)
        attendance_per_type_per_year_analysis(workshops_df, excel_writer)

        workshops_per_UK_region_analysis(workshops_df, excel_writer)

        excel_writer.save()
        print("Analyses of Carpentry workshops complete - results saved to " + workshop_analyses_excel_file + "\n")
    except Exception:
        print ("An error occurred while creating workshop analyses Excel spreadsheet ...")
        print(traceback.format_exc())


def workshops_per_year_analysis(df, writer):
    """
    Number of workshops per year.
    """
    workshops_per_year = pd.core.frame.DataFrame(
        {'number_of_workshops': df.groupby(['year']).size()}).reset_index()
    workshops_per_year.to_excel(writer, sheet_name='workshops_per_year', index=False)

    workbook = writer.book
    worksheet = writer.sheets['workshops_per_year']

    chart1 = workbook.add_chart({'type': 'column'})

    chart1.add_series({
        'categories': ['workshops_per_year', 1, 0, len(workshops_per_year.index), 0],
        'values': ['workshops_per_year', 1, 1, len(workshops_per_year.index), 1],
        'gap': 2,
    })

    chart1.set_y_axis({'major_gridlines': {'visible': False}})
    chart1.set_legend({'position': 'none'})
    chart1.set_x_axis({'name': 'Year'})
    chart1.set_y_axis({'name': 'Number of workshops', 'major_gridlines': {'visible': False}})
    chart1.set_title({'name': 'Number of workshops per year'})

    worksheet.insert_chart('I2', chart1)

    return workshops_per_year


def workshops_per_type_analysis(df, writer):
    """
    Number of workshops of different type (SWC, DC, LC, TTT, Circuits).
    """
    workshops_per_type = pd.core.frame.DataFrame(
        {'number_of_workshops': df.groupby(['workshop_type']).size()}).reset_index()

    workshops_per_type.to_excel(writer, sheet_name='workshops_per_type', index=False)

    workbook = writer.book
    worksheet = writer.sheets['workshops_per_type']

    chart = workbook.add_chart({'type': 'column'})

    chart.add_series({
        'categories': ['workshops_per_type', 1, 0, len(workshops_per_type.index), 0],
        'values': ['workshops_per_type', 1, 1, len(workshops_per_type.index), 1],
        'gap': 2,
    })

    chart.set_y_axis({'major_gridlines': {'visible': False}})
    chart.set_legend({'position': 'none'})
    chart.set_x_axis({'name': 'Workshop type'})
    chart.set_y_axis({'name': 'Number of workshops', 'major_gridlines': {'visible': False}})
    chart.set_title({'name': 'Number of workshops of different types'})

    worksheet.insert_chart('I2', chart)

    return workshops_per_type


def workshops_per_type_per_year_analysis(df, writer):
    """
    Number of workshops of different types (SWC, DC, LC, TTT) over years.
    """
    workshops_per_type_per_year = pd.core.frame.DataFrame(
        {'number_of_workshops': df.groupby(['workshop_type', 'year']).size()}).reset_index()
    workshops_per_type_per_year_pivot = workshops_per_type_per_year.pivot_table(index='year', columns='workshop_type')

    workshops_per_type_per_year_pivot.to_excel(writer, sheet_name='workshops_per_type_per_year')

    workbook = writer.book
    worksheet = writer.sheets['workshops_per_type_per_year']

    chart = workbook.add_chart({'type': 'column', 'subtype': 'stacked'})

    for i in range(1, len(workshops_per_type_per_year_pivot.columns) + 1):
        chart.add_series({
            'name': ['workshops_per_type_per_year', 1, i],
            'categories': ['workshops_per_type_per_year', 3, 0, len(workshops_per_type_per_year_pivot.index) + 2, 0],
            'values': ['workshops_per_type_per_year', 3, i, len(workshops_per_type_per_year_pivot.index) + 2,
                       i],
            'gap': 2,
        })

    chart.set_y_axis({'major_gridlines': {'visible': False}})
    chart.set_x_axis({'name': 'Year'})
    chart.set_y_axis({'name': 'Number of workshops', 'major_gridlines': {'visible': False}})
    chart.set_title({'name': 'Number of workshops of different types over years'})

    worksheet.insert_chart('B20', chart)

    return workshops_per_type_per_year_pivot


def workshops_per_host_per_year_analysis(df, writer):
    """
    Number of workshops at different hosts over years.
    """
    # Remove rows with NaN value for the institution
    df = df.dropna(subset=['host_domain'])

    workshops_per_host_per_year = pd.core.frame.DataFrame(
        {'number_of_workshops': df.groupby(['host_domain', 'year']).size()}).reset_index()
    workshops_per_host_per_year_pivot = workshops_per_host_per_year.pivot_table(index='host_domain', columns='year')
    workshops_per_host_per_year_pivot = workshops_per_host_per_year_pivot.fillna(0).astype('int')

    workshops_per_host_per_year_pivot.to_excel(writer, sheet_name='workshops_per_host_per_year')

    workbook = writer.book
    worksheet = writer.sheets['workshops_per_host_per_year']

    chart = workbook.add_chart({'type': 'column', 'subtype': 'stacked'})

    for i in range(1, len(workshops_per_host_per_year_pivot.columns) + 1):
        chart.add_series({
            'name': ['workshops_per_host_per_year', 1, i],
            'categories': ['workshops_per_host_per_year', 3, 0, len(workshops_per_host_per_year_pivot.index) + 2, 0],
            'values': ['workshops_per_host_per_year', 3, i, len(workshops_per_host_per_year_pivot.index) + 2, i],
            'gap': 2,
        })

    chart.set_y_axis({'major_gridlines': {'visible': False}})
    chart.set_x_axis({'name': 'Year'})
    chart.set_y_axis({'name': 'Number of workshops', 'major_gridlines': {'visible': False}})
    chart.set_title({'name': 'Number of workshops at different hosts over years'})

    worksheet.insert_chart('N20', chart)

    return workshops_per_host_per_year_pivot


def workshops_per_host_analysis(df, writer):
    """
    Number of workshops per host.
    """

    # Remove rows with NaN value for the institution
    df = df.dropna(subset=['host_domain'])

    workshops_per_host = pd.core.frame.DataFrame(
        {'workshops_per_host': df.groupby(['host_domain']).size().sort_values()}).reset_index()

    workshops_per_host.to_excel(writer, sheet_name='workshops_per_host', index=False)

    workbook = writer.book
    worksheet = writer.sheets['workshops_per_host']

    chart = workbook.add_chart({'type': 'column'})

    chart.add_series({
        'categories': ['workshops_per_host', 1, 0, len(workshops_per_host.index), 0],
        'values': ['workshops_per_host', 1, 1, len(workshops_per_host.index), 1],
        'gap': 2,
    })

    chart.set_y_axis({'major_gridlines': {'visible': False}})
    chart.set_legend({'position': 'none'})
    chart.set_x_axis({'name': 'Host institution'})
    chart.set_y_axis({'name': 'Number of workshops', 'major_gridlines': {'visible': False}})
    chart.set_title({'name': 'Number of workshops per host institution'})

    worksheet.insert_chart('I2', chart)

    return workshops_per_host


def attendance_per_year_analysis(df, writer):
    """
    Number of workshop attendees per year.
    """
    # Calculate average attendance
    average_attendance = round(df[df["workshop_type"] != "TTT"]["attendance"].mean())
    # Adjust attendance with average where data is missing
    df["attendance"] = df["attendance"].fillna(average_attendance)

    attendance_per_year = pd.core.frame.DataFrame(
        {'number_of_attendees': df.groupby(['year'])['attendance'].sum()}).reset_index()

    attendance_per_year.to_excel(writer, sheet_name='attendance_per_year', index=False)

    workbook = writer.book
    worksheet = writer.sheets['attendance_per_year']

    chart = workbook.add_chart({'type': 'column'})

    chart.add_series({
        'categories': ['attendance_per_year', 1, 0, len(attendance_per_year.index), 0],
        'values': ['attendance_per_year', 1, 1, len(attendance_per_year.index), 1],
        'gap': 2,
    })

    chart.set_y_axis({'major_gridlines': {'visible': False}})
    chart.set_legend({'position': 'none'})
    chart.set_x_axis({'name': 'Year'})
    chart.set_y_axis({'name': 'Number of attendees', 'major_gridlines': {'visible': False}})
    chart.set_title({'name': 'Number of attendees per year (with estimates for missing data)'})

    worksheet.insert_chart('I2', chart)

    return attendance_per_year


def attendance_per_type_analysis(df, writer):
    """
    Number of attendees for various workshop types.
    """
    # Calculate average attendance
    average_attendance = round(df[df["workshop_type"] != "TTT"]["attendance"].mean())
    # Adjust attendance with average where data is missing
    df["attendance"] = df["attendance"].fillna(average_attendance)

    attendance_per_type = pd.core.frame.DataFrame(
        {'number_of_attendees': df.groupby(['workshop_type'])['attendance'].sum()}).reset_index()

    attendance_per_type.to_excel(writer, sheet_name='attendance_per_type', index=False)

    workbook = writer.book
    worksheet = writer.sheets['attendance_per_type']

    chart = workbook.add_chart({'type': 'column'})

    chart.add_series({
        'categories': ['attendance_per_type', 1, 0, len(attendance_per_type.index), 0],
        'values': ['attendance_per_type', 1, 1, len(attendance_per_type.index), 1],
        'gap': 2,
    })

    chart.set_y_axis({'major_gridlines': {'visible': False}})
    chart.set_legend({'position': 'none'})
    chart.set_x_axis({'name': 'Workshop type'})
    chart.set_y_axis({'name': 'Number of attendees', 'major_gridlines': {'visible': False}})
    chart.set_title({'name': 'Number of attendees per workshop type (with estimates for missing data)'})

    worksheet.insert_chart('I2', chart)

    return attendance_per_type


def attendance_per_type_per_year_analysis(df, writer):
    """
    Number of attendees per workshop type over years.
    """
    # Calculate average attendance
    average_attendance = round(df[df["workshop_type"] != "TTT"]["attendance"].mean())
    # Adjust attendance with average where data is missing
    df["attendance"] = df["attendance"].fillna(average_attendance)

    attendance_per_type_per_year = df.groupby(['year', 'workshop_type'])[
        'attendance'].sum().to_frame()
    attendance_per_type_per_year_pivot = attendance_per_type_per_year.pivot_table(
        index='year', columns='workshop_type')

    attendance_per_type_per_year_pivot.to_excel(writer, sheet_name='attendance_type_year')

    workbook = writer.book
    worksheet = writer.sheets['attendance_type_year']

    chart = workbook.add_chart({'type': 'column', 'subtype': 'stacked'})

    for i in range(1, len(attendance_per_type_per_year_pivot.columns) + 1):
        chart.add_series({
            'name': ['attendance_type_year', 1, i],
            'categories': ['attendance_type_year', 3, 0,
                           len(attendance_per_type_per_year_pivot.index) + 2, 0],
            'values': ['attendance_type_year', 3, i, len(attendance_per_type_per_year_pivot.index) + 2,
                       i],
            'gap': 2,
        })

    chart.set_y_axis({'major_gridlines': {'visible': False}})
    chart.set_x_axis({'name': 'Year'})
    chart.set_y_axis({'name': 'Number of attendees', 'major_gridlines': {'visible': False}})
    chart.set_title(
        {'name': 'Number of attendees for different workshop types over years (with estimates for missing data)'})

    worksheet.insert_chart('I2', chart)

    return attendance_per_type_per_year_pivot


def workshops_per_UK_region_analysis(df, writer):
    """
    Number of workshops per UK region.
    """
    workshops_per_UK_region = pd.core.frame.DataFrame(
        {'number_of_workshops': df.groupby(['region']).size().sort_values()}).reset_index()
    workshops_per_UK_region.to_excel(writer,
                                     sheet_name='workshops_per_region',
                                     index=False)

    workbook = writer.book
    worksheet = writer.sheets['workshops_per_region']

    chart = workbook.add_chart({'type': 'column'})

    chart.add_series({
        'categories': ['workshops_per_region', 1, 0, len(workshops_per_UK_region.index), 0],
        'values': ['workshops_per_region', 1, 1, len(workshops_per_UK_region.index), 1],
        'gap': 2,
    })

    chart.set_y_axis({'major_gridlines': {'visible': False}})
    chart.set_legend({'position': 'none'})
    chart.set_x_axis({'name': 'Region'})
    chart.set_y_axis({'name': 'Number of workshops', 'major_gridlines': {'visible': False}})
    chart.set_title({'name': 'Number of workshops per region'})

    worksheet.insert_chart('D2', chart)

    return workshops_per_UK_region


if __name__ == '__main__':
    main()
