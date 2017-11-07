import os
import folium
import json
import pandas as pd
from folium.plugins import MarkerCluster
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


DIR_PATH = os.path.dirname(os.path.realpath(__file__))
findFile = [filename for filename in os.listdir(DIR_PATH + '/data/workshops')
            if filename.startswith("carpentry-workshops_")
            and filename.endswith('.csv')]
if not findFile:
  print('No file was found.')  
else:
  DATA = findFile[-1]


def load_workshops_data(filename):
    """
    Uploads instructors data to a dataframe.
    """
    df = pd.read_csv(DIR_PATH + '/data/workshops/' + findFile[-1],
                     usecols=['venue','latitude','longitude'])
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
    regions = json.load(open(DIR_PATH + '/lib/regions.json',encoding = 'utf-8-sig'))

    ## Add to a layer
    folium.GeoJson(regions,
                   name='regions',
                   style_function=lambda feature: {
                           'fillColor': '#99ffcc',
                           'color': '#00cc99'
                           }).add_to(m)
    folium.LayerControl().add_to(m)

    ## Find main file date
    date = filename.split('_')[2].replace('.csv','')

    ## Save mapp to html
    path_html = DIR_PATH + '/data/workshops/map_cluster_workshops_per_venue_' + date + '.html'
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
    df = load_workshops_data(DATA)
    print('Generating map...')
    html_file = generate_map(df,DATA)
    print('HTML file created.')

##    drive = google_drive_authentication()
##    google_drive_upload(html_file,drive)
##    print('Analysis spreadsheet uploaded to Google Drive.')



if __name__ == '__main__':
    main()
