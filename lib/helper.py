import pandas as pd
import numpy as np
import os
import argparse
import sys
import json
import folium
from folium.plugins import MarkerCluster
from folium.plugins import HeatMap
from shapely.geometry import shape, Point
import traceback
import getpass

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
UK_REGIONS_FILE = CURRENT_DIR + '/UK-regions.json'
UK_AIRPORTS_REGIONS_FILE = CURRENT_DIR + '/UK-airports_regions.csv' # Extracted on 2017-10-16 from https://en.wikipedia.org/wiki/List_of_airports_in_the_United_Kingdom_and_the_British_Crown_Dependencies
NORMALISED_INSTITUTIONS_DICT_FILE = CURRENT_DIR + '/venue-normalised_institutions-dictionary.json'
UK_ACADEMIC_INSTITUTIONS_GEODATA_FILE = CURRENT_DIR + '/UK-academic-institutions-geodata.csv'  # Extracted on 2017-10-27 from http://learning-provider.data.ac.uk/
UK_NON_ACADEMIC_INSTITUTIONS_GEODATA_FILE = CURRENT_DIR + '/UK-non-academic-institutions-geodata.json'

STOPPED_WORKSHOP_TYPES = ['stalled', 'cancelled']  # , 'unresponsive']

UK_AIRPORTS_REGIONS_DF = pd.read_csv(UK_AIRPORTS_REGIONS_FILE, encoding = "utf-8")
UK_REGIONS = json.load(open(UK_REGIONS_FILE), encoding = "utf-8")

def get_uk_non_academic_institutions():
    """
    Return names and coordinates for UK institutions that are not high education providers
    (so are not in the official academic institutions list), but appear in AMY as affiliations of UK instructors.
    This list needs to be periodically updated as more non-academic affiliations appear in AMY.
    """
    non_academic_UK_institutions_coords = json.load(open(UK_NON_ACADEMIC_INSTITUTIONS_GEODATA_FILE))
    return pd.DataFrame(non_academic_UK_institutions_coords)


def get_uk_academic_institutions():
    uk_academic_institutions_geodata_df = pd.read_csv(UK_ACADEMIC_INSTITUTIONS_GEODATA_FILE, encoding="utf-8",
                                                      usecols=['VIEW_NAME', 'LONGITUDE', 'LATITUDE'])
    return uk_academic_institutions_geodata_df


NORMALISED_INSTITUTIONS_DICT = json.load(open(NORMALISED_INSTITUTIONS_DICT_FILE))
UK_ACADEMIC_INSTITUTIONS_DF = get_uk_academic_institutions()
ALL_UK_INSTITUTIONS_DF = UK_ACADEMIC_INSTITUTIONS_DF.append(get_uk_non_academic_institutions())


def parse_command_line_parameters(arguments_of_interest):
    parser = argparse.ArgumentParser()
    if "-c" in arguments_of_interest:
        parser.add_argument("-c", "--country_code", type=str,
                            help="ISO-3166-1 two-letter country_code code or leave blank for all countries")
    if "-u" in arguments_of_interest:
        parser.add_argument("-u", "--username", type=str, help="Username to login to AMY")
    if "-p" in arguments_of_interest:
        parser.add_argument("-p", "--password", type=str, nargs='?', default=argparse.SUPPRESS, help="Password to log in to AMY - you will be prompted for it (do not enter your password on command line)")
    if "-w" in arguments_of_interest:
        parser.add_argument("-w", "--workshops_file", type=str, default=None,
                            help="An absolute path to the workshops CSV file to analyse/map")
    if "-i" in arguments_of_interest:
        parser.add_argument("-i", "--instructors_file", type=str, default=None,
                            help="An absolute path to instructors CSV file to analyse/map")
    args = parser.parse_args()
    if hasattr(args, "password"): #if the -p switch was set - ask user for a password but do not echo it
        if args.password is None:
            args.password = getpass.getpass(prompt='Enter AMY password: ')
    else:
        setattr(args, 'password', None) # the -p switch was not used - add the password argument 'manually' but set it to None
    return args


