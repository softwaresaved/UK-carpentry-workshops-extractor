import os
import re
import pandas as pd
import numpy as np
import sys
import traceback
import datetime
from ast import literal_eval

sys.path.append('/lib')
import lib.helper as helper

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = CURRENT_DIR + '/data'
RAW_DATA_DIR = DATA_DIR + '/raw'
ANALYSES_DIR = DATA_DIR + '/analyses'

YEARS = ['2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020']


def main():
    """
    Main function
    """
    args = helper.parse_command_line_parameters_analyses()

    instructors_file = args.input_file
    instructors_file_name = os.path.basename(instructors_file)
    instructors_file_name_without_extension = re.sub('\.csv$', '', instructors_file_name.strip())

    print('CSV file with Carpentry instructors to be analysed ' + instructors_file)

    try:
        instructors_df = pd.read_csv(instructors_file, encoding="utf-8")

        if not os.path.exists(ANALYSES_DIR):
            os.makedirs(ANALYSES_DIR)

        print('Creating the analyses Excel spreadsheet ...')
        if args.output_file:
            instructor_analyses_excel_file = args.output_file
        else:
            instructor_analyses_excel_file = ANALYSES_DIR + '/analysed_' + instructors_file_name_without_extension + '.xlsx'

        # Let's change type of some columns and do some conversions

        instructors_df.loc[~instructors_df['taught_workshops_per_year'].isnull(), ['taught_workshops_per_year']] = \
        instructors_df.loc[~instructors_df['taught_workshops_per_year'].isnull(), 'taught_workshops_per_year'].apply(
            lambda x: literal_eval(x))
        instructors_df.loc[instructors_df['taught_workshops_per_year'].isnull(), ['taught_workshops_per_year']] = \
        instructors_df.loc[instructors_df['taught_workshops_per_year'].isnull(), 'taught_workshops_per_year'].apply(
            lambda x: {})

        # Convert list of strings into list of dates for 'taught_workshop_dates' and 'earliest_badge_awarded'
        # columns (turn NaN into [])
        instructors_df['taught_workshop_dates'] = instructors_df['taught_workshop_dates'].str.split(',')
        instructors_df.loc[instructors_df['taught_workshop_dates'].isnull(), ['taught_workshop_dates']] = \
            instructors_df.loc[instructors_df['taught_workshop_dates'].isnull(), 'taught_workshop_dates'].apply(
                lambda x: [])
        instructors_df['taught_workshop_dates'] = instructors_df['taught_workshop_dates'].apply(
            lambda list_str: [datetime.datetime.strptime(date_str, '%Y-%m-%d').date() for date_str in list_str])

        # Convert list of strings into list of dates for ' ' column (turn NaN into [])
        instructors_df['taught_workshops'] = instructors_df['taught_workshops'].str.split(',')
        instructors_df.loc[instructors_df['taught_workshops'].isnull(), ['taught_workshops']] = instructors_df.loc[
            instructors_df['taught_workshops'].isnull(), 'taught_workshop_dates'].apply(lambda x: [])

        # Convert 'earliest_badge_awarded' column from strings to datetime
        instructors_df['earliest_badge_awarded'] = pd.to_datetime(instructors_df['earliest_badge_awarded'],
                                                                  format="%Y-%m-%d").apply(lambda x: x.date())

        # Get the date of the last taught workshop
        instructors_df['last_taught_workshop_date'] = instructors_df['taught_workshop_dates'].apply(
            lambda x: max(x) if (x != []) else None)

        # Extract column for each year containing number of workshops taught that year by instructor
        for year in YEARS:
            instructors_df[year] = instructors_df['taught_workshops_per_year'].apply(
                lambda x: x.get(int(year), 0))

        # Average number of workshop taught across all active years
        instructors_df['average_taught_workshops_per_year'] = instructors_df[YEARS].replace(0, np.nan).mean(axis=1)

        # Active and inactive instructors
        instructors_df['is_active'] = instructors_df['taught_workshop_dates'].apply(
            lambda x: is_active(x))

        excel_writer = helper.create_excel_analyses_spreadsheet(instructor_analyses_excel_file,instructors_df,
                                                                "carpentry_instructors")
        helper.create_readme_tab(excel_writer,
                                 "Data in sheet 'carpentry_instructors' contains Carpentry workshop data from " +
                                 instructor_analyses_excel_file + ". Analyses performed on " + datetime.datetime.now().strftime(
                                     "%Y-%m-%d %H:%M") +
                                 ".")

        instructors_per_year_analysis(instructors_df, excel_writer)
        instructors_per_country_analysis(instructors_df, excel_writer)
        instructors_per_institution_analysis(instructors_df, excel_writer)
        instructors_per_UK_region_analysis(instructors_df, excel_writer)
        active_instructors_analysis(instructors_df, excel_writer)
        excel_writer.save()
        print("Analyses of Carpentry instructors complete - results saved to " + instructor_analyses_excel_file + "\n")
    except Exception:
        print("An error occurred while creating workshop analyses Excel spreadsheet ...")
        print(traceback.format_exc())


