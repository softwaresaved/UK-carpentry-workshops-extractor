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
WORKSHOP_DATA_DIR = CURRENT_DIR + '/data/workshops/'
REGIONS_FILE = CURRENT_DIR + '/lib/regions.json'


def create_regions_column(df, regions):
    """
    Find coordinates and see in which region they fall and create
    the respective columns.
    """

    ## List corresponding to the region collumn
    list_regions = []

    ## Find the region for each point and add in a new column
    count = 1
    for row in df.itertuples():
        print('Finding region for marker ' + str(count) + ' out of ' +
              str(len(df.index)))
        point = Point(row[3].item(), row[2].item())
        for feature in regions['features']:
            polygon = shape(feature['geometry'])
            if polygon.contains(point):
                list_regions.append(feature['properties']['NAME'])
        count += 1

    ## Add regions
    df["region"] = list_regions
    return df


def workshops_per_region(df):
    """
    Creates a dataframe with the number of workshops per region.
    """
    DataFrame = pd.core.frame.DataFrame
    region_table = DataFrame({'count': df.groupby(['region']).size()}).reset_index()

    return region_table


def define_threshold_scale(df_region):
    """
    Creates the threshold scale to be visualized in the map
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
    Generates a choropleth map of the number of workshops that can be found
    in each UK region based on the venue coordinates of extracted excel file.
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
        legend_name='Number of Workshops per region',
        threshold_scale=threshold_scale)
    return maps

def main():
    """
    Main function
    """
    args = helper.parse_command_line_paramters()
    print("Mapping workshop venue geocoordinates into a 'heat map' over UK regions ...\n")
    print("Note: this map only makes sense to generate with workshops in the UK as it maps them per UK regions.\n")

    if args.workshops_file:
        workshops_file = args.workshops_file
    else:
        print("Trying to locate the latest CSV spreadsheet with Carpentry workshops to map in " + WORKSHOP_DATA_DIR + "\n")
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
        regions = json.load(open(REGIONS_FILE, encoding='utf-8-sig'))
    except:
        print ("An error occurred while reading the UK regions file " + REGIONS_FILE)
        print(traceback.format_exc())
    else:
        try:
            df = helper.load_data_from_csv(workshops_file, ['venue', 'latitude', 'longitude'])
            df = create_regions_column(df, regions)
            workshops_per_region_df = workshops_per_region(df)
            print('Generating a map of workshop venues per UK regions ...')
            threshold_scale = define_threshold_scale(workshops_per_region_df)
            maps = generate_map(workshops_per_region_df, regions, threshold_scale)

            ## Save map to a HTML file
            html_map_file = WORKSHOP_DATA_DIR + 'map_per_UK_regions_' + workshops_file_name_without_extension + '.html'
            maps.save(html_map_file)
            print('Map of workshops per region saved to HTML file ' + html_map_file)
        except:
            print ("An error occurred while creating the map Excel spreadsheet ...")
            print(traceback.format_exc())
        else:
            if args.google_drive_dir_id:
                try:
                    print("Uploading workshops per region map to Google Drive " + html_map_file)
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