def create_readme_tab(writer, readme_text):
    """
    Create the README tab in the spreadsheet.
    """
    workbook = writer.book
    worksheet = workbook.add_worksheet('README')
    worksheet.write(0, 0, readme_text)

def create_excel_analyses_spreadsheet(file, df, sheet_name):
    """
    Create an Excel spreadsheet to save the dataframe and various analyses and graphs.
    """
    writer = pd.ExcelWriter(file, engine='xlsxwriter')
    df.to_excel(writer, sheet_name=sheet_name, index = False)
    return writer


def insert_normalised_institution(df, non_normalised_institution_column):
    """
    Fix names of UK institutions to be the official names, so we can cross reference them with their geocodes later on.
    Use column 'institution' and create new column 'normalised_institution' based off it. For institutions that we do not have
    normanised names, just keep it as is.
    """

    # Get the index of column 'venue'/'institution/affiliation' (with non-normalised workshop venue or instructor's institution/affiliation),
    # right to which we want to insert the new column containing normalised institution name
    idx = df.columns.get_loc(non_normalised_institution_column)
    df.insert(loc=idx + 1, column='normalised_institution_name',
              value=df[
                  non_normalised_institution_column])  # insert to the right of the column 'venue'/'institution/affiliation'
    df[df["country_code"] == "GB"]["normalised_institution_name"].map(get_normalised_institution_name,
                                                                      na_action="ignore")
    return df


def get_normalised_institution_name(non_normalised_institution_name):
    if non_normalised_institution_name in ALL_UK_INSTITUTIONS_DF['VIEW_NAME'].values:
        normalised_institution_name = non_normalised_institution_name
    else:
        normalised_institution_name = NORMALISED_INSTITUTIONS_DICT.get(non_normalised_institution_name.strip(),
                                                                       "Unknown")  # Replace with 'Unknown' if you cannot find the mapping

    if normalised_institution_name == "Unknown":
        print(
                    'For institution "' + non_normalised_institution_name + '" we do not have the normalised name information. ' +
                    'Setting the institution to "Unknown" ...\n')
    return normalised_institution_name


def insert_institutional_geocoordinates(df):
    # Insert latitude and longitude for affiliations, by looking up the all_uk_institutions_coords_df
    idx = df.columns.get_loc("normalised_institution_name")  # index of column where normalised institution is kept
    df.insert(loc=idx + 1,
              column='normalised_institution_latitude',
              value=None)
    df.insert(loc=idx + 2,
              column='normalised_institution_longitude',
              value=None)
    # replace with the affiliation's latitude and longitude coordinates
    df['normalised_institution_latitude'] = df['normalised_institution_name'].map(
        ALL_UK_INSTITUTIONS_DF.set_index("VIEW_NAME")['LATITUDE'])
    df['normalised_institution_longitude'] = df['normalised_institution_name'].map(
        ALL_UK_INSTITUTIONS_DF.set_index("VIEW_NAME")['LONGITUDE'])

    return df


def insert_uk_region(df):
    """
    Insert UK region for instructors' airport geocoordinates into new column 'region'.
    """
    df['region'] = df.apply(
        lambda x: get_uk_region(airport_code=x['airport_code'], latitude=x['normalised_institution_latitude'],
                                longitude=x['normalised_institution_longitude']), axis=1)
    return df


