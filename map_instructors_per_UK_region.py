import os
import argparse
import json
import folium
import pandas as pd
import shapefile
import traceback
import glob
import re
import sys

sys.path.append('/lib')
import lib.helper as helper

from shapely.geometry import shape, Point

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
INSTRUCTORS_DATA_DIR = CURRENT_DIR + '/data/instructors/'
EXCEL_FILE = CURRENT_DIR + '/lib/UK-academic-institutions-geodata.xlsx'
REGIONS_FILE = CURRENT_DIR + '/lib/regions.json'
#GOOGLE_DRIVE_DIR_ID = "0B6P79ipNuR8EdDFraGgxMFJaaVE"

def add_missing_institutions(excel_file):
    """
    Add coordinates for missing institutions in excel file.
    """
    try:
        excel_file = pd.ExcelFile(excel_file)
        df_excel = excel_file.parse('UK-academic-institutions')
    except FileNotFoundError:
        print('The file you were looking for is not found.')
        
    data_coords = df_excel[['VIEW_NAME','LONGITUDE','LATITUDE']]

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
                 {'VIEW_NAME': 'Media Molecule', 'LONGITUDE':-0.5756398999999419, 'LATITUDE':51.2355975},
                 {'VIEW_NAME': 'BBC', 'LONGITUDE':-0.226846, 'LATITUDE':51.510025}]

    other_coords = pd.DataFrame(other_dic)

    ## Merge both dataframes to include all coordinates
    return data_coords.append(other_coords)

def create_regions_column(df,df_all,regions):
    """
    Find coordinates and see in which region they fall and create
    the respective columns.
    """
    ## Create latitude and longitude list to create columns
    latitude = []
    longitude = []

    ## Transform affiliation column into List and find respective coords
    affiliation_list = df['affiliation'].tolist()
    for aff in affiliation_list:
            long_coords = df_all[df_all['VIEW_NAME'] == aff]['LONGITUDE']
            lat_coords = df_all[df_all['VIEW_NAME'] == aff]['LATITUDE']
            latitude.append(lat_coords.iloc[0])
            longitude.append(long_coords.iloc[0])

    ## Add coords to the DataFrame
    df["LATITUDE"] = latitude
    df["LONGITUDE"] = longitude

    ## List corresponding to the region collumn
    list_regions = []

    ## Find the region for each point and add in a new column
    count = 1
    for row in df.itertuples():
            print('Finding region for marker ' + str(count) + ' out of ' +
                  str(len(df.index)))
            point = Point(row[4].item(), row[3].item())
            for feature in regions['features']:
                    polygon = shape(feature['geometry'])
                    if polygon.contains(point):
                            list_regions.append(feature['properties']['NAME'])
            count+=1

    ## Add regions
    df["region"] = list_regions
    return df
    
def instructors_per_region(df):
    """
    Creates a dataframe with the number of instructors per region.
    """
    DataFrame = pd.core.frame.DataFrame
    region_table = DataFrame({'count' : df.groupby(['region']).size()}).reset_index()
    return region_table

def define_threshold_scale(df_region):
    """
    Creates the threshold scale to be visualized in the map
    """
    scale_list = df_region['count'].tolist()
    max_scale = max(scale_list)
    scale = int(max_scale / 5)
    threshold_scale = []
    for each in range(0,max_scale+1,scale):
      threshold_scale.append(each)
    return threshold_scale

def generate_map(df,regions,threshold_scale):
    """
    Generates Map to be visualized.
    """
    maps = folium.Map(
            location=[54.00366, -2.547855],
            zoom_start=6,
            tiles='cartodbpositron') # for a lighter map tiles='Mapbox Bright'

    maps.choropleth(
            geo_data=regions,
            data=df,
            columns=['region', 'count'],
            key_on='feature.properties.NAME',
            fill_color='YlGn',
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name='Number of Instructors per region',
            threshold_scale = threshold_scale)
    return maps

def main():
    """
    Main function
    """
    args = helper.parse_command_line_paramters()
    print("Mapping instructors affiliation geocoordinates into a 'heat map' over UK regions ...")
    print("Note: this map only makes sense to generate with instructors in the UK as it maps them per UK regions.")

    if args.instructors_file:
        instructors_file = args.instructors_file
    else:
        print("Trying to locate the latest CSV spreadsheet with Carpentry instructors to map in " + INSTRUCTORS_DATA_DIR + "\n")
        instructors_files = glob.glob(INSTRUCTORS_DATA_DIR + "carpentry-instructors_GB_*.csv")
        instructors_files.sort(key=os.path.getctime)  # order by creation date

        if not instructors_files[-1]:  # get the last element
            print('No CSV file with Carpentry instructors found in ' + INSTRUCTORS_DATA_DIR + ". Exiting ...")
            sys.exit(1)
        else:
            instructors_file = instructors_files[-1]

    instructors_file_name = os.path.basename(instructors_file)
    instructors_file_name_without_extension = re.sub('\.csv$', '', instructors_file_name.strip())
    print("The CSV spreadsheet with Carpentry instructors to be mapped: " + instructors_file)

    try:
        regions = json.load(open(REGIONS_FILE, encoding='utf-8-sig'))
    except:
        print ("An error occurred while reading the UK regions file " + REGIONS_FILE)
        print(traceback.format_exc())
    else:
        try:
            df = helper.load_data_from_csv(instructors_file, ['affiliation','nearest_airport_code'])
            df = helper.transform_data('b',df)
            df_all = add_missing_institutions(EXCEL_FILE)
            df = create_regions_column(df,df_all,regions)    
            instructors_per_region_df = instructors_per_region(df)
            print('Generating map of instructors per UK regions ...')
            threshold_scale = define_threshold_scale(instructors_per_region_df)
            maps = generate_map(instructors_per_region_df, regions, threshold_scale)

            ## Save map to a HTML file
            html_map_file = INSTRUCTORS_DATA_DIR + 'map_per_UK_regions_' + instructors_file_name_without_extension + '.html'
            maps.save(html_map_file)
            print('Map of Instructors per region saved to HTML file ' + html_map_file)
        except:
            print ("An error occurred while creating the map Excel spreadsheet ...")
            print(traceback.format_exc())
        else:
            if args.google_drive_dir_id:
                try:
                    print("Uploading instructors per region map to Google Drive " + html_map_file)
                    drive = helper.google_drive_authentication()
                    helper.google_drive_upload(html_map_file,
                                               drive,
                                               [{'mimeType': 'text/plain', 'id': args.google_drive_dir_id}],
                                               False)
                    print('Map uploaded to Google Drive.')
                except Exception:
                    print ("An error occurred while uploading the map to Google Drive ...")
                    print(traceback.format_exc())


if __name__ == '__main__':
    main()
