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
## Removes null values for affiliation and country_code
data_instructors = data_instructors.dropna(subset=['affiliation'])

## Change Imperial College for the name in UK institutions
data_instructors['affiliation'] = data_instructors['affiliation'].map({'Imperial College London': 'Imperial College of Science, Technology and Medicine'})

## Upload coordinates isntitution data
data_coords = pd.read_csv(dirP + '/lib/UK-academic-insitutions-geodata.csv',
                               usecols = ['VIEW_NAME','LONGITUDE','LATITUDE'])

## Add Missing coordinates
other_dic = [{'VIEW_NAME': 'Queen Mary University of London', 'LONGITUDE':-0.03999799999996867, 'LATITUDE':51.5229832},
             {'VIEW_NAME': 'Wellcome Trust Sanger Institute', 'LONGITUDE':0.18558740000003127, 'LATITUDE':52.0797171},
             {'VIEW_NAME': 'Earlham Institute', 'LONGITUDE':1.2189869000000044, 'LATITUDE':52.6217407},
             {'VIEW_NAME': 'Arriva Group', 'LONGITUDE':-1.4335148000000117, 'LATITUDE':54.86353090000001},
             {'VIEW_NAME': 'Delcam Ltd', 'LONGITUDE':-1.8450110999999652, 'LATITUDE':52.46245099999999},
             {'VIEW_NAME': 'Met Office', 'LONGITUDE':-3.472338000000036, 'LATITUDE':50.72742100000001},
             {'VIEW_NAME': 'Thales', 'LONGITUDE':-2.185189799999989, 'LATITUDE':53.3911872},
             {'VIEW_NAME': 'The John Innes Centre', 'LONGITUDE':1.2213810000000649, 'LATITUDE':52.622271},
             {'VIEW_NAME': 'Climate Code Foundation', 'LONGITUDE':-1.52900139999997, 'LATITUDE':53.3143842},
             {'VIEW_NAME': 'Kew Royal Botanic Gardens', 'LONGITUDE':-0.2955729999999903, 'LATITUDE':51.4787438},
             {'VIEW_NAME': 'The Sainsbury Laboratory', 'LONGITUDE':1.2228880000000117, 'LATITUDE':52.622316},
             {'VIEW_NAME': 'James Hutton Institute', 'LONGITUDE':-2.158366000000001, 'LATITUDE':57.133131},
             {'VIEW_NAME': 'Aberystwyth University', 'LONGITUDE':-4.0659220000000005, 'LATITUDE':52.417776},
             {'VIEW_NAME': 'Daresbury Laboratory', 'LONGITUDE':-2.6399344000000156, 'LATITUDE':53.34458119999999},
             {'VIEW_NAME': 'Owen Stephens Consulting', 'LONGITUDE':-1.520078900000044, 'LATITUDE':52.28519050000001},
             {'VIEW_NAME': 'Public Health England', 'LONGITUDE':-0.10871080000003985, 'LATITUDE':51.50153030000001},
             {'VIEW_NAME': 'IBM', 'LONGITUDE':-0.1124157000000423, 'LATITUDE':51.5071586},
             {'VIEW_NAME': 'Media Molecule', 'LONGITUDE':-0.5756398999999419, 'LATITUDE':51.2355975}]

other_coords = pd.DataFrame(other_dic)

all_coords = data_coords.append(other_coords)

## Number of People per affiliation
table = data_instructors.groupby(['affiliation']).size()
instructors = table.to_dict()

## Generate Map
m = folium.Map(
    location=[54.00366, -2.547855],
    zoom_start=6)

for key, value in instructors.items():
            long_coords = all_coords[all_coords['VIEW_NAME'] == key]['LONGITUDE']
            lat_coords = all_coords[all_coords['VIEW_NAME'] == key]['LATITUDE']
            if long_coords.empty == False:
                folium.Marker([lat_coords.iloc[0],
                               long_coords.iloc[0]],
                              popup=str(value)).add_to(m)

m.save(dirP + '/data/instructors/Intructors_per_Affiliation.html')