def get_uk_region(airport_code, latitude, longitude):
    """
    Lookup UK region given an airport (IATA) code or (latitude, longitude) coordinates of an institution.
    """
    if airport_code is not None and airport_code is not np.nan:
        print("Looking up region for airport " + airport_code)
        region = UK_AIRPORTS_REGIONS_DF.loc[UK_AIRPORTS_REGIONS_DF["airport_code"] == airport_code, 'UK_region']
        if region is not None and region is not []:
            return region.values[0] # should only be one element in the array
    elif latitude is not None and latitude is not np.nan and longitude is not None and longitude is not np.nan:
        print("Looking up region for geocoordinates: (" + str(latitude) + ", " + str(
            longitude) + ")")
        point = Point(longitude, latitude)
        for feature in UK_REGIONS['features']:
            polygon = shape(feature['geometry'])
            if polygon.contains(point):
                return(feature['properties']['NAME'])
        return("Not in a UK region/online")
    else:
        print("Cannot look up region for location - airport_code, latitude, longitude are all missing.")
        return None


def get_center(df):
    # Extract longitude and latitude columns from the dataframe
    coords = df[['latitude', 'longitude']]
    tuples = [tuple(coords) for coords in coords.values]
    x, y = zip(*tuples)

    ## Find center
    center = [(max(x) + min(x)) / 2., (max(y) + min(y)) / 2.]

    return center


def add_UK_regions_layer(map):
    ## Load UK region information from a json file
    try:
        regions = json.load(open(UK_REGIONS_FILE, encoding='utf-8'))

        ## Add to a layer
        folium.GeoJson(regions,
                       name='regions',
                       style_function=lambda feature: {
                           # 'fillColor': '#99ffcc',
                           'color': '#b7b7b7'
                       }).add_to(map)
        folium.LayerControl().add_to(map)
    except:
        print ("An error occurred while reading the UK regions file: " + UK_REGIONS_FILE)
        print(traceback.format_exc())

    return map


def generate_heatmap(df):
    center = get_center(df)

    map = folium.Map(
        location=center,
        zoom_start=6,
        tiles='cartodbpositron')  # for a lighter map tiles='Mapbox Bright'

    lat_long = []
    for index, row in df.iterrows():
        lat_long.append([row['latitude'], row['longitude']])

    HeatMap(lat_long).add_to(map)

    return map


def generate_map_with_circular_markers(df):
    center = get_center(df)

    map = folium.Map(
        location=center,
        zoom_start=6,
        tiles='cartodbpositron')  # for a lighter map tiles='Mapbox Bright'

    for index, row in df.iterrows():
        print(str(index) + ": " + row['institution'])

        # iframe = branca.element.IFrame(html=row['description'], width=300, height=200)
        # popup = folium.Popup(iframe, max_width=500)

        popup = folium.Popup(row['description'], parse_html=True)
        folium.CircleMarker(
            radius=3,
            location=[row['latitude'], row['longitude']],
            popup=popup,
            color='#ff6600',
            fill=True,
            fill_color='#ff6600').add_to(map)

    return map


def generate_map_with_clustered_markers(df):
    """
    Generates a map with clustered markers of a number of locations given in a dataframe.
    """

    center = get_center(df)

    map = folium.Map(
        location=center,
        zoom_start=6,
        tiles='cartodbpositron')  # for a lighter map tiles='Mapbox Bright'

    marker_cluster = MarkerCluster(name='workshops').add_to(map)

    for index, row in df.iterrows():
        popup = folium.Popup(row['description'], parse_html=True)

        folium.CircleMarker(
            radius=5,
            location=[row['latitude'], row['longitude']],
            popup=popup,
            color='#ff6600',
            fill=True,
            fill_color='#ff6600').add_to(marker_cluster)

    return map


def generate_choropleth_map(df, regions, item_type="workshops"):
    """
    Generates a choropleth map of the number of items (instructors or workshops) that can be found
    in each UK region.
    """

    items_per_region_df = pd.DataFrame({'count': df.groupby(['region']).size()}).reset_index()

    center = get_center(df)

    # Creates the threshold scale to be visualized in the map.
    scale_list = items_per_region_df['count'].tolist()
    max_scale = max(scale_list)
    scale = int(max_scale / 5)
    threshold_scale = []
    for each in range(0, max_scale + 1, scale):
        threshold_scale.append(each)

    maps = folium.Map(
        location=center,  # [54.00366, -2.547855],
        zoom_start=6,
        tiles='cartodbpositron')  # for a lighter map tiles='Mapbox Bright'

    maps.choropleth(
        geo_data=regions,
        data=items_per_region_df,
        columns=['region', 'count'],
        key_on='feature.properties.NAME',
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Number of ' + item_type + ' per UK regions',
        threshold_scale=threshold_scale)
    return maps

