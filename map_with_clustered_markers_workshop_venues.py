import os
import pandas as pd
import traceback
import glob
import re
import sys

sys.path.append('/lib')
import lib.helper as helper


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
WORKSHOP_DATA_DIR = CURRENT_DIR + '/data/workshops/'


def main():
    """
    Main function
    """
    args = helper.parse_command_line_paramters()
    print("Mapping workshop venue geocoordinates into clusters on an interactive map ...\n")

    if args.workshops_file:
        workshops_file = args.workshops_file
        print("The CSV spreadsheet with Carpentry workshops to be mapped: " + args.workshops_file + "\n")
    else:
        print(
        "Trying to locate the latest CSV spreadsheet with Carpentry workshops to map in " + WORKSHOP_DATA_DIR + "\n")
        workshops_files = glob.glob(WORKSHOP_DATA_DIR + "carpentry-workshops_*.csv")
        workshops_files.sort(key=os.path.getctime)  # order by creation date

        if not workshops_files:
            print('No CSV file with Carpentry workshops found in ' + WORKSHOP_DATA_DIR + ". Exiting ...")
            sys.exit(1)
        else:
            workshops_file = workshops_files[-1]  # get the last element

    workshops_file_name = os.path.basename(workshops_file)
    workshops_file_name_without_extension = re.sub('\.csv$', '', workshops_file_name.strip())
    print("The CSV spreadsheet with Carpentry workshops to be mapped: " + workshops_file + "\n")

    try:
        df = helper.load_data_from_csv(workshops_file, ['venue', 'latitude', 'longitude'])
        print('Generating a map of workshop venues ...\n')
        map = helper.generate_map_with_clustered_markers(df, "venue")
        if "GB" in workshops_file:  # if the data is for UK workshops - add layer with UK regions to the map
            map = helper.add_UK_regions_layer(map)

        ## Save map to a HTML file
        html_map_file = WORKSHOP_DATA_DIR + 'map_clustered_workshop_venues_' + workshops_file_name_without_extension + '.html'
        map.save(html_map_file)
        print('Map of workshop venues saved to HTML file ' + html_map_file + '\n')

    except:
        print ("An error occurred while creating the map of workshop venues  ...")
        print(traceback.format_exc())
    else:
        if args.google_drive_dir_id:
            try:
                print("Uploading workshop venues map to Google Drive " + html_map_file)
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
