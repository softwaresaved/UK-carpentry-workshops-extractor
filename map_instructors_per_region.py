import os
import json
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
                               usecols=['nearest_airport_code'])

## Removes null values for airport_code
data_instructors = data_instructors.dropna(subset=['nearest_airport_code'])

##Region Conversions of the existing Airports
regions_excel = pd.ExcelFile(dirP + '/lib/UK-regions-airports.xlsx')
regions = regions_excel.parse('UK-regions-airports')
dict_Regions = area_dict = dict(zip(regions['Airport_code'],
                                    regions['UK_region']))

data_instructors_region = data_instructors.copy()
data_instructors_region['nearest_airport_code'].replace(dict_Regions, inplace=True)

## Number of People per region
DataFrame = pd.core.frame.DataFrame

region_table = DataFrame({'count' :
                          data_instructors_region.groupby(['nearest_airport_code']).size()
                          }).reset_index()
## Import data
state_geo = dirP + '/lib/regions.json'

## Generate Map
m = folium.Map(
    location=[54.00366, -2.547855],
    zoom_start=6
)

m.choropleth(
    geo_data=open(state_geo).read(),
    data=region_table,
    columns=['nearest_airport_code', 'count'],
    key_on='feature.properties.EER13NM',
    fill_color='YlGn',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Number of Instructors per region'
)

m.save(dirP + '/data/instructors/Instructors_per_region.html')
