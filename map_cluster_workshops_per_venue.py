import os
import folium
import json
import pandas as pd
from folium.plugins import MarkerCluster
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

## Gogle Drive Authentication
##gauth = GoogleAuth()
##gauth.LocalWebserverAuth()
##drive = GoogleDrive(gauth)

## Upload instructors data to be mapped
dirP = os.path.dirname(os.path.realpath(__file__))
findFile = [filename for filename in os.listdir(dirP + '/data/workshops')
                if filename.startswith("carpentry-workshops_")
                and filename.endswith('.csv')]
try:
        len(findFile)!=0    
except FileNotFoundError:
    print("The file you were looking for is not found.")

data_instructors = pd.read_csv(dirP + '/data/workshops/' + findFile[-1],
                               usecols=['venue','latitude','longitude'])

## Generate Map
m = folium.Map(
    location=[54.00366, -2.547855],
    zoom_start=6,
    tiles='Mapbox Bright') # for a darker map tiles='cartodbpositron'

marker_cluster = MarkerCluster(name = 'workshops').add_to(m)

for index, row in data_instructors.iterrows():
        popup = folium.Popup(row['venue'], parse_html=True)
        folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=popup
        ).add_to(marker_cluster)

## Region information json
regions = json.load(open(dirP + '/lib/regions.json',encoding = 'utf-8-sig'))

## Add to a layer
folium.GeoJson(regions,
               name='regions',
               style_function=lambda feature: {
                       'fillColor': '#99ffcc',
                       'color': '#00cc99'
                       }).add_to(m)
folium.LayerControl().add_to(m)

## Find main file date
date = findFile[-1].split('_')[2].replace('.csv','')

## Save mapp to html
path_html = dirP + '/data/workshops/map_cluster_workshops_per_location_' + date + '.html'
m.save(path_html)

print('HTML file created and ready to be visualized.')

## Upload to google drive
##upload_map = drive.CreateFile({'parents': [{"mimeType":"text/plain",
##                                            'id': '0B6P79ipNuR8EdDFraGgxMFJaaVE'}],
##                               'title':'map_cluster_workshops_per_location_' + date })
##upload_map.SetContentFile(path_html)
##upload_map.Upload({'convert': False})
##
##print("Document Uploaded to Google Drive.")
