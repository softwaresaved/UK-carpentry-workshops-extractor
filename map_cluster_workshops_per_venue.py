import os
import folium
import pandas as pd
from folium.plugins import MarkerCluster


## Upload both instructors data to be mapped
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
    zoom_start=6)

marker_cluster = MarkerCluster().add_to(m)

for index, row in data_instructors.iterrows():
        folium.Marker(
                location=[row['latitude'], row['longitude']]
        ).add_to(marker_cluster)
        
m.save(dirP + '/data/workshops/map_cluster_workshops_per_location.html')
