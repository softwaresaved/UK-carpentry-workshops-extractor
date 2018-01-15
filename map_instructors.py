import os
import pandas as pd
import traceback
import glob
import re
import sys
import json
import shapefile
from shapely.geometry import shape, Point


sys.path.append('/lib')
import lib.helper as helper


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
INSTRUCTORS_DATA_DIR = CURRENT_DIR + '/data/instructors/'
UK_INSTITUTIONS_GEODATA_FILE = CURRENT_DIR + '/lib/UK-academic-institutions-geodata.xlsx'
UK_REGIONS_FILE = CURRENT_DIR + '/lib/UK_regions.json'


def insert_region_column(df, regions):
    """
    Lookup coordinates from the dataframe and see in which region they fall. Insert the corresponding 'region' column
    in the dataframe.
    """

    region_list = []

    # Find the region for each longitude, latitude pair and add in a new column
    for index, row in df.iterrows():
        print('Finding a UK region for institution ' + row['institution'] + ' in row ' + str(index) + ' out of ' +
              str(len(df.index) - 1) + ". ", "")
        point = Point(row['longitude'], row['latitude'])
        for feature in regions['features']:
            polygon = shape(feature['geometry'])
            if polygon.contains(point):
                region_list.append(feature['properties']['NAME'])
                print("Found region: " + feature['properties']['NAME'])

    print(len(region_list))

    ## Add 'region' column
    df.insert(len(df.columns), "region", region_list, allow_duplicates=False)
    return df


