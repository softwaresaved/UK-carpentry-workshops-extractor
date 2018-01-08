import os
import argparse
import folium
import pandas as pd
import traceback
import gmaps
import config
import glob
import re
import sys

sys.path.append('/lib')
import lib.helper as helper

from ipywidgets.embed import embed_minimal_html


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
INSTRUCTORS_DATA_DIR = CURRENT_DIR + '/data/instructors/'
UK_INSTITUTIONS_GEODATA_FILE = CURRENT_DIR + '/lib/UK-academic-institutions-geodata.xlsx'


def generate_map(instructors_affiliations, institutions_coords_df, center):
    """
    Generates a map of the number of instructors per affiliation.
    """
    gmaps.configure(api_key=config.api_key)

    ## Calculate the values for the circle scalling in the map.
    max_value = instructors_affiliations['count'].max()
    min_value = instructors_affiliations['count'].min()
    grouping = (max_value - min_value)/3
    second_value = min_value + grouping
    third_value = second_value + grouping

    ## Create lists that will hold the found values.
    names_small = []
    locations_small = []
    
    names_medium = []
    locations_medium = []

    names_large = []
    locations_large = []

    ## Iterate through the datafrane to found the information needed to fill
    ## the lists.
    for index, row in instructors_affiliations.iterrows():
        long_coords = institutions_coords_df[institutions_coords_df['VIEW_NAME'] == row['affiliation']]['LONGITUDE']
        lat_coords = institutions_coords_df[institutions_coords_df['VIEW_NAME'] == row['affiliation']]['LATITUDE']
        if not long_coords.empty and not lat_coords.empty:
            if row['count']>=min_value and row['count']<second_value:
                locations_small.append((lat_coords.iloc[0],long_coords.iloc[0]))
                names_small.append(row['affiliation'] + ': ' + str(row['count']))
            elif row['count']>=second_value and row['count']<third_value:
                locations_medium.append((lat_coords.iloc[0],long_coords.iloc[0]))
                names_medium.append(row['affiliation'] + ': ' + str(row['count']))
            elif row['count']>=third_value and row['count']<=max_value:
                locations_large.append((lat_coords.iloc[0],long_coords.iloc[0]))
                names_large.append(row['affiliation'] + ': ' + str(row['count']))
        else:
            print('For institution "' + row['affiliation'] + '" we either have not got coordinates or it is not the official name of an UK '
                  'academic institution. Skipping it ...\n')

    ## Add the different markers to a different layers corresponding to the
    ## different amounts of instructors per affiliation.
    symbol_layer_small = gmaps.symbol_layer(locations_small, fill_color="#ff6600", stroke_color="#ff6600",
                                      scale=3, display_info_box = True, info_box_content=names_small)
    symbol_layer_medium = gmaps.symbol_layer(locations_medium, fill_color="#ff6600", stroke_color="#ff6600",
                                      scale=6, display_info_box = True, info_box_content=names_medium)
    symbol_layer_large = gmaps.symbol_layer(locations_large, fill_color="#ff6600", stroke_color="#ff6600",
                                      scale=8, display_info_box = True, info_box_content=names_large)

    ## Resize the map to fit the whole screen.
    map = gmaps.Map(height='100vh', layout={'height': '100vh'})

    ## Add all the layers to the map.
    map.add_layer(symbol_layer_small)
    map.add_layer(symbol_layer_medium)
    map.add_layer(symbol_layer_large)

    return map

def generate_heatmap(instructors_affiliations, institutions_coords_df):
    """
    Generates a heatmap of the number of instructors per affiliation.
    """
    gmaps.configure(api_key=config.api_key)

    ## Create lat and long list and fill it with the information from the
    ## dataframe.
    lat_list = []
    long_list = []
    for index, row in instructors_affiliations.iterrows():
        long_coords = institutions_coords_df[institutions_coords_df['VIEW_NAME'] == row['affiliation']]['LONGITUDE']
        lat_coords = institutions_coords_df[institutions_coords_df['VIEW_NAME'] == row['affiliation']]['LATITUDE']
        if not long_coords.empty and not lat_coords.empty:
            long_list.append(long_coords.iloc[0])
            lat_list.append(lat_coords.iloc[0])

    ## Create a list of tuples with the following format
    ## [(lat1,long1),(lat2,long2),...,(latx,longx)]      
    locations = zip(lat_list, long_list)

    ## Resize the map to fit the full browser screen.
    map = gmaps.Map(height='100vh', layout={'height': '100vh'})
    
    ## Add heatmap layer to the map
    map.add_layer(gmaps.heatmap_layer(locations))

    return map
    
def main():
    """
    Main function
    """
    args = helper.parse_command_line_paramters()
    print("Mapping instructors affiliation geocoordinates on an interactive map and a heatmap ...\n")
    print("Note: this map only makes sense to generate with instructors in the UK as it cross references their affiliations with geocoordinates of UK institutions.\n")

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
            print("Generating a map and heatmap of instructors' affiliations ...")
            df = helper.drop_null_values_from_columns(df, ['affiliation'])
            df = helper.fix_UK_academic_institutions_names(df)

            uk_academic_institutions_coords_df = uk_academic_institutions_df[['VIEW_NAME', 'LONGITUDE', 'LATITUDE']]
            all_uk_institutions_coords_df = uk_academic_institutions_coords_df.append(
                helper.get_UK_non_academic_institutions_coords())
            center = helper.get_center(all_uk_institutions_coords_df)

            instructors_affiliations_df = pd.core.frame.DataFrame({'count': df.groupby(['affiliation']).size()}).reset_index()
            
            map = generate_map(instructors_affiliations_df, all_uk_institutions_coords_df, center)
            heatmap = generate_heatmap(instructors_affiliations_df, all_uk_institutions_coords_df)

            # Save maps to HTML files
            map_file = INSTRUCTORS_DATA_DIR + 'map_instructors_affiliations_' + instructors_file_name_without_extension + '.html'
            embed_minimal_html(map_file, views=[map])
            print("Map of instructors' affiliations saved to HTML file " + map_file + "\n")
            
            heatmap_file = INSTRUCTORS_DATA_DIR + 'heatmap_instructors_affiliations_' + instructors_file_name_without_extension + '.html'
            embed_minimal_html(heatmap_file, views=[heatmap])
            print("Heatmap of instructors' affiliations saved to HTML file " + heatmap_file + "\n")
            
        except:
            print ("An error occurred while creating the map of instructors' affiliations ...")
            print(traceback.format_exc())
        else:
            if args.google_drive_dir_id:
                try:
                    print("Uploading instructors' affiliations map " + map_file + " to Google Drive.\n")
                    drive = helper.google_drive_authentication()
                    helper.google_drive_upload(map_file,
                                               drive,
                                               [{'mimeType': 'text/plain', 'id': args.google_drive_dir_id}],
                                               False)
                    print("Map uploaded to Google Drive.\n")

                    print("Uploading instructors' affiliations heatmap " + html_heatmap_file + " to Google Drive.\n")
                    helper.google_drive_upload(html_heatmap_file,
                                               drive,
                                               [{'mimeType': 'text/plain', 'id': args.google_drive_dir_id}],
                                               False)
                    print("Heatmap uploaded to Google Drive.\n")

                except Exception:
                    print ("An error occurred while uploading the map to Google Drive ...")
                    print(traceback.format_exc())


if __name__ == '__main__':
    main()

