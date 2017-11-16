import os
import argparse
import folium
import json
import pandas as pd
import traceback
import glob
import re
from folium.plugins import MarkerCluster
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import sys
sys.path.append('/lib')
import lib.helper as helper


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
WORKSHOP_DATA_DIR = CURRENT_DIR + '/data/workshops/'
REGIONS_FILE = CURRENT_DIR + '/lib/regions.json'


def generate_map(df,filename):
    """
    Generates Map to be visualized.
    """
    subset = df[['latitude', 'longitude']]
    tuples = [tuple(coords) for coords in subset.values]
    x,y=zip(*tuples)
    center=(max(x)+min(x))/2., (max(y)+min(y))/2.
    
    maps = folium.Map(
            location=[center[0], center[1]],
            zoom_start=6,
            tiles='cartodbpositron') # for a lighter map tiles='Mapbox Bright'

    marker_cluster = MarkerCluster(name = 'workshops').add_to(maps)
    for index, row in df.iterrows():
            popup = folium.Popup(row['venue'], parse_html=True)
            folium.CircleMarker(
              radius = 5,
              location=[row['latitude'], row['longitude']],
              popup = popup,
              color = '#ff6600',
              fill = True,
              fill_color = '#ff6600').add_to(marker_cluster)

    ## Region information json
    regions = json.load(open(CURRENT_DIR + '/lib/regions.json',encoding = 'utf-8-sig'))

    ## Add to a layer
    folium.GeoJson(regions,
                   name='regions',
                   style_function=lambda feature: {
                           'fillColor': '#99ffcc',
                           'color': '#00cc99'
                           }).add_to(maps)
    folium.LayerControl().add_to(maps)

    return maps

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
        regions = json.load(open(REGIONS_FILE, encoding='utf-8-sig'))
    except:
        print ("An error occurred while reading the UK regions file " + REGIONS_FILE)
        print(traceback.format_exc())
    else:
        try:
            df = helper.load_data_from_csv(workshops_file, ['venue', 'latitude', 'longitude'])
            print('Generating map of workshop venues ...')
            maps = generate_map(df, workshops_file_name_without_extension)

            ## Save map to a HTML file
            html_map_file = WORKSHOP_DATA_DIR + 'map_clustered_workshop_venues_' + workshops_file_name_without_extension + '.html'
            maps.save(html_map_file)
            print('Map of workshop venues saved to HTML file ' + html_map_file)
        except:
            print ("An error occurred while creating the map Excel spreadsheet ...")
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
