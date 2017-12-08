import os
import argparse
import json
import pandas as pd
import traceback
import gmaps
import yaml
import config
import glob
import re
import sys

sys.path.append('/lib')
import lib.helper as helper

from ipywidgets.embed import embed_minimal_html
import analyse_workshops as aw


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
WORKSHOP_DATA_DIR = CURRENT_DIR + '/data/workshops/'
UK_INSTITUTIONS_GEODATA_FILE = CURRENT_DIR + '/lib/UK-academic-institutions-geodata.xlsx'
WORKSHOPS_INSTITUTIONS_FILE = CURRENT_DIR + '/lib/workshop_institutions.yaml'
#GOOGLE_DRIVE_DIR_ID = "0B6P79ipNuR8EdDFraGgxMFJaaVE"


def workshops_per_institution(df):
    """
    Creates a dataframe with the values of the number of workshops
    per institution.
    """
    ## Removes 'Unkown' values from workshop_institution
    df = df[df.workshop_institution != 'Unkown']
    
    table = pd.core.frame.DataFrame({'count': df.groupby(['workshop_institution']).size()}).reset_index()
    return table

def generate_map(workshop_institution, workshop_coords_df, center):
    """
    Generates a map.
    """
    gmaps.configure(api_key=config.api_key)

    m = gmaps.Map()

    max_value = workshop_institution['count'].max()
    min_value = workshop_institution['count'].min()
    grouping = (max_value - min_value)/3
    second_value = min_value + grouping
    third_value = second_value + grouping

    names_small = []
    locations_small = []
    
    names_medium = []
    locations_medium = []

    names_large = []
    locations_large = []

    for index, row in workshop_institution.iterrows():
        long_coords = workshop_coords_df[workshop_coords_df['VIEW_NAME'] == row['workshop_institution']]['LONGITUDE']
        lat_coords = workshop_coords_df[workshop_coords_df['VIEW_NAME'] == row['workshop_institution']]['LATITUDE']
        if not long_coords.empty and not lat_coords.empty:
            if row['count']>=min_value and row['count']<second_value:
                locations_small.append((lat_coords.iloc[0],long_coords.iloc[0]))
                names_small.append(row['workshop_institution'] + ': ' + str(row['count']))
            elif row['count']>=second_value and row['count']<third_value:
                locations_medium.append((lat_coords.iloc[0],long_coords.iloc[0]))
                names_medium.append(row['workshop_institution'] + ': ' + str(row['count']))
            elif row['count']>=third_value and row['count']<=max_value:
                locations_large.append((lat_coords.iloc[0],long_coords.iloc[0]))
                names_large.append(row['workshop_institution'] + ': ' + str(row['count']))
        else:
            print('For institution "' + row['workshop_institution'] + '" we either have not got coordinates or it is not the official name of an UK '
                  'academic institution. Skipping it ...\n')

    symbol_layer_small = gmaps.symbol_layer(locations_small, fill_color="green", stroke_color="green",
                                      scale=3, hover_text=names_small)
    symbol_layer_medium = gmaps.symbol_layer(locations_medium, fill_color="green", stroke_color="green",
                                      scale=6, hover_text=names_medium)
    symbol_layer_large = gmaps.symbol_layer(locations_large, fill_color="green", stroke_color="green",
                                      scale=8, hover_text=names_large)
    m = gmaps.Map()
    m.add_layer(symbol_layer_small)
    m.add_layer(symbol_layer_medium)
    m.add_layer(symbol_layer_large)

    return m

def main():
    """
    Main function
    """
    args = helper.parse_command_line_paramters()
    print("Mapping workshop venue geocoordinates into clusters on an interactive map ...")

    if args.workshops_file:
        workshops_file = args.workshops_file
        print("The CSV spreadsheet with Carpentry workshops to be mapped: " + args.workshops_file)
    else:
        print("Trying to locate the latest CSV spreadsheet with Carpentry workshops to map in " + WORKSHOP_DATA_DIR)
        workshops_files = glob.glob(WORKSHOP_DATA_DIR + "carpentry-workshops_GB_*.csv")
        workshops_files.sort(key=os.path.getctime)  # order by creation date

        if not workshops_files[-1]:  # get the last element
            print('No CSV file with Carpentry workshops found in ' + WORKSHOP_DATA_DIR + ". Exiting ...")
            sys.exit(1)
        else:
            workshops_file = workshops_files[-1]

    workshops_file_name = os.path.basename(workshops_file)
    workshops_file_name_without_extension = re.sub('\.csv$', '', workshops_file_name.strip())
    print("The CSV spreadsheet with Carpentry workshops to be mapped: " + workshops_file)

    try:
        uk_academic_institutions_excel_file = pd.ExcelFile(UK_INSTITUTIONS_GEODATA_FILE)
        uk_academic_institutions_df = uk_academic_institutions_excel_file.parse('UK-academic-institutions')
    except:
        print ("An error occurred while reading the UK academic institutions' geodata file " + UK_INSTITUTIONS_GEODATA_FILE)
    else:
        try:
            df = helper.load_data_from_csv(workshops_file, ['venue', 'latitude', 'longitude'])
            print('Generating a map of workshop institutions ...')
            df = aw.insert_workshop_institution(df,WORKSHOPS_INSTITUTIONS_FILE)

            uk_academic_institutions_coords_df = uk_academic_institutions_df[['VIEW_NAME', 'LONGITUDE', 'LATITUDE']]
            all_uk_institutions_coords_df = uk_academic_institutions_coords_df.append(
                helper.get_UK_non_academic_institutions_coords())
            center = helper.get_center(all_uk_institutions_coords_df)
            
            workshops_per_institution_df = workshops_per_institution(df)

            maps = generate_map(workshops_per_institution_df,all_uk_institutions_coords_df,center)

            ## Save map to a HTML file
            html_map_file = WORKSHOP_DATA_DIR + 'map_workshop_institution_' + workshops_file_name_without_extension + '.html'
            embed_minimal_html(html_map_file, views=[maps])
            print('Map of workshop institutions saved to HTML file ' + html_map_file + '\n')

        except:
            print ("An error occurred while creating the map of workshop institutions  ...")
            print(traceback.format_exc())
        else:
            if args.google_drive_dir_id:
                try:
                    print("Uploading workshop institutions map to Google Drive " + html_map_file)
                    drive = helper.google_drive_authentication()
                    helper.google_drive_upload(html_map_file,
                                               drive,
                                               [{'mimeType': 'text/plain', 'id': args.google_drive_dir_id}],
                                               False)
                    print('Map uploaded to Google Drive.')
                except Exception:
                    print ("An error occurred while uploading the map to Google Drive ...")
                    print(traceback.format_exc())


if __name__ == '__main__':
    main()
