import os
import argparse
import folium
import pandas as pd
import traceback
import gmaps
import config
import glob
import re
import sys

sys.path.append('/lib')
import lib.helper as helper

from ipywidgets.embed import embed_minimal_html


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
INSTRUCTORS_DATA_DIR = CURRENT_DIR + '/data/instructors/'
UK_INSTITUTIONS_GEODATA_FILE = CURRENT_DIR + '/lib/UK-academic-institutions-geodata.xlsx'


def main():
    """
    Main function
    """
    args = helper.parse_command_line_paramters()
    print("Mapping instructors affiliation geocoordinates on an interactive map and a heatmap ...\n")
    print("Note: this map only makes sense to generate with instructors in the UK as it cross references their affiliations with geocoordinates of UK institutions.\n")

    if args.instructors_file:
        instructors_file = args.instructors_file
        print("The CSV spreadsheet with Carpentry instructors to be mapped: " + args.instructors_file)
    else:
        print("Trying to locate the latest CSV spreadsheet with Carpentry instructors to map in " + INSTRUCTORS_DATA_DIR + "\n")
        instructors_files = glob.glob(INSTRUCTORS_DATA_DIR + "carpentry-instructors_GB_*.csv")
        instructors_files.sort(key=os.path.getctime)  # order by creation date

        if not instructors_files[-1]:  # get the last element
            print('No CSV file with Carpentry instructors found in ' + INSTRUCTORS_DATA_DIR + ". Exiting ...")
            sys.exit(1)
        else:
            instructors_file = instructors_files[-1]

    instructors_file_name = os.path.basename(instructors_file)
    instructors_file_name_without_extension = re.sub('\.csv$', '', instructors_file_name.strip())
    print('CSV file with Carpentry instructors to analyse ' + instructors_file_name)

    try:
        uk_academic_institutions_excel_file = pd.ExcelFile(UK_INSTITUTIONS_GEODATA_FILE)
        uk_academic_institutions_df = uk_academic_institutions_excel_file.parse('UK-academic-institutions')
    except:
        print (
            "An error occurred while reading the UK academic institutions' geodata file " + UK_INSTITUTIONS_GEODATA_FILE)
    else:
        try:
            df = helper.load_data_from_csv(instructors_file, ['affiliation'])
            # Rename 'affiliation' column to 'institution'
            df.rename(columns={'affiliation': 'institution'}, inplace=True)

            print("Generating a map and a heatmap of instructors' affiliations ...\n")
            df = helper.drop_null_values_from_columns(df, ['institution'])
            df = helper.fix_UK_academic_institutions_names(df)

            uk_academic_institutions_coords_df = uk_academic_institutions_df[['VIEW_NAME', 'LONGITUDE', 'LATITUDE']]
            all_uk_institutions_coords_df = uk_academic_institutions_coords_df.append(
                helper.get_UK_non_academic_institutions_coords())

            df = helper.insert_institutions_geocoordinates(df, all_uk_institutions_coords_df)

            instructors_institutions_df = pd.core.frame.DataFrame({'count': df.groupby(['institution']).size()}).reset_index()
            instructors_institutions_df = helper.insert_institutions_geocoordinates(instructors_institutions_df, all_uk_institutions_coords_df)

            print(df)
            map = helper.generate_circles_map(instructors_institutions_df)
            heatmap = helper.generate_heatmap(df)

            # Save maps to HTML files
            map_file = INSTRUCTORS_DATA_DIR + 'map_instructors_affiliations_' + instructors_file_name_without_extension + '.html'
            embed_minimal_html(map_file, views=[map])
            print("Map of instructors' affiliations saved to HTML file " + map_file + "\n")
            
            heatmap_file = INSTRUCTORS_DATA_DIR + 'heatmap_instructors_affiliations_' + instructors_file_name_without_extension + '.html'
            embed_minimal_html(heatmap_file, views=[heatmap])
            print("Heatmap of instructors' affiliations saved to HTML file " + heatmap_file + "\n")
            
        except:
            print ("An error occurred while creating the map of instructors' affiliations ...")
            print(traceback.format_exc())
        else:
            if args.google_drive_dir_id:
                try:
                    print("Uploading instructors' affiliations map " + map_file + " to Google Drive.\n")
                    drive = helper.google_drive_authentication()
                    helper.google_drive_upload(map_file,
                                               drive,
                                               [{'mimeType': 'text/plain', 'id': args.google_drive_dir_id}],
                                               False)
                    print("Map uploaded to Google Drive.\n")

                    print("Uploading instructors' affiliations heatmap " + html_heatmap_file + " to Google Drive.\n")
                    helper.google_drive_upload(html_heatmap_file,
                                               drive,
                                               [{'mimeType': 'text/plain', 'id': args.google_drive_dir_id}],
                                               False)
                    print("Heatmap uploaded to Google Drive.\n")

                except Exception:
                    print ("An error occurred while uploading the map to Google Drive ...")
                    print(traceback.format_exc())


if __name__ == '__main__':
    main()

