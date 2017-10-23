import os
import folium
import pandas as pd

## Upload both instructors data to be mapped and corresponding coordinates
dirP = os.path.dirname(os.path.realpath(__file__))
findFile = [filename for filename in os.listdir(dirP + '/data/instructors')
                if filename.startswith("carpentry-instructors_")
                and filename.endswith('.csv')]
try:
        len(findFile)!=0    
except FileNotFoundError:
    print("The file you were looking for is not found.")

data_instructors = pd.read_csv(dirP + '/data/instructors/' + findFile[-1],
                               usecols=['affiliation'])

data_coordinates = pd.read_csv(dirP + '/lib/UK-academic-insitutions-geodata.csv',
                               usecols = ['VIEW_NAME','LONGITUDE','LATITUDE'])

## Removes null values for affiliation and country_code
data_instructors = data_instructors.dropna(subset=['affiliation'])

## Number of People per affiliation
table = data_instructors.groupby(['affiliation']).size()
instructors = table.to_dict()

## Generate Map
m = folium.Map(
    location=[54.00366, -2.547855],
    zoom_start=6)

for key, value in instructors.items():
            long_coords = data_coordinates[data_coordinates['VIEW_NAME'] == key]['LONGITUDE']
            lat_coords = data_coordinates[data_coordinates['VIEW_NAME'] == key]['LATITUDE']
            if long_coords.empty == False:
                folium.Marker([lat_coords.iloc[0],
                               long_coords.iloc[0]],
                              popup=str(value)).add_to(m)

m.save(dirP + '/data/instructors/Intructors_per_Affiliation.html')
