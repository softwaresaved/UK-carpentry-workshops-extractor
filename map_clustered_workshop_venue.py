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
GOOGLE_DRIVE_DIR_ID = "0B6P79ipNuR8EdDFraGgxMFJaaVE"


def load_workshops_data(csv_file):
    """
    Uploads instructors data to a dataframe.
    """
    df = pd.read_csv(csv_file, usecols=['venue','latitude','longitude'])
    return pd.DataFrame(df)

def generate_map(df,filename):
    """
    Generates Map to be visualized.
    """
    maps = folium.Map(
            location=[54.00366, -2.547855],
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
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--workshops_file', type=str, help='an absolute path to a workshops file to analyse')
    parser.add_argument('-gid', '--google_drive_dir_id', type=str, help='ID of a Google Drive directory where to upload the files to')
    args = parser.parse_args()

    if args.workshops_file:
        workshops_file = args.workshops_file
        print("The CSV spreadsheet with Carpentry workshops to be mapped: " + args.workshops_file)
    else:
        print(
            "Trying to locate the latest CSV spreadsheet with Carpentry workshops to map in " + WORKSHOP_DATA_DIR + "\n")
        workshops_files = glob.glob(WORKSHOP_DATA_DIR + "carpentry-workshops_GB_*.csv")
        workshops_files.sort(key=os.path.getctime)  # order by creation date

        if not workshops_files[-1]:  # get the last element
            print('No CSV file with UK Carpentry workshops found in ' + WORKSHOP_DATA_DIR + ". Exiting ...")
            sys.exit(1)
        else:
            workshops_file = workshops_files[-1]

    workshops_file_name = os.path.basename(workshops_file)
    workshops_file_name_without_extension = re.sub('\.csv$', '', workshops_file_name.strip())

    try:
        regions = json.load(open(REGIONS_FILE, encoding='utf-8-sig'))
    except:
        print ("An error occurred while reading the UK regions file " + REGIONS_FILE)
        print(traceback.format_exc())
    else:
        try:
            df = load_workshops_data(workshops_file)
            print('Generating map of workshops per venue ...')
            maps = generate_map(df, workshops_file_name_without_extension)

            ## Save map to a HTML file
            html_map_file = WORKSHOP_DATA_DIR + 'map_clustered_workshop_venue_' + workshops_file_name_without_extension + '.html'
            maps.save(html_map_file)
            print('Map of workshops per venue saved to HTML file ' + html_map_file)
        except:
            print ("An error occurred while creating the map Excel spreadsheet ...")
            print(traceback.format_exc())
        else:
            if args.google_drive_dir_id:
                try:
                    print("Uploading workshops per venue map to Google Drive " + html_map_file)
                    drive = helper.google_drive_authentication()
                    parameter = "mimeType" 
                    variable = "text/plain"
                    boolean = False
                    helper.google_drive_upload(html_map_file, drive, args.google_drive_dir_id,parameter,variable,boolean)
                    print('Map uploaded to Google Drive.')
                except Exception:
                    print ("An error occurred while uploading workshops per venue map to Google Drive ...")
                    print(traceback.format_exc())


if __name__ == '__main__':
    main()
