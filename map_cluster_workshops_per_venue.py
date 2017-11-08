import os
import argparse
import folium
import json
import pandas as pd
import pycountry
from folium.plugins import MarkerCluster
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
WORKSHOP_DATA_DIR = CURRENT_DIR + '/data/workshops/'


def load_workshops_data(csv_file):
    """
    Uploads instructors data to a dataframe.
    """
    try:
        df = pd.read_csv(csv_file, usecols=['venue','latitude','longitude'])
    except:
      raise
    return pd.DataFrame(df)

def generate_map(df,filename):
    """
    Generates Map to be visualized.
    """
    m = folium.Map(
            location=[54.00366, -2.547855],
            zoom_start=6,
            tiles='cartodbpositron') # for a lighter map tiles='Mapbox Bright'

    marker_cluster = MarkerCluster(name = 'workshops').add_to(m)
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
                           }).add_to(m)
    folium.LayerControl().add_to(m)

    ## Find suffix
    suffix = filename.split('_',1)[1].replace('.csv','')

    ## Save mapp to html
    path_html = WORKSHOP_DATA_DIR + 'map_cluster_workshops_per_venue_' + suffix + '.html'
    m.save(path_html)
    return path_html

def google_drive_authentication():
    """
    Authentication to the google drive account
    """
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    return drive
    
def google_drive_upload(html_file,drive):
    """
    Upload map to google drive
    """
    upload_map = drive.CreateFile({'parents': [{"mimeType":"text/plain",
                                                'id': '0B6P79ipNuR8EdDFraGgxMFJaaVE'}],
                                   'title':'map_cluster_workshops_per_venue_' + date })
    upload_map.SetContentFile(html_file)
    upload_map.Upload({'convert': False})


def main():
    """
    Main function
    """
    country_code = ''

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--country_code', default='GB', type=str)
    args = parser.parse_args()

    try:
        pycountry.countries.get(alpha_2=args.country_code)
    except:
        print('The country code submitted does not exist.')
        raise
        
    print("Trying to locate the latest CSV spreadsheet with Carpentry workshops to analyse in directory " + WORKSHOP_DATA_DIR + ".")
    workshops_files = [os.path.join(WORKSHOP_DATA_DIR,filename) for filename in os.listdir(WORKSHOP_DATA_DIR)
                       if filename.startswith("carpentry-workshops_" + str(args.country_code)) and filename.endswith('.csv')]

    if not workshops_files:
        print('No CSV file with Carpentry workshops found in ' + WORKSHOP_DATA_DIR + ".")
        print('Exiting...')
        exit(-1)
    else:
        workshops_file = max(workshops_files, key=os.path.getctime)## if want most recent modification date use getmtime

    df = load_workshops_data(workshops_file)
    print('Generating map...')
    html_file = generate_map(df,workshops_file)
    print('Cluster Map of workshops per venue created - see results in ' +
          html_file + '.')

##    print("Uploading Map of workshops per venue to Google Drive ...")
##    drive = google_drive_authentication()
##    google_drive_upload(html_file,drive)
##    print('Cluster Map uploaded to Google Drive.')


if __name__ == '__main__':
    main()
