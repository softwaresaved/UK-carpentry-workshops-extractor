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
    args = helper.parse_command_line_parameters_maps()
    workshops_file = args.input_file
    workshops_file_name = os.path.basename(workshops_file)
    workshops_file_name_without_extension = re.sub('\.csv$', '', workshops_file_name.strip())
    print("CSV spreadsheet with Carpentry workshops to be mapped: " + workshops_file + "\n")

    try:
        workshops_df = pd.read_csv(workshops_file, encoding="utf-8", usecols=['venue', 'address', 'latitude',
                                                                              'longitude', 'region'])
        # Rename 'venue' column to 'institution' as some of our methods expect that column name
        workshops_df.rename(columns={"venue": "institution"}, inplace=True)

       # Add column 'popup' which is used in popups in maps
        workshops_df['popup'] = np.where(workshops_df["address"].empty, workshops_df["institution"],
                                               workshops_df["institution"] + ', ' + workshops_df["address"])
        # print(workshops_df)
        if not os.path.exists(MAPS_DIR):
            os.makedirs(MAPS_DIR)
    except Exception:
        print ("An error occurred while loading Carpentry workshops ...")
        print(traceback.format_exc())
        sys.exit(1)

    # Map with clustered markers
    try:
        print("#####################################################################")
        print("Map 1: Generating a map of workshop venues as clusters of markers")
        print("#####################################################################\n")
        workshops_map = helper.generate_map_with_clustered_markers(workshops_df)
        if "GB" in workshops_file:  # if the data is for UK workshops - add layer with UK regions to the map
            workshops_map = helper.add_UK_regions_layer(workshops_map)
        # Save map to a HTML file
        map_file = MAPS_DIR + '/map_clustered_markers_' + workshops_file_name_without_extension + '.html'
        workshops_map.save(map_file)
        print('Map of clustered workshop locations saved to HTML file ' + map_file + '\n')
    except Exception:
        print ("An error occurred while creating the map of workshop locations as clusters of markers.")
        print(traceback.format_exc())

    # A map of workshop venues with circular markers
    try:
        print("####################################################################")
        print("Map 2: Generating a map of workshop venues with circular markers")
        print("####################################################################\n")
        workshops_map = helper.generate_map_with_circular_markers(workshops_df)
        # Save the map to an HTML file
        map_file = MAPS_DIR + '/map_individual_markers_' + workshops_file_name_without_extension + '.html'
        workshops_map.save(map_file)
        print("A map of workshop venues with circular markers saved to HTML file " + map_file + "\n")
    except Exception:
        print ("An error occurred while creating a map of workshop venues with circular markers.\n")
        print(traceback.format_exc())

    # A heat map of workshop venues
    try:
        print("#######################################################")
        print("Map 3: Generating a heat map of workshop venue locations")
        print("#######################################################\n")
        workshops_map = helper.generate_heatmap(workshops_df)
        # Save the heat map to an HTML file
        map_file = MAPS_DIR + '/heat_map_' + workshops_file_name_without_extension + '.html'
        workshops_map.save(map_file)
        print("Heat map of workshop venue locations saved to HTML file " + map_file + "\n")
    except Exception:
        print ("An error occurred while creating a heat map of workshop venue locations.\n")
        print(traceback.format_exc())

    # # Choropleth map over UK regions -  only makes sense for the UK
    # try:
    #     print("#####################################################################")
    #     print('Map 4: Generating a choropleth map of workshop venues over UK regions')
    #     print("#####################################################################\n")
    #     uk_regions = json.load(open(UK_REGIONS_FILE, encoding='utf-8-sig'))
    #     # Get rid of rows where region is null
    #     workshops_df = workshops_df.dropna(subset=['region'])
    #     workshops_map = helper.generate_choropleth_map(workshops_df, uk_regions, "workshops")
    #     # Save map to a HTML file
    #     map_file = MAPS_DIR + '/choropleth_map_UK_regions_' + workshops_file_name_without_extension + '.html'
    #     workshops_map.save(map_file)
    #     print('A choropleth map of workshops over UK regions saved to HTML file ' + map_file + '\n')
    # except Exception:
    #     print ("An error occurred while creating a choropleth map of workshops over UK regions.\n")
    #     print(traceback.format_exc())


if __name__ == '__main__':
    main()
