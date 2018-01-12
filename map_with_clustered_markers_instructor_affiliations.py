import os
import pandas as pd
import traceback
import glob
import re
import sys

sys.path.append('/lib')
import lib.helper as helper


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
INSTRUCTORS_DATA_DIR = CURRENT_DIR + '/data/instructors/'
UK_INSTITUTIONS_GEODATA_FILE = CURRENT_DIR + '/lib/UK-academic-institutions-geodata.xlsx'


def main():
    """
    Main function
    """
    args = helper.parse_command_line_paramters()
    print("Mapping instructor affiliations's geocoordinates into clusters on an interactive map ... \n")

    print("Note: this map only makes sense to generate with instructors in the UK as it cross references their affiliations with geocoordinates of UK institutions.\n")

    if args.instructors_file:
        instructors_file = args.instructors_file
        print("The CSV spreadsheet with Carpentry instructors to be mapped: " + args.instructors_file)
    else:
        print("Trying to locate the latest CSV spreadsheet with Carpentry instructors to map in " + INSTRUCTORS_DATA_DIR + "\n")
        instructors_files = glob.glob(INSTRUCTORS_DATA_DIR + "carpentry-instructors_GB_*.csv")
        instructors_files.sort(key=os.path.getctime)  # order by creation date

        if not instructors_files:
            print('No CSV file with Carpentry instructors found in ' + INSTRUCTORS_DATA_DIR + ". Exiting ...")
            sys.exit(1)
        else:
            instructors_file = instructors_files[-1] # get the last element

    instructors_file_name = os.path.basename(instructors_file)
    instructors_file_name_without_extension = re.sub('\.csv$', '', instructors_file_name.strip())
    print('Found CSV file with Carpentry instructors to analyse ' + instructors_file_name + "\n")

    try:
        uk_academic_institutions_geodata_file = pd.ExcelFile(UK_INSTITUTIONS_GEODATA_FILE)
        uk_academic_institutions_geodata_df = uk_academic_institutions_geodata_file.parse('UK-academic-institutions')
    except:
        print (
            "An error occurred while reading the UK academic institutions' geodata file " + UK_INSTITUTIONS_GEODATA_FILE)
    else:
        try:
            df = helper.load_data_from_csv(instructors_file, ['affiliation'])
            df = helper.drop_null_values_from_columns(df, ['affiliation'])
            # Rename 'affiliation' column as 'institution'
            df.rename(columns={'affiliation': 'institution'}, inplace=True)
            df = helper.fix_UK_academic_institutions_names(df)

            uk_academic_institutions_coords_df = uk_academic_institutions_geodata_df[['VIEW_NAME', 'LONGITUDE', 'LATITUDE']]
            all_uk_institutions_coords_df = uk_academic_institutions_coords_df.append(
                helper.get_UK_non_academic_institutions_coords())

            df = helper.insert_institutions_geocoordinates(df, all_uk_institutions_coords_df)

            # Lookup longitude and latitude values for instructors' affiliations
            for index, row in df.iterrows():
                if pd.isnull(row['longitude']) or pd.isnull(row['latitude']):
                    print('For affiliation "' + row[
                        'institution'] + '" we either have not got coordinates or it is not the official name of an UK '
                                         'academic institution. Skipping it ...\n')

            # Drop rows where we do not have longitude and latitude
            df.dropna(0, 'any', None, ['latitude', 'longitude'], inplace=True)

            print("Generating a map of instructors' affiliations as clusters of markers that can be zoomed in and out of ... \n")

            map = helper.generate_map_with_clustered_markers(df, "institution")
            map = helper.add_UK_regions_layer(map)

            ## Save map to an HTML file
            html_map_file = INSTRUCTORS_DATA_DIR + 'map_clustered_instructor_affiliations_' + instructors_file_name_without_extension + '.html'
            map.save(html_map_file)
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
