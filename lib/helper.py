import pandas as pd
import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import argparse
import sys
import json
# import gmaps
import config
import folium
from folium.plugins import MarkerCluster
from folium.plugins import HeatMap
from shapely.geometry import shape, Point
# import branca

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

UK_REGIONS_FILE = CURRENT_DIR + '/UK_regions.json'

# GOOGLE_DRIVE_DIR_ID = "0B6P79ipNuR8EdDFraGgxMFJaaVE"


def load_data_from_csv(csv_file, columns=None):
    """
    Loads data from a CSV file into a dataframe with an optional list of columns to load.
    """
    df = pd.read_csv(csv_file, usecols=columns)
    return pd.DataFrame(df)


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


def google_drive_authentication():
    """
    Authentication to a Google Drive account
    """
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    return drive


def google_drive_upload(file, drive, parents_list, convert):
    """
    Upload a file to a folder in Google Drive
    """
    gfile = drive.CreateFile({'parents': parents_list,
                              'title': os.path.basename(file)})
    gfile.SetContentFile(file)
    gfile.Upload({'convert': convert})




def parse_command_line_paramters():
    parser = argparse.ArgumentParser()
    if "workshop" in os.path.basename(sys.argv[0]): # e.g. the name of the script is 'analyse_workshops'
        parser.add_argument('-w', '--workshops_file', type=str, default=None,
                            help='an absolute path to the workshops CSV file to analyse/map')
    elif "instructor" in os.path.basename(sys.argv[0]):
        parser.add_argument('-i', '--instructors_file', type=str, default=None,
                            help='an absolute path to instructors CSV file to analyse/map')
    else:
        print("You are possibly not invoking the correct python script - analyse_workshops.py or analyse_instructors.py.")
        exit(1)

    parser.add_argument('-gid', '--google_drive_dir_id', type=str,
                        help='ID of a Google Drive directory where to upload the analyses and map files to')
    args = parser.parse_args()
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

def drop_null_values_from_columns(df, column_list):
    for column in column_list:
        df = df.dropna(subset=[column])
        df = df.reset_index(drop=True)
    return df

def fix_UK_academic_institutions_names(df):
    """
    Fix names of academic institutions to be the official names, so we can cross reference them with their geocodes later on.
    """
    df.loc[df.institution == 'Imperial College London', 'institution'] = 'Imperial College of Science, Technology and Medicine'
    df.loc[df.institution == 'Queen Mary University of London', 'institution'] = 'Queen Mary and Westfield College, University of London'
    df.loc[df.institution == 'Aberystwyth University', 'institution'] = 'Prifysgol Aberystwyth'
    return df

def remove_stopped_workshops(df, tag_list):
    for tag in tag_list:
        df = df[df.tags != tag]
    return df

def get_UK_non_academic_institutions_coords():
    """
    Return coordinates for UK institutions that are not high education providers
    (so are not in the official academic institutions list), but appear in AMY as affiliations of UK instructors.
    This list needs to be periodically updated as more non-academic affiliations appear in AMY.
    """
    non_academic_UK_institutions_coords = json.load(open(CURRENT_DIR + '/UK-non-academic-institutions-geodata.json'))
    return pd.DataFrame(non_academic_UK_institutions_coords)

def insert_institutions_geocoordinates(df, affiliations_geocoordinates_df):
    # Insert latitude and longitude for affiliations, by looking up the all_uk_institutions_coords_df
    idx = df.columns.get_loc("institution")  # index of column where 'institution' is kept
    df.insert(loc=idx + 1,
                                       column='latitude',
                                       value=None)  # copy values from 'institution' column and insert to the right
    df.insert(loc=idx + 2,
                                       column='longitude',
                                       value=None)  # copy values from 'institution' column and insert to the right
    # replace with the affiliation's latitude and longitude coordinates
    df['latitude'] = df['institution'].map(
        affiliations_geocoordinates_df.set_index('VIEW_NAME')['LATITUDE'])
    df['longitude'] = df['institution'].map(
        affiliations_geocoordinates_df.set_index('VIEW_NAME')['LONGITUDE'])

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
#                 names_small.append(row['institution'] + ': ' + str(row['count']))
#             elif row['count'] >= second_value and row['count'] < third_value:
#                 locations_medium.append((lat_coords.iloc[index], long_coords.iloc[index]))
#                 names_medium.append(row['institution'] + ': ' + str(row['count']))
#             elif row['count'] >= third_value and row['count'] <= max_value:
#                 locations_large.append((lat_coords.iloc[index], long_coords.iloc[index]))
#                 names_large.append(row['institution'] + ': ' + str(row['count']))
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

