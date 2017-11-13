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
import pycountry
 
from mpl_toolkits.basemap import Basemap
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from matplotlib.colors import Normalize

warnings.filterwarnings("ignore",category=matplotlib.cbook.mplDeprecation)


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
INSTRUCTORS_DATA_DIR = CURRENT_DIR + '/data/instructors/'
EXCEL_FILE = CURRENT_DIR + '/lib/UK-academic-institutions-geodata.xlsx'


def load_instructors_data(csv_file):
    """
    Uploads instructors data to a dataframe.
    """
    try:
      df = pd.read_csv(csv_file, usecols=['affiliation','nearest_airport_code'])
    except:
      raise
    return pd.DataFrame(df)

def transform_data(df):
    """
    Removes null values for affiliation.
    Change Imperial College for the name in UK institutions.
    """
    df.loc[df.affiliation == 'Imperial College London', 'affiliation'] = 'Imperial College of Science, Technology and Medicine'
    df = df.dropna(subset=['affiliation'])
    df = df.dropna(subset=['nearest_airport_code'])
    return df

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


def create_coordinates_columns(df,df_all):
    """
    Find coordinates and create the respective columns.
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
    return df

def generate_map(df,filename):
    """
    Generates Map to be visualized.
    """
    ax = plt.subplots(figsize=(10,20))

    m = Basemap(resolution='i', # c, l, i, h, f or None
                projection='merc',
                lat_0=58.44, lon_0=-9.26,
                llcrnrlon=-10.9, llcrnrlat= 49.68, urcrnrlon=2.29, urcrnrlat=59.14)

    m.drawmapboundary(fill_color='#46bcec')
    m.fillcontinents(color='grey',lake_color='#46bcec')
    m.drawcoastlines()

    ##Add Markers to the Map
    count = 1
    for row in df.itertuples():
            print('Plotting marker ' + str(count) + ' out of ' +
                  str(len(df.index)))
            x,y = m(row[4].item(),row[3].item())
            m.plot(x, y, 'ro', markersize = 5, marker = 'o')
            count+=1

    plt.title('Map of Instructors per affiliation')

    ## Find suffix
    suffix = filename.split('_',1)[1].replace('.csv','')

    #Save file to png
    img_path = INSTRUCTORS_DATA_DIR + 'map_instructors_per_affiliation_'
    plt.savefig(img_path + suffix,pad_inches=0.0, bbox_inches='tight')
    return img_path + '.png'

    
def google_drive_authentication():
    """
    Authentication to the google drive account
    """
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    return drive

## CHANGE THIS   
def google_drive_upload(filename,drive):
    """
    Upload map to google drive
    """
    upload_map = drive.CreateFile({'parents': [{'id': '0B6P79ipNuR8EdDFraGgxMFJaaVE'}],
                                   'title':'map_intructors_per_affiliation_' + date })
    upload_map.SetContentFile(filename)
    upload_map.Upload({'convert': False})
    

def main():
    """
    Main function
    """

    country_code = ''

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--country_code', default='GB', type=str)
    args = parser.parse_args()

    try:
        pycountry.countries.get(alpha_2=args.country_code)
    except:
        print('The country code submitted does not exist.')
        raise
        
    print("Trying to locate the latest CSV spreadsheet with Carpentry instructors to analyse in directory " + INSTRUCTORS_DATA_DIR + ".")
    instructors_files = [os.path.join(INSTRUCTORS_DATA_DIR,filename) for filename in os.listdir(INSTRUCTORS_DATA_DIR)
                       if filename.startswith("carpentry-instructors_" + str(args.country_code)) and filename.endswith('.csv')]

    if not instructors_files:
        print('No CSV file with Carpentry instructors found in ' + INSTRUCTORS_DATA_DIR + ".")
        print('Exiting...')
        raise SystemExit
    else:
        instructors_file = max(instructors_files, key=os.path.getctime)## if want most recent modification date use getmtime
    
    df = load_instructors_data(instructors_file)
    df = transform_data(df)
    df_all = add_missing_institutions(EXCEL_FILE)
    df = create_coordinates_columns(df,df_all)

    print('Generating map...')    
    image_file = generate_map(df,instructors_file)
    print('Image of instructors per region created - see results in ' +
          image_file + '.')

##    print("Uploading Image of instructors per region to Google Drive ...")    
##    drive = google_drive_authentication()
##    google_drive_upload(image_file,drive)
##    print('Image uploaded to Google Drive.')



if __name__ == '__main__':
    main()
