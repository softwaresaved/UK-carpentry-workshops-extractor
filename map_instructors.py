import os
import pandas as pd
import numpy as np
import traceback
import glob
import re
import sys
import json
import shapefile

# import selenium
sys.path.append('/lib')
import lib.helper as helper

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = CURRENT_DIR + '/data'
RAW_DATA_DIR = DATA_DIR + '/raw'
MAPS_DIR = DATA_DIR + "/maps"

UK_INSTITUTIONS_GEODATA_FILE = CURRENT_DIR + '/lib/UK-academic-institutions-geodata.csv'
UK_REGIONS_FILE = CURRENT_DIR + '/lib/UK-regions.json'


def main():
    """
    Main function
    """
    # The maps only make sense for the data in the UK
    print(
        "#########################################################################################################################################################")
    print(
        "Note: these maps only make sense to generate with instructors from the UK as it cross references their affiliations with geocoordinates of UK institutions.")
    print(
        "#########################################################################################################################################################\n")

    args = helper.parse_command_line_parameters_maps()
    if args.input_file:
        instructors_file = args.input_file
    else:
        print("Trying to locate the latest CSV spreadsheet with Carpentry instructors to analyse in " + RAW_DATA_DIR)
        instructors_files = glob.glob(RAW_DATA_DIR + "/carpentry-instructors_*.csv")
        instructors_files.sort(key=os.path.getctime)  # order files by creation date

        if not instructors_files:
            print("No CSV file with Carpentry instructors found in " + RAW_DATA_DIR + ". Exiting ...")
            sys.exit(1)
        else:
            instructors_file = instructors_files[-1]  # get the last file

    instructors_file_name = os.path.basename(instructors_file)
    instructors_file_name_without_extension = re.sub('\.csv$', '', instructors_file_name.strip())

    print("CSV spreadsheet with UK Carpentry instructors to be mapped: " + instructors_file + "\n")

    try:
        instructors_df = pd.read_csv(instructors_file, encoding="utf-8", usecols=["affiliation", "country_code"])
        # Drop rows where we do not have affiliation as there is nothing to map there
        instructors_df.dropna(subset=["affiliation"], inplace=True)
        # Normalise affiliations
        instructors_df = helper.insert_normalised_institution(instructors_df, "affiliation")
        # Insert latitude, longitude pairs for instructor's affiliation
        instructors_df = helper.insert_institutional_geocoordinates(instructors_df, "normalised_institution_name",
                                                                    "latitude", "longitude")
        # Insert the UK region that affiliation's geocoordinates fall in
        instructors_df = helper.insert_uk_region(instructors_df)
        # Drop rows where we do not have longitude and latitude
        instructors_df.dropna(0, 'any', None, ['longitude', 'latitude'],
                              inplace=True)
        instructors_df.rename(columns={"affiliation" : "institution"},inplace=True)
        instructors_df = instructors_df.reset_index(drop=True)

        # Add column 'description' which is used for popups in maps
        instructors_df['description'] = instructors_df["institution"]

        # Save instructors locations table, it may come in handy
        instructors_file = MAPS_DIR + "/locations_" + instructors_file_name_without_extension + ".csv"
        instructors_df.to_csv(instructors_file, encoding="utf-8", index=False)
        print("\nSaved instructors locations to " + instructors_file + "\n")

    except Exception:
        print ("An error occurred while loading Carpentry instructors ...")
        print(traceback.format_exc())
        sys.exit(1)

    # Map with clustered markers
    try:
        print("#########################################################################")
        print("Map 1: Generating a map of instructor affiliations as clusters of markers")
        print("#########################################################################\n")
        instructors_map = helper.generate_map_with_clustered_markers(instructors_df)
        instructors_map = helper.add_UK_regions_layer(instructors_map)
        # Save map to a HTML file
        map_file = MAPS_DIR + '/map_clustered_instructor_affiliations_' + instructors_file_name_without_extension + '.html'
        instructors_map.save(map_file)
        print('Map of instructor affiliations saved to HTML file ' + map_file + '\n')
    except Exception:
        print ("An error occurred while creating the map of instructors affiliations as clusters of markers.")
        print(traceback.format_exc())

    # A map of instructors affiliations with circular markers
    try:
        print("########################################################################")
        print("Map 2: Generating a map of instructor affiliations with circular markers")
        print("########################################################################\n")
        instructors_map = helper.generate_map_with_circular_markers(instructors_df)
        # Save the map to an HTML file
        map_file = MAPS_DIR + '/map_individual_markers_instructor_affiliations_' + \
                   instructors_file_name_without_extension + '.html'
        instructors_map.save(map_file)
        print("A map of instructor affiliations with circular markers saved to HTML file " + map_file + "\n")
    except Exception:
        print ("An error occurred while creating a map of instructor affiliations with circular markers.\n")
        print(traceback.format_exc())

    # A heatmap of instructors affiliations
    try:
        print("#######################################################")
        print("Map 3: Generating a heatmap of instructors affiliations")
        print("#######################################################\n")
        instructors_map = helper.generate_heatmap(instructors_df)
        # Save the heatmap to an HTML file
        map_file = MAPS_DIR + '/heatmap_instructors_affiliations_' + instructors_file_name_without_extension + '.html'
        instructors_map.save(map_file)
        print("Heatmap of instructors affiliations saved to HTML file " + map_file + "\n")
    except Exception:
        print ("An error occurred while creating a heatmap of instructors affiliations.\n")
        print(traceback.format_exc())

    # Choropleth map over UK regions
    try:
        print("##############################################################################")
        print('Map 4: Generating a choropleth map of instructors affiliations over UK regions')
        print("##############################################################################\n")
        uk_regions = json.load(open(UK_REGIONS_FILE, encoding='utf-8-sig'))
        instructors_map = helper.generate_choropleth_map(instructors_df, uk_regions, "instructors")
        # Save map to a HTML file
        map_file = MAPS_DIR + '/choropleth_map_instructors_per_UK_regions_' + instructors_file_name_without_extension + '.html'
        instructors_map.save(map_file)
        print('A choropleth map of instructors affiliations over UK regions saved to HTML file ' + map_file + '\n')
    except Exception:
        print ("An error occurred while creating a choropleth map of instructors affiliations over UK regions.\n")
        print(traceback.format_exc())


if __name__ == '__main__':
    main()
