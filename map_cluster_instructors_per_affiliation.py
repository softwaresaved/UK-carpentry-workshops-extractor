import os
import folium
import json
import pandas as pd
from folium.plugins import MarkerCluster
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


def load_instructors_data(filename,dirP):
    """
    Uploads instructors data to a dataframe.
    """
    df = pd.read_csv(dirP + '/data/instructors/' + filename,
                     usecols=['affiliation'])
    return pd.DataFrame(df)

def transform_data(df):
    """
    Removes null values for affiliation.
    Change Imperial College for the name in UK institutions.
    """
    df.loc[df.affiliation == 'Imperial College London', 'affiliation'] = 'Imperial College of Science, Technology and Medicine'
    return df.dropna(subset=['affiliation'])

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

def generate_map(df,df_all,dirP,filename):
    """
    Generates Map to be visualized.
    """
    ## Transform affiliation column into List
    affiliation_list = df['affiliation'].tolist()

    m = folium.Map(
            location=[54.00366, -2.547855],
            zoom_start=6,
            tiles='cartodbpositron') # for a lighter map tiles='Mapbox Bright'

    marker_cluster = MarkerCluster(name = 'instructors').add_to(m)

    for aff in affiliation_list:
            long_coords = df_all[df_all['VIEW_NAME'] == aff]['LONGITUDE']
            lat_coords = df_all[df_all['VIEW_NAME'] == aff]['LATITUDE']
            popup = folium.Popup(aff, parse_html=True)
            if long_coords.empty == False:
                    folium.Marker(
                            location=[lat_coords.iloc[0], long_coords.iloc[0]],
                            popup=popup
                            ).add_to(marker_cluster)

    ## Region information json
    regions = json.load(open(dirP + '/lib/regions.json'))

    ## Add to a layer
    folium.GeoJson(regions,
                   name='regions',
                   style_function=lambda feature: {
                           'fillColor': '#99ffcc',
                           'color': '#00cc99'
                           }).add_to(m)
    folium.LayerControl().add_to(m)

    ## Find main file date
    date = filename.split('_')[2].replace('.csv','')

    ## Save mapp to html
    path_html = dirP + '/data/instructors/map_cluster_intructors_per_affiliation_' + date + '.html'
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
                                   'title':'map_cluster_intructors_per_affiliation_' + date })
    upload_map.SetContentFile(html_file)
    upload_map.Upload({'convert': False})


def main():
    """
    Main function
    """
    df = load_instructors_data(DATA,DIR_PATH)
    df = transform_data(df)
    df_all = add_missing_institutions(EXCEL_FILE)
    print('Generating map...')    
    html_file = generate_map(df,df_all,DIR_PATH,DATA)
    print('HTML file created.')

##    drive = google_drive_authentication()
##    google_drive_upload(html_file,drive)
##    print('Analysis spreadsheet uploaded to Google Drive.')



if __name__ == '__main__':
    main()