def main():
    """
    Main function
    """
    args = helper.parse_command_line_paramters()
    print("Mapping instructor affiliations' into various maps ... \n")

    print("#########################################################################################################################################################")
    print("Note: this map only makes sense to generate with instructors from the UK as it cross references their affiliations with geocoordinates of UK institutions.")
    print("#########################################################################################################################################################\n")

    if args.instructors_file:
        instructors_file = args.instructors_file
        print("The CSV spreadsheet with Carpentry instructors to be mapped: " + args.instructors_file)
    else:
        print("Trying to locate the latest CSV spreadsheet with Carpentry instructors to map in " + INSTRUCTORS_DATA_DIR + "\n")
        instructors_files = glob.glob(INSTRUCTORS_DATA_DIR + "carpentry-instructors_GB_*.csv")
        instructors_files.sort(key=os.path.getctime)  # order by creation date

        if not instructors_files:
            print('No CSV file with Carpentry instructors found in ' + INSTRUCTORS_DATA_DIR + ". Exiting ...\n")
            sys.exit(1)
        else:
            instructors_file = instructors_files[-1] # get the last element

    instructors_file_name = os.path.basename(instructors_file)
    instructors_file_name_without_extension = re.sub('\.csv$', '', instructors_file_name.strip())
    print('Found CSV file with Carpentry instructors to analyse ' + instructors_file_name + "\n")

    try:
        uk_academic_institutions_geodata_file = pd.ExcelFile(UK_INSTITUTIONS_GEODATA_FILE)
        uk_academic_institutions_geodata_df = uk_academic_institutions_geodata_file.parse('UK-academic-institutions')
    except:
        print (
            "An error occurred while reading the UK academic institutions' geodata file " + UK_INSTITUTIONS_GEODATA_FILE)
    else:
        try:
            df = helper.load_data_from_csv(instructors_file, ['institution'])
            df = helper.drop_null_values_from_columns(df, ['institution'])
            df = helper.fix_UK_academic_institutions_names(df)

            uk_academic_institutions_coords_df = uk_academic_institutions_geodata_df[['VIEW_NAME', 'LONGITUDE', 'LATITUDE']]
            all_uk_institutions_coords_df = uk_academic_institutions_coords_df.append(
                helper.get_UK_non_academic_institutions_coords())

            # Insert latitude, longitude pairs for instructors' institutions into the dataframe with all the instrucotrs' data
            df = helper.insert_institutions_geocoordinates(df, all_uk_institutions_coords_df)

            # Discard all institutions that we do not have longitude and latitude values for, as they cannot be mapped
            for index, row in df.iterrows():
                if pd.isnull(row['longitude']) or pd.isnull(row['latitude']):
                    print('For affiliation "' + row[
                        'institution'] + '" we either have not got coordinates or it is not the official name of an UK '
                                         'academic institution. Skipping it ...\n')
            # Drop rows where we do not have longitude and latitude
            df.dropna(0, 'any', None, ['latitude', 'longitude'], inplace=True)
            df = df.reset_index(drop=True)
        except:
            print ("An error occurred while loading instructors' data and preparing it for mapping...\n")
            print(traceback.format_exc())
        else:

            # Map with clustered markers
            try:
                print("############################################################################")
                print("Generating a map of instructor affiliations as clusters of markers ...")
                print("############################################################################\n")

                map = helper.generate_map_with_clustered_markers(df, "institution")
                map = helper.add_UK_regions_layer(map)

                ## Save map to an HTML file
                html_map_file = INSTRUCTORS_DATA_DIR + 'map_clustered_instructor_affiliations_' + instructors_file_name_without_extension + '.html'
                map.save(html_map_file)
                print('Map of instructors affiliations saved to HTML file ' + html_map_file + '\n')
            except:
                print ("An error occurred while creating a clustered map of instructor affiliations ...")
                print(traceback.format_exc())
            else:
                if args.google_drive_dir_id:
                    try:
                        print("Uploading instructor affiliations map to Google Drive " + html_map_file)
                        drive = helper.google_drive_authentication()
                        helper.google_drive_upload(html_map_file,
                                                   drive,
                                                   [{'mimeType': 'text/plain', 'id': args.google_drive_dir_id}],
                                                   False)
                        print('Map uploaded to Google Drive.')
                    except Exception:
                        print ("An error occurred while uploading the map to Google Drive...\n")
                        print(traceback.format_exc())

            # Choropleth map over UK regions
            try:
                uk_regions = json.load(open(UK_REGIONS_FILE, encoding='utf-8-sig'))

                df = insert_region_column(df, uk_regions)

                print("#############################################################")
                print('Generating a choropleth map of instructors over UK regions ...')
                print("#############################################################\n")

                map = helper.generate_choropleth_map(df, uk_regions)

                ## Save map to a HTML file
                html_map_file = INSTRUCTORS_DATA_DIR + 'map_instructors_per_UK_regions_' + instructors_file_name_without_extension + '.html'
                map.save(html_map_file)
                print('A choropleth map of instructors over UK regions saved to HTML file ' + html_map_file + '\n')
            except:
                print ("An error occurred while creating a choropleth map of instructors over UK regions...\n")
                print(traceback.format_exc())
            else:
                if args.google_drive_dir_id:
                    try:
                        print("Uploading a choropleth map of instructors over UK regions to Google Drive " + html_map_file)
                        drive = helper.google_drive_authentication()
                        helper.google_drive_upload(html_map_file,
                                                   drive,
                                                   [{'mimeType': 'text/plain', 'id': args.google_drive_dir_id}],
                                                   False)
                        print('Map uploaded to Google Drive.')
                    except Exception:
                        print ("An error occurred while uploading the map to Google Drive...\n")
                        print(traceback.format_exc())

            try:
                print("#############################################################")
                print('Generating a heatmap of instructor affiliations ...\n')
                print("#############################################################\n")

                heatmap = helper.generate_heatmap(df)

                # Save heatmap to an HTML file
                heatmap_file = INSTRUCTORS_DATA_DIR + 'heatmap_instructors_affiliations_' + instructors_file_name_without_extension + '.html'
                heatmap.save(heatmap_file)
                print("Heatmap of instructors' affiliations saved to HTML file " + heatmap_file + "\n")
            except:
                print ("An error occurred while creating a heatmap of instructor affiliations ...\n")
                print(traceback.format_exc())
            else:
                if args.google_drive_dir_id:
                    try:
                        print("Uploading a heatmap of instructor affiliations to Google Drive " + html_map_file)
                        drive = helper.google_drive_authentication()
                        helper.google_drive_upload(html_map_file,
                                                   drive,
                                                   [{'mimeType': 'text/plain', 'id': args.google_drive_dir_id}],
                                                   False)
                        print('Map uploaded to Google Drive.')
                    except Exception:
                        print ("An error occurred while uploading the map to Google Drive...\n")
                        print(traceback.format_exc())

if __name__ == '__main__':
    main()
