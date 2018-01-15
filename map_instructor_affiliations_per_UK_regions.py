import os
import argparse
import json
import folium
import pandas as pd
import shapefile
import traceback
import glob
import re
import sys

sys.path.append('/lib')
import lib.helper as helper

from shapely.geometry import shape, Point

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
INSTRUCTORS_DATA_DIR = CURRENT_DIR + '/data/instructors/'
UK_INSTITUTIONS_GEODATA_FILE = CURRENT_DIR + '/lib/UK-academic-institutions-geodata.xlsx'
REGIONS_FILE = CURRENT_DIR + '/lib/UK_regions.json'


def add_region_column(df, coords_df, regions):
    """
    Find coordinates and see in which region they fall and create a column
    with the correspondig results.
    """
    ## Create latitude and longitude list to create columns
    latitude_list = []
    longitude_list = []

    ## Transform 'institution' column into list and find respective coords
    for index, row in df.iterrows():
        long_coords = coords_df[coords_df['VIEW_NAME'] == row['institution']]['LONGITUDE']
        lat_coords = coords_df[coords_df['VIEW_NAME'] == row['institution']]['LATITUDE']
        if lat_coords.empty or long_coords.empty:
            print('\nInstructor in row with index ' + str(index) + ' has affiliation "' + row['affiliation'] +
                  '" which we either have not got coordinates for or it is not the official name of an UK '
                  'academic institution. Skipping it ...\n')
            df.drop(index, inplace=True)
        else:
            latitude_list.append(lat_coords.iloc[0])
            longitude_list.append(long_coords.iloc[0])

    ## Add coords to the DataFrame
    df["LATITUDE"] = latitude_list
    df["LONGITUDE"] = longitude_list

    ## List corresponding to the region column
    region_list = []

    ## Find the region for each point and add in a new column
    count = 1
    for row in df.itertuples():
        print('Finding region for marker ' + str(count) + ' out of ' +
              str(len(df.index)))
        point = Point(row[4].item(), row[3].item())
        for feature in regions['features']:
            polygon = shape(feature['geometry'])
            if polygon.contains(point):
                region_list.append(feature['properties']['NAME'])
        count += 1

    ## Add regions
    df["region"] = region_list
    return df


def instructors_per_region(df):
    """
    Creates a dataframe with the number of instructors per region.
    """
    DataFrame = pd.core.frame.DataFrame
    region_table = DataFrame({'count': df.groupby(['region']).size()}).reset_index()
    return region_table


def define_threshold_scale(df_region):
    """
    Creates the threshold scale to be visualized in the map.
    """
    scale_list = df_region['count'].tolist()
    max_scale = max(scale_list)
    scale = int(max_scale / 5)
    threshold_scale = []
    for each in range(0, max_scale + 1, scale):
        threshold_scale.append(each)
    return threshold_scale


def generate_map(df, regions, threshold_scale):
    """
    Generates a choropleth map of the number of instructors that can be found
    in each UK region.
    """
    maps = folium.Map(
        location=[54.00366, -2.547855],
        zoom_start=6,
        tiles='cartodbpositron')  # for a lighter map tiles='Mapbox Bright'

    maps.choropleth(
        geo_data=regions,
        data=df,
        columns=['region', 'count'],
        key_on='feature.properties.NAME',
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Number of instructors per UK region',
        threshold_scale=threshold_scale)
    return maps


def main():
    """
    Main function
    """
    args = helper.parse_command_line_paramters()
    print("Mapping instructors affiliation geocoordinates into a 'heat map' over UK regions...\n")

    if args.instructors_file:
        instructors_file = args.instructors_file
    else:
        print(
        "Trying to locate the latest CSV spreadsheet with Carpentry instructors to map in " + INSTRUCTORS_DATA_DIR + "\n")
        instructors_files = glob.glob(INSTRUCTORS_DATA_DIR + "carpentry-instructors_GB_*.csv")
        instructors_files.sort(key=os.path.getctime)  # order by creation date

        if not instructors_files:
            print('No CSV file with Carpentry instructors found in ' + INSTRUCTORS_DATA_DIR + ". Exiting ...")
            sys.exit(1)
        else:
            instructors_file = instructors_files[-1]  # get the last element

    instructors_file_name = os.path.basename(instructors_file)
    instructors_file_name_without_extension = re.sub('\.csv$', '', instructors_file_name.strip())
    print("The CSV spreadsheet with Carpentry instructors to be mapped: " + instructors_file)

    try:
        regions = json.load(open(REGIONS_FILE, encoding='utf-8-sig'))
    except:
        print ("An error occurred while reading the UK regions file " + REGIONS_FILE)
        print(traceback.format_exc())
    else:
        try:
            uk_academic_institutions_excel_file = pd.ExcelFile(UK_INSTITUTIONS_GEODATA_FILE)
            uk_academic_institutions_df = uk_academic_institutions_excel_file.parse('UK-academic-institutions')
        except:
            print ("An error occurred while reading the UK academic institutions' geodata file " + UK_INSTITUTIONS_GEODATA_FILE)
        else:
            try:
                df = helper.load_data_from_csv(instructors_file, ['institution', 'nearest_airport_code'])
                df = helper.drop_null_values_from_columns(df, ['institution', 'nearest_airport_code'])
                df = helper.fix_UK_academic_institutions_names(df)

                uk_academic_institutions_coords_df = uk_academic_institutions_df[['VIEW_NAME', 'LONGITUDE', 'LATITUDE']]
                all_uk_institutions_coords_df = uk_academic_institutions_coords_df.append(helper.get_UK_non_academic_institutions_coords())
                df = add_region_column(df, all_uk_institutions_coords_df, regions)
                instructors_per_region_df = instructors_per_region(df)

                print('Generating a map of instructors per UK regions ...')
                threshold_scale = define_threshold_scale(instructors_per_region_df)
                maps = generate_map(instructors_per_region_df, regions, threshold_scale)

                ## Save map to a HTML file
                html_map_file = INSTRUCTORS_DATA_DIR + 'map_instructors_per_UK_regions_' + instructors_file_name_without_extension + '.html'
                maps.save(html_map_file)
                print('Map of instructors per UK regions saved to HTML file ' + html_map_file)
            except:
                print ("An error occurred while creating the map of instructors per UK regions ...")
                print(traceback.format_exc())
            else:
                if args.google_drive_dir_id:
                    try:
                        print("Uploading instructors per UK regions map to Google Drive " + html_map_file)
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
