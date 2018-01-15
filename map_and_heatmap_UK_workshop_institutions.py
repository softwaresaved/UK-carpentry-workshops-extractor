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
WORKSHOPS_INSTITUTIONS_FILE = CURRENT_DIR + '/lib/workshop_institutions.yml'


# GOOGLE_DRIVE_DIR_ID = "0B6P79ipNuR8EdDFraGgxMFJaaVE"


def main():
    """
    Main function
    """
    args = helper.parse_command_line_paramters()
    print("Mapping workshop institution geocoordinates (extracted by cross-referencing workshop venue with its institution) into clusters on an interactive map ...\n")

    print("Note: this map only makes sense to generate with workshops in the UK as it cross references their institutions with geocoordinates of UK institutions.\n")

    if args.workshops_file:
        workshops_file = args.workshops_file
        print("The CSV spreadsheet with Carpentry workshops to be mapped: " + args.workshops_file)
    else:
        print("Trying to locate the latest CSV spreadsheet with Carpentry workshops to map in " + WORKSHOP_DATA_DIR)
        workshops_files = glob.glob(WORKSHOP_DATA_DIR + "carpentry-workshops_GB_*.csv")
        workshops_files.sort(key=os.path.getctime)  # order by creation date

        if not workshops_files:
            print('No CSV file with Carpentry workshops found in ' + WORKSHOP_DATA_DIR + ". Exiting ...")
            sys.exit(1)
        else:
            workshops_file = workshops_files[-1] # get the last element

    workshops_file_name = os.path.basename(workshops_file)
    workshops_file_name_without_extension = re.sub('\.csv$', '', workshops_file_name.strip())
    print("The CSV spreadsheet with Carpentry workshops to be mapped: " + workshops_file + "\n")

    try:
        uk_academic_institutions_excel_file = pd.ExcelFile(UK_INSTITUTIONS_GEODATA_FILE)
        uk_academic_institutions_df = uk_academic_institutions_excel_file.parse('UK-academic-institutions')
    except:
        print (
        "An error occurred while reading the UK academic institutions' geodata file " + UK_INSTITUTIONS_GEODATA_FILE)
    else:
        try:
            df = helper.load_data_from_csv(workshops_file, ['venue', 'latitude', 'longitude'])
            print('Generating a map and a heatmap of workshop institutions ...\n')
            df = aw.insert_workshop_institution(df)

            uk_academic_institutions_coords_df = uk_academic_institutions_df[['VIEW_NAME', 'LONGITUDE', 'LATITUDE']]
            all_uk_institutions_coords_df = uk_academic_institutions_coords_df.append(
                helper.get_UK_non_academic_institutions_coords())

            # Remove 'Unknown' values from 'institution' column
            df = df[df.institution != 'Unknown']
            workshops_institutions_df = pd.core.frame.DataFrame({'count': df.groupby(['institution']).size()}).reset_index()
            workshops_institutions_df = helper.insert_institutions_geocoordinates(workshops_institutions_df, all_uk_institutions_coords_df)

            print(df)
            map = helper.generate_gmap_map_with_circular_markers(workshops_institutions_df)
            heatmap = helper.generate_heatmap(df)

            ## Save map to a HTML file
            html_map_file = WORKSHOP_DATA_DIR + 'map_workshop_institutions_' + workshops_file_name_without_extension + '.html'
            embed_minimal_html(html_map_file, views=[map])
            print('Map of workshop institutions saved to HTML file ' + html_map_file + '\n')

            html_heatmap_file = WORKSHOP_DATA_DIR + 'heatmap_workshop_institutions_' + workshops_file_name_without_extension + '.html'
            embed_minimal_html(html_heatmap_file, views=[heatmap])
            print('Heatmap of workshop institutions saved to HTML file ' + html_heatmap_file + '\n')

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