def instructors_per_year_analysis(df, writer):
    """
    Number of instructors per year.
    """
    instructors_per_year = pd.core.frame.DataFrame(
        {'number_of_instructors': df.groupby(['year_earliest_badge_awarded']).size()}).reset_index()
    instructors_per_year.to_excel(writer,
                                  sheet_name='instructors_per_year',
                                  index=False)

    workbook = writer.book
    worksheet = writer.sheets['instructors_per_year']

    chart = workbook.add_chart({'type': 'column'})
    chart.add_series({
        'categories': ['instructors_per_year', 1, 0, len(instructors_per_year.index), 0],
        'values': ['instructors_per_year', 1, 1, len(instructors_per_year.index), 1],
        'gap': 2,
    })
    chart.set_y_axis({'major_gridlines': {'visible': False}})
    chart.set_legend({'position': 'none'})
    chart.set_x_axis({'name': 'Year'})
    chart.set_y_axis({'name': 'Number of instructors', 'major_gridlines': {'visible': False}})
    chart.set_title({'name': 'Number of instructors per year'})

    worksheet.insert_chart('I2', chart)

    return instructors_per_year


def instructors_per_institution_analysis(df, writer):
    """
    Number of instructors per institution (using normalised institution name).

    """
    instructors_per_institution = pd.core.frame.DataFrame(
        {'number_of_instructors': df.groupby(['normalised_institution']).size().sort_values()}).reset_index()
    instructors_per_institution.to_excel(writer,
                                         sheet_name='instructors_per_institution',
                                         index=False)

    workbook = writer.book
    worksheet = writer.sheets['instructors_per_institution']

    chart = workbook.add_chart({'type': 'column'})

    chart.add_series({
        'categories': ['instructors_per_institution', 1, 0, len(instructors_per_institution.index), 0],
        'values': ['instructors_per_institution', 1, 1, len(instructors_per_institution.index), 1],
        'gap': 2,
    })

    chart.set_y_axis({'major_gridlines': {'visible': False}})
    chart.set_legend({'position': 'none'})
    chart.set_x_axis({'name': 'Institution'})
    chart.set_y_axis({'name': 'Number of instructors', 'major_gridlines': {'visible': False}})
    chart.set_title({'name': 'Number of instructors per institution'})

    worksheet.insert_chart('D2', chart)

    return instructors_per_institution


def instructors_per_country_analysis(df, writer):
    """
    Number of instructors per country.
    """
    instructors_per_country = pd.core.frame.DataFrame(
        {'number_of_instructors': df.groupby(['country']).size()}).reset_index()
    instructors_per_country.to_excel(writer,
                                     sheet_name='instructors_per_country',
                                     index=False)

    workbook = writer.book
    worksheet = writer.sheets['instructors_per_country']

    chart = workbook.add_chart({'type': 'column'})
    chart.add_series({
        'categories': ['instructors_per_country', 1, 0, len(instructors_per_country.index), 0],
        'values': ['instructors_per_country', 1, 1, len(instructors_per_country.index), 1],
        'gap': 2,
    })
    chart.set_y_axis({'major_gridlines': {'visible': False}})
    chart.set_legend({'position': 'none'})
    chart.set_x_axis({'name': 'Year'})
    chart.set_y_axis({'name': 'Number of instructors', 'major_gridlines': {'visible': False}})
    chart.set_title({'name': 'Number of instructors per country'})

    worksheet.insert_chart('I2', chart)

    return instructors_per_country