# def generate_gmaps_heatmap(df):
#     gmaps.configure(api_key=config.api_key)
#
#     lat_list = []
#     long_list = []
#     for index, row in df.iterrows():
#         long_list.append(row['longitude'])
#         lat_list.append(row['latitude'])
#
#     locations = zip(lat_list, long_list)
#
#     ## Resize the map to fit the whole screen.
#     map = gmaps.Map(height='100vh', layout={'height': '100vh'})
#
#     map.add_layer(gmaps.heatmap_layer(locations))
#
#     return map

# def generate_gmaps_map_with_circular_markers(df):
#     """
#     Generates a map from the dataframe where bigger dots indicate bigger counts for a location's geocoordinates.
#     """
#     gmaps.configure(api_key=config.api_key)
#
#     ## Calculate the values for the circle scalling in the map.
#     max_value = df['count'].max()
#     min_value = df['count'].min()
#     grouping = (max_value - min_value) / 3
#     second_value = min_value + grouping
#     third_value = second_value + grouping
#
#     ## Create lists that will hold the found values.
#     names_small = []
#     locations_small = []
#
#     names_medium = []
#     locations_medium = []
#
#     names_large = []
#     locations_large = []
#
#     ## Iterate through the dataframe to find the information needed to fill
#     ## the lists.
#     for index, row in df.iterrows():
#         long_coords = df['longitude']
#         lat_coords = df['latitude']
#         if not long_coords.empty and not lat_coords.empty:
#             if row['count'] >= min_value and row['count'] < second_value:
#                 locations_small.append((lat_coords.iloc[index], long_coords.iloc[index]))
#                 names_small.append(row['normalised_institution'] + ': ' + str(row['count']))
#             elif row['count'] >= second_value and row['count'] < third_value:
#                 locations_medium.append((lat_coords.iloc[index], long_coords.iloc[index]))
#                 names_medium.append(row['normalised_institution'] + ': ' + str(row['count']))
#             elif row['count'] >= third_value and row['count'] <= max_value:
#                 locations_large.append((lat_coords.iloc[index], long_coords.iloc[index]))
#                 names_large.append(row['normalised_institution'] + ': ' + str(row['count']))
#         else:
#             print('For institution "' + row[
#                 'affiliation'] + '" we either have not got coordinates or it is not the official name of an UK '
#                                  'academic institution. Skipping it ...\n')
#
#     ## Add the different markers to different layers corresponding to the
#     ## different amounts of instructors per affiliation.
#     symbol_layer_small = gmaps.symbol_layer(locations_small, fill_color="#ff6600", stroke_color="#ff6600",
#                                             scale=3, display_info_box=True, info_box_content=names_small)
#     symbol_layer_medium = gmaps.symbol_layer(locations_medium, fill_color="#ff6600", stroke_color="#ff6600",
#                                              scale=6, display_info_box=True, info_box_content=names_medium)
#     symbol_layer_large = gmaps.symbol_layer(locations_large, fill_color="#ff6600", stroke_color="#ff6600",
#                                             scale=8, display_info_box=True, info_box_content=names_large)
#
#     ## Resize the map to fit the whole screen.
#     map = gmaps.Map(height='100vh', layout={'height': '100vh'})
#
#     ## Add all the layers to the map.
#     map.add_layer(symbol_layer_small)
#     map.add_layer(symbol_layer_medium)
#     map.add_layer(symbol_layer_large)
#
#     return map
