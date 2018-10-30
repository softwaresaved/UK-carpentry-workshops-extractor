import pandas as pd
import os
import argparse
import sys
import json
import folium
from folium.plugins import MarkerCluster
from folium.plugins import HeatMap
from shapely.geometry import shape, Point
import traceback


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
UK_REGIONS_FILE = CURRENT_DIR + '/UK_regions.json'
NORMALISED_INSTITUTIONS_DICT_FILE = CURRENT_DIR + '/venue-normalised_institutions-dictionary.json'
UK_ACADEMIC_INSTITUTIONS_GEODATA_FILE = CURRENT_DIR + '/UK-academic-institutions-geodata.xlsx'
UK_NON_ACADEMIC_INSTITUTIONS_GEODATA_FILE = CURRENT_DIR + '/UK-non-academic-institutions-geodata.json'

STOPPED_WORKSHOP_TYPES = ['stalled', 'cancelled']  # , 'unresponsive']


def parse_command_line_parameters(arguments_of_interest):
    parser = argparse.ArgumentParser()
    if "-c" in arguments_of_interest:
        parser.add_argument("-c", "--country_code", type=str, help="ISO-3166-1 two-letter country_code code or leave blank for all countries")
    if "-u" in arguments_of_interest:
        parser.add_argument("-u", "--username", type=str, help="Username for logging to AMY")
    if "-p" in arguments_of_interest:
        parser.add_argument("-p", "--password", type=str, help="Password for logging to AMY")
    if "-w" in arguments_of_interest:
        parser.add_argument("-w", "--workshops_file", type=str, default=None,
                            help="An absolute path to the workshops CSV file to analyse/map")
    if "-i" in arguments_of_interest:
        parser.add_argument("-i", "--instructors_file", type=str, default=None,
                            help="An absolute path to instructors CSV file to analyse/map")
    args = parser.parse_args()
    return args


def insert_region_column(df, regions):
    """
    Lookup coordinates from the dataframe and see in which region they fall. Insert the corresponding 'region' column
    in the dataframe.
    """
    print("Finding UK regions for locations. This may take a while, depending on the size of your data ...\n")

    region_list = []
    # Find the region for each longitude, latitude pair and add in a new column
    for index, row in df.iterrows():
        point = Point(row['longitude'], row['latitude'])
        print("Looking for UK region for location " + str(index + 1) + " out of " + str(len(df.index)))
        for feature in regions['features']:
            polygon = shape(feature['geometry'])
            if polygon.contains(point):
                region_list.append(feature['properties']['NAME'])

    ## Add 'region' column
    df.insert(len(df.columns), "region", region_list, allow_duplicates=False)
    return df


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


def drop_null_values_from_columns(df, column_list):
    for column in column_list:
        df = df.dropna(subset=[column])
        df = df.reset_index(drop=True)
    return df


def insert_normalised_institutions_names(df, non_normalised_institution_column):
    """
    Fix names of UK institutions to be the official names, so we can cross reference them with their geocodes later on.
    Use column 'institution' and create new column 'normalised_institution' based off it. For institutions that we do not have
    normanised names, just keep it as is.
    """

    # Index of column 'venue'/'institution' (with workshop venue/not normalised instructor institution), right of which we want to
    # insert the new column containing normalised institution name
    idx = df.columns.get_loc(non_normalised_institution_column)

    normalised_institutions_dict = json.load(open(NORMALISED_INSTITUTIONS_DICT_FILE))

    uk_academic_institutions_df = get_UK_academic_institutions_coords()
    all_uk_institutions_df = uk_academic_institutions_df.append(get_UK_non_academic_institutions_coords()).reset_index(drop=True)

    normalised_institutions = []
    for institution in df[non_normalised_institution_column]:

        if institution in all_uk_institutions_df['VIEW_NAME'].values:
            normalised_institution = institution
        else:
            normalised_institution = normalised_institutions_dict.get(institution.strip(), "Unknown") # Replace with 'Unknown' if you cannot find the mapping

        normalised_institutions.append(normalised_institution)
        if normalised_institution == "Unknown":
            print('For institution "' + institution + '" we do not have the normalised name information. ' +
                  'Setting the institution to "Unknown" ...\n')

    df.insert(loc=idx + 1, column='normalised_institution',
              value=normalised_institutions)  # insert to the right of the column 'venue'/'institution'

    return df


def remove_stopped_workshops(df):
    for tag in STOPPED_WORKSHOP_TYPES:
        df = df[df.tags != tag]
    return df


def get_UK_non_academic_institutions_coords():
    """
    Return coordinates for UK institutions that are not high education providers
    (so are not in the official academic institutions list), but appear in AMY as affiliations of UK instructors.
    This list needs to be periodically updated as more non-academic affiliations appear in AMY.
    """
    non_academic_UK_institutions_coords = json.load(open(UK_NON_ACADEMIC_INSTITUTIONS_GEODATA_FILE))
    return pd.DataFrame(non_academic_UK_institutions_coords)


def get_UK_academic_institutions_coords():
    uk_academic_institutions_geodata_file = pd.ExcelFile(UK_ACADEMIC_INSTITUTIONS_GEODATA_FILE)
    uk_academic_institutions_geodata_df = uk_academic_institutions_geodata_file.parse('UK-academic-institutions')
    return uk_academic_institutions_geodata_df[['VIEW_NAME', 'LONGITUDE', 'LATITUDE']]

def insert_institutional_geocoordinates(df):

    # Get coords for UK academic institutions
    uk_academic_institutions_coords_df = get_UK_academic_institutions_coords()
    # Add coords for UK non academic institutions and academis ones that are not in the official list
    all_uk_institutions_coords_df = uk_academic_institutions_coords_df.append(get_UK_non_academic_institutions_coords()).reset_index(drop=True)

    # Insert latitude and longitude for affiliations, by looking up the all_uk_institutions_coords_df
    idx = df.columns.get_loc("normalised_institution")  # index of column where normalised institution is kept
    df.insert(loc=idx + 1,
                                       column='latitude',
                                       value=None)
    df.insert(loc=idx + 2,
                                       column='longitude',
                                       value=None)
    # replace with the affiliation's latitude and longitude coordinates
    df['latitude'] = df['normalised_institution'].map(
        all_uk_institutions_coords_df.set_index('VIEW_NAME')['LATITUDE'])
    df['longitude'] = df['normalised_institution'].map(
        all_uk_institutions_coords_df.set_index('VIEW_NAME')['LONGITUDE'])

    return df


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
        regions = json.load(open(UK_REGIONS_FILE, encoding='utf-8-sig'))

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
        print(str(index) + ": "+row['institution'])

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
        location = center, #[54.00366, -2.547855],
        zoom_start = 6,
        tiles = 'cartodbpositron')  # for a lighter map tiles='Mapbox Bright'

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