def instructors_per_UK_region_analysis(df, writer):
    """
    Number of instructors per UK region.
    """
    instructors_per_UK_region = pd.core.frame.DataFrame(
        {'number_of_instructors': df.groupby(['region']).size().sort_values()}).reset_index()
    instructors_per_UK_region.to_excel(writer,
                                       sheet_name='instructors_per_region',
                                       index=False)

    workbook = writer.book
    worksheet = writer.sheets['instructors_per_region']

    chart = workbook.add_chart({'type': 'column'})

    chart.add_series({
        'categories': ['instructors_per_region', 1, 0, len(instructors_per_UK_region.index), 0],
        'values': ['instructors_per_region', 1, 1, len(instructors_per_UK_region.index), 1],
        'gap': 2,
    })

    chart.set_y_axis({'major_gridlines': {'visible': False}})
    chart.set_legend({'position': 'none'})
    chart.set_x_axis({'name': 'Region'})
    chart.set_y_axis({'name': 'Number of instructors', 'major_gridlines': {'visible': False}})
    chart.set_title({'name': 'Number of instructors per region'})

    worksheet.insert_chart('D2', chart)

    return instructors_per_UK_region


def is_active(taught_workshop_dates):
    """
    :param taught_workshop_dates: list of workshops taught by an instructor
    :return:
    """
    # Let's define active and inactive instructors
    # Active = taught in the past 2 years. Inactive = everyone else.
    if taught_workshop_dates == [] or (datetime.date.today() - max(taught_workshop_dates)).days > 712:
        return False
    else:
        return True


def active_instructors_analysis(df, writer):
    """
    Number of active vs inactive instructors.
    """
    # How many active and inactive instructors?
    active_vs_inactive = df['is_active'].value_counts()
    # print(active_vs_inactive)
    active_vs_inactive.index = ['inactive', 'active']
    active_vs_inactive.to_excel(writer,
                                sheet_name='active_vs_inactive',
                                index=True)

    workbook = writer.book
    worksheet = writer.sheets['active_vs_inactive']

    chart = workbook.add_chart({'type': 'column'})

    chart.add_series({
        'categories': ['active_vs_inactive', 1, 0, len(active_vs_inactive.index), 0],
        'values': ['active_vs_inactive', 1, 1, len(active_vs_inactive.index), 1],
        'gap': 2,
    })

    chart.set_y_axis({'major_gridlines': {'visible': False}})
    chart.set_legend({'position': 'none'})
    chart.set_x_axis({'name': 'active_vs_inactive'})
    chart.set_y_axis({'name': 'Number of instructors', 'major_gridlines': {'visible': False}})
    chart.set_title({'name': 'Number of active vs inactive instructors'})

    worksheet.insert_chart('D20', chart)

    # How many instructors taught 0 times?
    worksheet.write(0, 3, "How many instructors taught 0 times? " +
                    str(len(df[df['last_taught_workshop_date'].isnull()].index)))

    active = df[df['is_active']==True]
    inactive = df[df['is_active']==False]

    # Average number of workshops taught across all active years (for all instructors)
    worksheet.write(0, 3, "Average number of workshops taught across all active years (for all instructors): " +
                    str((df[YEARS].replace(0, np.NaN).mean(axis=0)).mean()))

    worksheet.write(2, 3, "Average number of workshops taught across all active years (for active instructors): " +
                     str((active[YEARS].replace(0, np.NaN).mean(axis=0)).mean()))

    worksheet.write(4, 3, "Average number of workshops taught across all active years (for inactive instructors): " +
                    str((inactive[YEARS].replace(0, np.NaN).mean(axis=0)).mean()))

    return df


if __name__ == '__main__':
    main()
