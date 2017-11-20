## If problems installing basemap manually use
## http://www.lfd.uci.edu/~gohlke/pythonlibs/#basemap
import os
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm
import warnings
import json
import traceback
import glob
import re
import sys

sys.path.append('/lib')
import lib.helper as helper

from mpl_toolkits.basemap import Basemap
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from matplotlib.colors import Normalize

warnings.filterwarnings("ignore",category=matplotlib.cbook.mplDeprecation)


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
INSTRUCTORS_DATA_DIR = CURRENT_DIR + '/data/instructors/'
EXCEL_FILE = CURRENT_DIR + '/lib/UK-academic-institutions-geodata.xlsx'
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
    all_coords = data_coords.append(other_coords)

    ## List of Tuples for longitude and latitude
    subset = all_coords[['LATITUDE', 'LONGITUDE']]
    tuples = [tuple(coords) for coords in subset.values]
    x,y=zip(*tuples)
    ## Find center
    center=(max(x)+min(x))/2., (max(y)+min(y))/2.
    return all_coords,center

def generate_map(df,center):
    """
    Generates Map to be visualized.
    """
    ax = plt.subplots(figsize=(10,20))
    maps = Basemap(resolution='i', # c, l, i, h, f or None
                projection='merc',
                lat_0=center[0], lon_0=center[1],
                llcrnrlon=-10.9, llcrnrlat= 49.68, urcrnrlon=2.29, urcrnrlat=59.14)

    maps.drawmapboundary(fill_color='#46bcec')
    maps.fillcontinents(color='grey',lake_color='#46bcec')
    maps.drawcoastlines()
    
    ##Add Markers to the Map
    count = 1
    for row in df.itertuples():
            print('Plotting marker ' + str(count) + ' out of ' +
                  str(len(df.index)))
            x,y = maps(row[2].item(),row[1].item())
            maps.plot(x, y, 'ro', markersize = 5, marker = 'o')
            count+=1

    plt.title('Map of Instructors per affiliation')

    return maps
    
def main():
    """
    Main function
    """
    args = helper.parse_command_line_paramters()
    print("Mapping instructors affiliation geocoordinates on an interactive map ...")

    if args.instructors_file:
        instructors_file = INSTRUCTORS_DATA_DIR + args.instructors_file
        print("The CSV spreadsheet with Carpentry instructors to be mapped: " + args.instructors_file)
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
    print('CSV file with Carpentry instructors to analyse ' + instructors_file_name)

    try:
        df = helper.load_data_from_csv(instructors_file, ['affiliation','nearest_airport_code'])
        df = helper.drop_null_values_from_columns(df, ['affiliation', 'nearest_airport_code'])
        df = helper.fix_imperial_college_name(df)
        df = add_missing_institutions(EXCEL_FILE)
        print('Generating map of instructors per affiliation ...')
        maps = generate_map(df[0],df[1])
        
        ## Save map to a PNG file
        img_map_file = INSTRUCTORS_DATA_DIR + 'map_instructors_per_affiliation_' + instructors_file_name_without_extension + '.png'
        plt.savefig(img_map_file,pad_inches=0.0, bbox_inches='tight')
        print('Map of instructors per affiliation saved to image file ' + img_map_file)
    except:
        print ("An error occurred while creating the map image ...")
        print(traceback.format_exc())
    else:
        if args.google_drive_dir_id:
            try:
                print("Uploading instructors per affiliation map to Google Drive " + img_map_file)
                drive = helper.google_drive_authentication()
                helper.google_drive_upload(img_map_file,
                                           drive,
                                           [{'id': args.google_drive_dir_id}],
                                           False)
                print('Map uploaded to Google Drive.')
            except Exception:
                print ("An error occurred while uploading instructors per affiliation map to Google Drive ...")
                print(traceback.format_exc())



if __name__ == '__main__':
    main()
