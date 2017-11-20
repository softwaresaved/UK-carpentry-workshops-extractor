import os
import argparse
import folium
import pandas as pd
import traceback
import glob
import re
import sys

sys.path.append('/lib')
import lib.helper as helper


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

def instructors_per_affiliation(df):
    """
    Creates a dictionary with the values of the number of instructors
    per affiliation.
    """
    table = df.groupby(['affiliation']).size()
    return table.to_dict()

def generate_map(dictionary,df_all,filename,center):
    """
    Generates Map to be visualized.
    """
    maps = folium.Map(
            location=[center[0], center[1]],
            zoom_start=6,
            tiles='cartodbpositron') # for a lighter map tiles='Mapbox Bright'

    for key, value in dictionary.items():
            long_coords = df_all[df_all['VIEW_NAME'] == key]['LONGITUDE']
            lat_coords = df_all[df_all['VIEW_NAME'] == key]['LATITUDE']
            label = folium.Popup(key+ ': ' + str(value), parse_html=True)
            if long_coords.empty == False or lat_coords.empty == False:
                    folium.CircleMarker(
                      radius = 5,
                      location = [lat_coords.iloc[0], long_coords.iloc[0]],
                      popup = label,
                      color = '#ff6600',
                      fill = True,
                      fill_color = '#ff6600').add_to(maps)
            else:
                print('')
                print(key + ' is out of range of our list of coordinates!')
                print('')

    return maps


def main():
    """
    Main function
    """
    args = helper.parse_command_line_paramters()
    print("Mapping instructors affiliation geocoordinates on an interactive map ...")

    if args.instructors_file:
        instructors_file = args.instructors_file
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
        df = helper.load_data_from_csv(instructors_file, ['affiliation'])
        print('Generating map of instructors per affiliation ...')
        df = helper.drop_null_values_from_columns(df, ['affiliation'])
        df = helper.fix_imperial_college_name(df)
        df_values = add_missing_institutions(EXCEL_FILE)
        instructors_dic = instructors_per_affiliation(df)
        maps = generate_map(instructors_dic,df_values[0], instructors_file_name_without_extension,df_values[1])

        ## Save map to a HTML file
        html_map_file = INSTRUCTORS_DATA_DIR + 'map_instructors_per_affiliation_' + instructors_file_name_without_extension + '.html'
        maps.save(html_map_file)
        print('Map of instructors per affiliation saved to HTML file ' + html_map_file)
    except:
        print ("An error occurred while creating the map Excel spreadsheet ...")
        print(traceback.format_exc())
    else:
        if args.google_drive_dir_id:
            try:
                print("Uploading instructors per affiliation map to Google Drive " + html_map_file)
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

