import os
import argparse
import folium
import json
import pandas as pd
import traceback
import glob
import re
import sys

sys.path.append('/lib')
import lib.helper as helper

from folium.plugins import MarkerCluster

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
INSTRUCTORS_DATA_DIR = CURRENT_DIR + '/data/instructors/'
UK_INSTITUTIONS_GEODATA_FILE = CURRENT_DIR + '/lib/UK-academic-institutions-geodata.xlsx'


def generate_map(df,df_all,center):
    """
    Generates a cluster map of the number of instructors per affiliation.
    """
    maps = folium.Map(
        location=[center[0], center[1]],
        zoom_start=6,
        tiles='cartodbpositron') # for a lighter map tiles='Mapbox Bright'

    marker_cluster = MarkerCluster(name = 'instructors').add_to(maps)

    for index,row in df.iterrows():
        long_coords = df_all[df_all['VIEW_NAME'] == row['affiliation']]['LONGITUDE']
        lat_coords = df_all[df_all['VIEW_NAME'] == row['affiliation']]['LATITUDE']
        popup = folium.Popup(row['affiliation'], parse_html=True)
        if not long_coords.empty and not lat_coords.empty:
            folium.CircleMarker(
                radius = 5,
                location = [lat_coords.iloc[0], long_coords.iloc[0]],
                popup = popup,
                color = '#ff6600',
                fill = True,
                fill_color = '#ff6600').add_to(marker_cluster)
        else:
            print('For affiliation "' + row['affiliation'] + '" we either have not got coordinates or it is not the official name of an UK '
                                                             'academic institution. Skipping it ...\n')


    ## Region information json
    regions = json.load(open(CURRENT_DIR + '/lib/regions.json'))

    ## Add to a layer
    folium.GeoJson(regions,
                   name='regions',
                   style_function=lambda feature: {
                       'fillColor': '#99ffcc',
                       'color': '#00cc99'
                   }).add_to(maps)
    folium.LayerControl().add_to(maps)

    return maps


def main():
    """
    Main function
    """
    args = helper.parse_command_line_paramters()
    print("Mapping instructors affiliation geocoordinates into clusters on an interactive map ...")

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
        uk_academic_institutions_excel_file = pd.ExcelFile(UK_INSTITUTIONS_GEODATA_FILE)
        uk_academic_institutions_df = uk_academic_institutions_excel_file.parse('UK-academic-institutions')
    except:
        print (
            "An error occurred while reading the UK academic institutions' geodata file " + UK_INSTITUTIONS_GEODATA_FILE)
    else:
        try:
            df = helper.load_data_from_csv(instructors_file, ['affiliation'])
            df = helper.drop_null_values_from_columns(df, ['affiliation'])
            df = helper.fix_UK_academic_institutions_names(df)

            uk_academic_institutions_coords_df = uk_academic_institutions_df[['VIEW_NAME', 'LONGITUDE', 'LATITUDE']]
            all_uk_institutions_coords_df = uk_academic_institutions_coords_df.append(
                helper.get_UK_non_academic_institutions_coords())
            center = helper.get_center(all_uk_institutions_coords_df)

            print('Generating a clustered map of instructors per affiliation ...')
            maps = generate_map(df, all_uk_institutions_coords_df, center)

            ## Save map to a HTML file
            html_map_file = INSTRUCTORS_DATA_DIR + 'map_clustered_instructors_per_affiliation_' + instructors_file_name_without_extension + '.html'
            maps.save(html_map_file)
            print('Map of instructors affiliations saved to HTML file ' + html_map_file)
        except:
            print ("An error occurred while creating a clustered map of instructors per affiliation ...")
            print(traceback.format_exc())
        else:
            if args.google_drive_dir_id:
                try:
                    print("Uploading instructors affiliations map to Google Drive " + html_map_file)
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
