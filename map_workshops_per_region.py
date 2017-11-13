import os
import argparse
import json
import folium
import pandas as pd
import shapefile
import pycountry
from shapely.geometry import shape, Point
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
WORKSHOP_DATA_DIR = CURRENT_DIR + '/data/workshops/'
try:
  REGIONS = json.load(open(CURRENT_DIR + '/lib/regions.json',encoding = 'utf-8-sig'))
except FileNotFoundError:
  print("Wrong file or file path")

def load_workshops_data(csv_file):
    """
    Uploads instructors data to a dataframe.
    """
    try:
        df = pd.read_csv(csv_file, usecols=['venue','latitude','longitude'])
    except:
      raise
    return pd.DataFrame(df)

def create_regions_column(df, regions):
    """
    Find coordinates and see in which region they fall and create
    the respective columns.
    """

    ## List corresponding to the region collumn
    list_regions = []

    ## Find the region for each point and add in a new column
    count = 1
    for row in df.itertuples():
            print('Finding region for marker ' + str(count) + ' out of ' +
                  str(len(df.index)))
            point = Point(row[3].item(), row[2].item())
            for feature in regions['features']:
                    polygon = shape(feature['geometry'])
                    if polygon.contains(point):
                            list_regions.append(feature['properties']['NAME'])
            count+=1

    ## Add regions
    df["region"] = list_regions
    return df

def workshops_per_region(df):
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

def generate_map(df_region,regions,filename,threshold_scale):
    """
    Generates Map to be visualized.
    """
    m = folium.Map(
            location=[54.00366, -2.547855],
            zoom_start=6,
            tiles='cartodbpositron') # for a lighter map tiles='Mapbox Bright'

    m.choropleth(
            geo_data=regions,
            data=df_region,
            columns=['region', 'count'],
            key_on='feature.properties.NAME',
            fill_color='YlGn',
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name='Number of Workshops per region',
            threshold_scale = threshold_scale)

    ## Find suffix
    suffix = filename.split('_',1)[1].replace('.csv','')
    print(filename.split('_',1))

    ## Save mapp to html
    path_html = WORKSHOP_DATA_DIR + 'map_workshops_per_region_' + suffix + '.html'
    m.save(path_html)
    return path_html

def google_drive_authentication():
    """
    Authentication to the google drive account
    """
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    return drive
    
def google_drive_upload(file,drive):
    """
    Upload map to google drive
    """
    upload_map = drive.CreateFile({'parents': [{"mimeType":"text/plain",
                                                'id': '0B6P79ipNuR8EdDFraGgxMFJaaVE'}],
                                   'title':os.path.basename(file)})
    upload_map.SetContentFile(html_file)
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
        
    print("Trying to locate the latest CSV spreadsheet with Carpentry workshops_ to analyse in directory " + WORKSHOP_DATA_DIR + ".")
    workshops_files = [os.path.join(WORKSHOP_DATA_DIR,filename) for filename in os.listdir(WORKSHOP_DATA_DIR)
                       if filename.startswith("carpentry-workshops_" + str(args.country_code)) and filename.endswith('.csv')]

    if not workshops_files:
        print('No CSV file with Carpentry workshops_ found in ' + WORKSHOP_DATA_DIR + ".")
        print('Exiting...')
        raise SystemExit
    else:
        workshops_file = max(workshops_files, key=os.path.getctime)## if want most recent modification date use getmtime

    
    df = load_workshops_data(workshops_file)
    df = create_regions_column(df,REGIONS)
    df_region = workshops_per_region(df)
    print('Generating map...')
    threshold_scale = define_threshold_scale(df_region)
    html_file = generate_map(df_region,REGIONS,workshops_file,threshold_scale)
    print('Map of workshops per region created - see results in ' +
          html_file + '.')
    
##    print("Uploading Map of workshops per region to Google Drive ...")
##    drive = google_drive_authentication()
##    google_drive_upload(html_file,drive)
##    print('Map uploaded to Google Drive.')


if __name__ == '__main__':
    main()
