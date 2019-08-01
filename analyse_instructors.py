import os
import re
import pandas as pd
import sys
import glob
import traceback

sys.path.append('/lib')
import lib.helper as helper

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = CURRENT_DIR + '/data'
RAW_DATA_DIR = DATA_DIR + '/raw'
ANALYSES_DIR = DATA_DIR + '/analyses'

UK_AIRPORTS_REGIONS_FILE = CURRENT_DIR + '/lib/UK-airports_regions.csv'


def main():
    """
    Main function
    """
    args = helper.parse_command_line_parameters(["-i"])

    if args.instructors_file:
        instructors_file = args.instructors_file
        print("The CSV spreadsheet with Carpentry instructors to be analysed: " + args.instructors_file)
    else:
        print("Trying to locate the latest CSV spreadsheet with Carpentry instructors to analyse in " + RAW_DATA_DIR)
        instructors_files = glob.glob(RAW_DATA_DIR + "/carpentry-instructors_*.csv")
        instructors_files.sort(key=os.path.getctime)  # order files by creation date

        if not instructors_files:
            print('No CSV file with Carpentry instructors found in ' + RAW_DATA_DIR + ". Exiting ...")
            sys.exit(1)
        else:
            instructors_file = instructors_files[-1]  # get the last file

    instructors_file_name = os.path.basename(instructors_file)
    instructors_file_name_without_extension = re.sub('\.csv$', '', instructors_file_name.strip())

    print('CSV file with Carpentry instructors to analyse ' + instructors_file)

    try:
        instructors_df = pd.read_csv(instructors_file, encoding="utf-8")
        instructors_df.drop(labels="email", axis=1, inplace=True)

        # Insert normalised/official names for institutions (for UK academic institutions)
        instructors_df = helper.insert_normalised_institution(instructors_df, "affiliation")

        # Insert latitude, longitude pairs for instructors' institutions
        instructors_df = helper.insert_institutional_geocoordinates(instructors_df)

        # Insert UK regional info based on instructors's affiliations or nearest airport
        instructors_df = helper.insert_uk_region(instructors_df)

        if not os.path.exists(ANALYSES_DIR):
            os.makedirs(ANALYSES_DIR)

        print('Creating the analyses Excel spreadsheet ...')
        instructor_analyses_excel_file = ANALYSES_DIR + '/analysed_' + instructors_file_name_without_extension + '.xlsx'
        excel_writer = helper.create_excel_analyses_spreadsheet(instructor_analyses_excel_file, instructors_df,
                                                                "carpentry_instructors")

        date = instructors_file_name_without_extension.split(
            "_")  # Extract date from the file name in YYYY-MM-DD format
        helper.create_readme_tab(excel_writer,
                                 "Data in sheet 'carpentry_instructors' contains Carpentry instructor data recorded in AMY extracted on " +
                                 date[
                                     2] + " using amy_data_extract.py script from https://github.com/softwaresaved/carpentry-workshops-instructors-extractor. Contact details have been removed.")

        instructors_per_year_analysis(instructors_df, excel_writer)
        instructors_per_country_analysis(instructors_df, excel_writer)
        instructors_per_institution_analysis(instructors_df, excel_writer)
        instructors_per_UK_region_analysis(instructors_df, excel_writer)

        excel_writer.save()
        print("Analyses of Carpentry instructors complete - results saved to " + instructor_analyses_excel_file + "\n")
    except Exception:
        print ("An error occurred while creating workshop analyses Excel spreadsheet ...")
        print(traceback.format_exc())


def instructors_per_year_analysis(df, writer):
    """
    Number of instructors per year.
    """
    instructors_per_year = pd.core.frame.DataFrame(
        {'number_of_instructors': df.groupby(['year-earliest-instructor-badge-awarded']).size()}).reset_index()
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
        {'number_of_instructors': df.groupby(['normalised_institution_name']).size().sort_values()}).reset_index()
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


if __name__ == '__main__':
    main()
