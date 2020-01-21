import os
import traceback
import glob
import re
import sys
import json
import pandas as pd
import numpy as np

sys.path.append('/lib')
import lib.helper as helper

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = CURRENT_DIR + '/data'
RAW_DATA_DIR = DATA_DIR + '/raw'
MAPS_DIR = DATA_DIR + "/maps"
UK_REGIONS_FILE = CURRENT_DIR + '/lib/UK-regions.json'


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

    print("CSV spreadsheet with Carpentry workshops to be mapped: " + workshops_file + "\n")

    try:
        workshops_df = pd.read_csv(workshops_file, encoding="utf-8", usecols=['venue', 'address', 'latitude',
                                                                              'longitude'])
        idx = workshops_df.columns.get_loc("longitude")
        workshops_df.insert(loc=idx + 1, column='region',
                            value=workshops_df["longitude"])
        # Rename 'venue' column to 'institution' as some of our methods expect that column name
        workshops_df.rename(columns={"venue": "institution"}, inplace=True)
        # Add column 'description' which is used in popups in maps
        workshops_df['description'] = np.where(workshops_df["address"].empty, workshops_df["institution"],
                                               workshops_df["institution"] + ', ' + workshops_df["address"])
        print(workshops_df)
        if not os.path.exists(MAPS_DIR):
            os.makedirs(MAPS_DIR)

        if "_GB_" in workshops_file_name_without_extension:  # Only makes sense for the UK
            # Calculate and insert UK region based on workshop location
            workshops_df['region'] = workshops_df.apply(
                lambda x: helper.get_uk_region(airport_code=np.nan, latitude=x['latitude'],
                                               longitude=x['longitude']), axis=1)
        # Save workshop locations table, it may come in handy
        workshops_file = MAPS_DIR + "/locations_" + workshops_file_name_without_extension + ".csv"
        workshops_df.to_csv(workshops_file, encoding="utf-8", index=False)
        print("\nSaved workshops locations to " + workshops_file + "\n")

        # Map with clustered markers
        try:
            print("#####################################################################")
            print("Map 1: Generating a map of workshop venues as clusters of markers")
            print("#####################################################################\n")
            workshop_map = helper.generate_map_with_clustered_markers(workshops_df)
            if "GB" in workshops_file:  # if the data is for UK workshops - add layer with UK regions to the map
                workshop_map = helper.add_UK_regions_layer(workshop_map)
            # Save map to a HTML file
            map_file = MAPS_DIR + '/map_clustered_workshop_venues_' + workshops_file_name_without_extension + '.html'
            workshop_map.save(map_file)
            print('Map of workshop venues saved to HTML file ' + map_file + '\n')
        except Exception:
            print ("An error occurred while creating the map of workshop venues as clusters of markers.")
            print(traceback.format_exc())

        # A map of workshop venues with circular markers
        try:
            print("####################################################################")
            print("Map 2: Generating a map of workshop venues with circular markers")
            print("####################################################################\n")
            workshop_map = helper.generate_map_with_circular_markers(workshops_df)
            # Save the map to an HTML file
            map_file = MAPS_DIR + '/map_individual_markers_workshop_venues_' + workshops_file_name_without_extension + '.html'
            workshop_map.save(map_file)
            print("A map of workshop venues with circular markers saved to HTML file " + map_file + "\n")
        except Exception:
            print ("An error occurred while creating a map of workshop venues with circular markers.\n")
            print(traceback.format_exc())

            # A heatmap of workshop venues
        try:
            print("#######################################################")
            print("Map 3: Generating a heatmap of workshop venue locations")
            print("#######################################################\n")
            workshop_map = helper.generate_heatmap(workshops_df)
            # Save the heatmap to an HTML file
            map_file = MAPS_DIR + '/heatmap_workshop_venues_' + workshops_file_name_without_extension + '.html'
            workshop_map.save(map_file)
            print("Heatmap of instructors' affiliations saved to HTML file " + map_file + "\n")
        except Exception:
            print ("An error occurred while creating a heatmap of workshop venue locations.\n")
            print(traceback.format_exc())

        # Choropleth map over UK regions
        if "_GB_" in workshops_file_name_without_extension:  # Only makes sense for the UK
            try:
                print("#####################################################################")
                print('Map 4: Generating a choropleth map of workshop venues over UK regions')
                print("#####################################################################\n")
                uk_regions = json.load(open(UK_REGIONS_FILE, encoding='utf-8-sig'))
                workshop_map = helper.generate_choropleth_map(workshops_df, uk_regions, "workshops")
                # Save map to a HTML file
                map_file = MAPS_DIR + '/choropleth_map_workshops_per_UK_regions_' + workshops_file_name_without_extension + '.html'
                workshop_map.save(map_file)
                print('A choropleth map of workshops over UK regions saved to HTML file ' + map_file + '\n')
            except Exception:
                print ("An error occurred while creating a choropleth map of workshops over UK regions.\n")
                print(traceback.format_exc())

    except Exception:
        print ("An error occurred while mapping Carpentry workshops ...")
        print(traceback.format_exc())


if __name__ == '__main__':
    main()
