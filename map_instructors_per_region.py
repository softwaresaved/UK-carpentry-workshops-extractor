import os
import json
import folium
import pandas as pd
import shapefile
from shapely.geometry import shape, Point
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


DIR_PATH = os.path.dirname(os.path.realpath(__file__))
findFile = [filename for filename in os.listdir(DIR_PATH + '/data/instructors')
                if filename.startswith("carpentry-instructors_")
                and filename.endswith('.csv')]
if not findFile:
  print('No file was found.')  
else:
  DATA = findFile[-1]
  EXCEL_FILE = DIR_PATH + '/lib/UK-academic-institutions-geodata.xlsx'
  try:
          REGIONS = json.load(open(DIR_PATH + '/lib/regions.json',encoding = 'utf-8-sig'))
  except FileNotFoundError:
          print("Wrong file or file path")

  
def load_instructors_data(filename,dirP):
    """
    Uploads instructors data to a dataframe.
    """
    df = pd.read_csv(dirP + '/data/instructors/' + filename,
                     usecols=['affiliation','nearest_airport_code'])
    return pd.DataFrame(df)

def transform_data(df):
    """
    Removes null values for affiliation and neares_airport_code
    Change Imperial College for the name in UK institutions.
    """
    df.loc[df.affiliation == 'Imperial College London', 'affiliation'] = 'Imperial College of Science, Technology and Medicine'
    df = df.dropna(subset=['affiliation'])
    df = df.dropna(subset=['nearest_airport_code'])
    return df

def add_missing_institutions(filename):
    """
    Add coordinates for missing institutions in excel file.
    """
    try:
        excel_file = pd.ExcelFile(filename)
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
                 {'VIEW_NAME': 'Media Molecule', 'LONGITUDE':-0.5756398999999419, 'LATITUDE':51.2355975}]

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

def generate_map(df_region,regions,dirP,filename):
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
            legend_name='Number of Instructors per region',
            threshold_scale = [0,6,13,20,27])

    ## Find main file date
    date = filename.split('_')[2].replace('.csv','')

    ## Save mapp to html
    path_html = dirP + '/data/instructors/map_instructors_per_region_' + date + '.html'
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
    
def google_drive_upload(html_file,drive):
    """
    Upload map to google drive
    """
    upload_map = drive.CreateFile({'parents': [{"mimeType":"text/plain",
                                                'id': '0B6P79ipNuR8EdDFraGgxMFJaaVE'}],
                                   'title':'map_intructors_per_region_' + date })
    upload_map.SetContentFile(html_file)
    upload_map.Upload({'convert': False})


def main():
    """
    Main function
    """
    df = load_instructors_data(DATA,DIR_PATH)
    df = transform_data(df)
    df_all = add_missing_institutions(EXCEL_FILE)
    df = create_regions_column(df,df_all,REGIONS)
    df_region = instructors_per_region(df)
    print('Generating map...')    
    html_file = generate_map(df_region,REGIONS,DIR_PATH,DATA)
    print('HTML file created.')

##    drive = google_drive_authentication()
##    google_drive_upload(html_file,drive)
##    print('Analysis spreadsheet uploaded to Google Drive.')



if __name__ == '__main__':
    main()
