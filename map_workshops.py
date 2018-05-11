import os
import traceback
import glob
import re
import sys
import json
import numpy as np

sys.path.append('/lib')
import lib.helper as helper

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
WORKSHOPS_DATA_DIR = CURRENT_DIR + '/data/workshops/'
UK_REGIONS_FILE = CURRENT_DIR + '/lib/UK_regions.json'


def main():
    """
    Main function
    """
    args = helper.parse_command_line_paramters()
    print("Mapping workshop venues into various maps ... \n")

    if args.workshops_file:
        workshops_file = args.workshops_file
        print("The CSV spreadsheet with Carpentry workshops to be mapped: " + args.workshops_file + "\n")
    else:
        print(
            "Trying to locate the latest CSV spreadsheet with Carpentry workshops to map in " + WORKSHOPS_DATA_DIR + "\n")
        workshops_files = glob.glob(WORKSHOPS_DATA_DIR + "carpentry-workshops_*.csv")
        workshops_files.sort(key=os.path.getctime)  # order by creation date

        if not workshops_files:
            print('No CSV file with Carpentry workshops found in ' + WORKSHOPS_DATA_DIR + ". Exiting ...")
            sys.exit(1)
        else:
            workshops_file = workshops_files[-1]  # get the last element

    workshops_file_name = os.path.basename(workshops_file)
    workshops_file_name_without_extension = re.sub('\.csv$', '', workshops_file_name.strip())
    print('Found CSV file with Carpentry workshops to mapped: ' + workshops_file + "\n")

    try:
        workshops_df = helper.load_data_from_csv(workshops_file, ['venue', 'address', 'latitude', 'longitude'])
        # Rename 'venue' column to 'institution' as some of out methods expect that column
        workshops_df.rename(columns={"venue": "institution"}, inplace=True)
        # Add column 'description' which is used in popups in maps
        workshops_df['description'] = np.where(workshops_df["address"].empty, workshops_df["institution"], workshops_df["institution"] + ', ' + workshops_df["address"])
    except:
        print ("An error occurred while loading workshops' data and preparing it for mapping...\n")
        print(traceback.format_exc())
    else:
        # Map with clustered markers
        try:
            print("#####################################################################")
            print("Map 1: generating a map of workshop venues as clusters of markers ...")
            print("#####################################################################\n")

            map = helper.generate_map_with_clustered_markers(workshops_df)
            if "GB" in workshops_file:  # if the data is for UK workshops - add layer with UK regions to the map
                map = helper.add_UK_regions_layer(map)

            # Save map to a HTML file
            map_file = WORKSHOPS_DATA_DIR + 'map_clustered_workshop_venues_' + workshops_file_name_without_extension + '.html'
            map.save(map_file)
            print('Map of workshop venues saved to HTML file ' + map_file + '\n')

        except:
            print ("An error occurred while creating the map of workshop venues  ...")
            print(traceback.format_exc())
        else:
            if args.google_drive_dir_id:
                try:
                    print("Uploading workshop venues map to Google Drive " + map_file)
                    drive = helper.google_drive_authentication()
                    helper.google_drive_upload(map_file,
                                               drive,
                                               [{'mimeType': 'text/plain', 'id': args.google_drive_dir_id}],
                                               False)
                    print('Map uploaded to Google Drive.')
                except Exception:
                    print ("An error occurred while uploading the map to Google Drive ...")
                    print(traceback.format_exc())

        # A map of workshop venues with circular markers.
        try:
            print("####################################################################")
            print('Map 2: generating a map of workshop venues with circular markers...')
            print("####################################################################\n")

            map = helper.generate_map_with_circular_markers(workshops_df)

            # Save the map to an HTML file
            map_file = WORKSHOPS_DATA_DIR + 'map_workshop_venues_' + workshops_file_name_without_extension + '.html'
            map.save(map_file)
            print("A map of workshop venues with circular markers saved to HTML file " + map_file + "\n")

            # Old code with Google maps that requires Google API key
            # map = helper.generate_gmap_map_with_circular_markers(df)
            # embed_minimal_html(map_file, views=[map])
        except:
            print ("An error occurred while creating a heatmap of instructor affiliations ...\n")
            print(traceback.format_exc())
        else:
            if args.google_drive_dir_id:
                try:
                    print("Uploading a heatmap of instructor affiliations to Google Drive " + map_file)
                    drive = helper.google_drive_authentication()
                    helper.google_drive_upload(map_file,
                                               drive,
                                               [{'mimeType': 'text/plain', 'id': args.google_drive_dir_id}],
                                               False)
                    print('Map uploaded to Google Drive.')
                except Exception:
                    print ("An error occurred while uploading the map to Google Drive...\n")
                    print(traceback.format_exc())

        # A heatmap of workshop venues.
        try:
            print("###################################################")
            print('Map 3: Generating a heatmap of workshop venues ...')
            print("###################################################\n")

            map = helper.generate_heatmap(workshops_df)

            # Save the heatmap to an HTML file
            map_file = WORKSHOPS_DATA_DIR + 'heatmap_workshop_venues_' + workshops_file_name_without_extension + '.html'
            map.save(map_file)
            print("Heatmap of instructors' affiliations saved to HTML file " + map_file + "\n")

            # Old code with Google maps that requires Google API key
            # heatmap = helper.generate_gmaps_heatmap(df)
            # embed_minimal_html(html_heatmap_file, views=[heatmap])
        except:
            print ("An error occurred while creating a heatmap of instructor affiliations ...\n")
            print(traceback.format_exc())
        else:
            if args.google_drive_dir_id:
                try:
                    print("Uploading a heatmap of instructor affiliations to Google Drive " + map_file)
                    drive = helper.google_drive_authentication()
                    helper.google_drive_upload(map_file,
                                               drive,
                                               [{'mimeType': 'text/plain', 'id': args.google_drive_dir_id}],
                                               False)
                    print('Map uploaded to Google Drive.')
                except Exception:
                    print ("An error occurred while uploading the map to Google Drive...\n")
                    print(traceback.format_exc())


        # Choropleth map over UK regions
        if "_GB_" in workshops_file_name_without_extension:  # Only makes sense for the UK
            try:
                print("#####################################################################")
                print('Map 4: generating a choropleth map of workshop venues over UK regions ...')
                print("#####################################################################\n")

                uk_regions = json.load(open(UK_REGIONS_FILE, encoding='utf-8-sig'))

                workshops_df = helper.insert_region_column(workshops_df, uk_regions)

                map = helper.generate_choropleth_map(workshops_df, uk_regions, "workshops")

                # Save map to a HTML file
                map_file = WORKSHOPS_DATA_DIR + 'choropleth_map_workshops_per_UK_regions_' + workshops_file_name_without_extension + '.html'
                map.save(map_file)
                print('A choropleth map of workshops over UK regions saved to HTML file ' + map_file + '\n')

            except:
                print ("An error occurred while creating a choropleth map of workshops over UK regions...\n")
                print(traceback.format_exc())
            else:
                if args.google_drive_dir_id:
                    try:
                        print(
                            "Uploading a choropleth map of workshops over UK regions to Google Drive " + map_file)
                        drive = helper.google_drive_authentication()
                        helper.google_drive_upload(map_file,
                                                   drive,
                                                   [{'mimeType': 'text/plain', 'id': args.google_drive_dir_id}],
                                                   False)
                        print('Map uploaded to Google Drive.')
                    except Exception:
                        print ("An error occurred while uploading the map to Google Drive...\n")
                        print(traceback.format_exc())




if __name__ == '__main__':
    main()
