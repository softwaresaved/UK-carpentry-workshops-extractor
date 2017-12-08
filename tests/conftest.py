import os
import re
import sys
import json
import pandas as pd
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0,parentdir)
import analyse_workshops as aw
import analyse_instructors as ai
import map_workshop_venues_per_UK_regions as mapwvUK
import map_clustered_workshop_venues as mapcwv
import map_workshop_institution as mapwi
import map_instructor_affiliations_per_UK_regions as mapiaUK
import map_clustered_instructor_affiliations as mapcia
import map_instructor_affiliations as mapia

sys.path.append('/lib')
import lib.helper as helper

REGIONS_FILE = parentdir + '/lib/regions.json'
UK_INSTITUTIONS_GEODATA_FILE = parentdir + '/lib/UK-academic-institutions-geodata.xlsx'
WORKSHOPS_INSTITUTIONS_FILE = parentdir + '/lib/workshop_institutions.yaml'

WORKSHOP_DATA_DIR = parentdir + '/data/workshops/'
STALLED_WORKSHOP_TYPES = ['stalled', 'cancelled', 'unresponsive']

INSTRUCTOR_DATA_DIR = parentdir + '/data/instructors/'

def pytest_namespace():
        ## Analysis workshops
        file_path_workshops = WORKSHOP_DATA_DIR + 'test_file_workshops.csv'
        file_name_workshops = os.path.basename(file_path_workshops)
        file_name_workshops_without_extension = re.sub('\.csv$', '', file_name_workshops.strip())
        df_workshops = helper.load_data_from_csv(file_path_workshops)
        df_badges_workshops = aw.insert_start_year(df_workshops)
        df_global_workshops = aw.insert_workshop_type(df_badges_workshops)
        df_global_workshops = aw.insert_workshop_institution(df_global_workshops,WORKSHOPS_INSTITUTIONS_FILE)
        df_global_workshops = helper.remove_stalled_workshops(df_global_workshops,STALLED_WORKSHOP_TYPES)
        writer_workshops = helper.create_excel_analyses_spreadsheet(file_name_workshops_without_extension, df_badges_workshops, "carpentry_workshops")

        ## Analysis instructors
        file_path_instructors = INSTRUCTOR_DATA_DIR + 'test_file_instructors.csv'
        file_name_instructors = os.path.basename(file_path_instructors)
        file_name_instructors_without_extension = re.sub('\.csv$', '', file_name_instructors.strip())
        df_instructors = helper.load_data_from_csv(file_path_instructors)
        df_instructors = helper.drop_null_values_from_columns(df_instructors, ['country_code', 'affiliation'])
        df_badges_instructors = ai.insert_earliest_badge_year(df_instructors)
        df_global_instructors = ai.insert_airport_region(df_badges_instructors)
        writer_instructors = helper.create_excel_analyses_spreadsheet(file_name_instructors_without_extension, df_badges_instructors, "carpentry_instructors")

        regions = json.load(open(REGIONS_FILE, encoding='utf-8-sig'))
        
        ## Map workshop venues per UK regions
        df_workshop_venue = helper.load_data_from_csv(file_path_workshops, ['venue', 'latitude', 'longitude'])
        df_workshopUKregions = mapwvUK.create_regions_column(df_workshop_venue, regions)
        workshops_per_region_df = mapwvUK.workshops_per_region(df_workshop_venue)
        threshold_scale_wvUK = mapwvUK.define_threshold_scale(workshops_per_region_df)
        maps_wvUK = mapwvUK.generate_map(workshops_per_region_df, regions, threshold_scale_wvUK)

        ## Map clustered workshop venue
        maps_cwv = mapcwv.generate_map(df_workshop_venue)

        uk_academic_institutions_excel_file = pd.ExcelFile(UK_INSTITUTIONS_GEODATA_FILE)
        uk_academic_institutions_df = uk_academic_institutions_excel_file.parse('UK-academic-institutions')
        uk_academic_institutions_coords_df = uk_academic_institutions_df[['VIEW_NAME', 'LONGITUDE', 'LATITUDE']]
        all_uk_institutions_coords_df = uk_academic_institutions_coords_df.append(helper.get_UK_non_academic_institutions_coords())
        center = helper.get_center(all_uk_institutions_coords_df)

        ## Map workshop per institution
        df_workshop_institution = aw.insert_workshop_institution(df_workshop_venue,WORKSHOPS_INSTITUTIONS_FILE)
        df_workshop_institution = mapwi.workshops_per_institution(df_workshop_institution)
        maps_wi = mapwi.generate_map(df_workshop_institution,all_uk_institutions_coords_df,center)
        
        ## Map instructor affiliations per UK region
        df_instructor_affiliation_region = helper.load_data_from_csv(file_path_instructors, ['affiliation', 'nearest_airport_code'])
        df_instructor_affiliation_region = helper.drop_null_values_from_columns(df_instructor_affiliation_region, ['affiliation', 'nearest_airport_code'])
        df_instructor_affiliation_region = helper.fix_UK_academic_institutions_names(df_instructor_affiliation_region)
        df_instructorUKregion = mapiaUK.add_region_column(df_instructor_affiliation_region, all_uk_institutions_coords_df, regions)
        instructors_per_region_df = mapiaUK.instructors_per_region(df_instructorUKregion)
        threshold_scale_iaUK = mapiaUK.define_threshold_scale(instructors_per_region_df)
        maps_iaUK = mapiaUK.generate_map(instructors_per_region_df, regions, threshold_scale_iaUK)   

        ## Map clustered instructor affiliations
        df_instructor_affiliation = helper.load_data_from_csv(file_path_instructors, ['affiliation'])
        df_instructor_affiliation = helper.drop_null_values_from_columns(df_instructor_affiliation, ['affiliation'])
        df_instructor_affiliation = helper.fix_UK_academic_institutions_names(df_instructor_affiliation)
        maps_cia = mapcia.generate_map(df_instructor_affiliation, all_uk_institutions_coords_df, center)
        
        ## Map instructor affiliations
        instructors_affiliatons = mapia.instructors_per_affiliation(df_instructor_affiliation)
        maps_ia = mapia.generate_map(instructors_affiliatons, all_uk_institutions_coords_df, center)
        
        return {'file_path_workshops': file_path_workshops,
                'df_workshops': df_workshops,
                'df_badges_workshops': df_badges_workshops,
                'df_global_workshops': df_global_workshops,
                'writer_workshops': writer_workshops,
                'file_path_instructors': file_path_instructors,
                'df_instructors': df_instructors,
                'df_badges_instructors': df_badges_instructors,
                'df_global_instructors': df_global_instructors,
                'writer_instructors': writer_instructors,
                'df_workshopUKregions': df_workshopUKregions,
                'workshops_per_region_df': workshops_per_region_df,
                'maps_wvUK': maps_wvUK,
                'maps_cwv': maps_cwv,
                'df_workshop_institution': df_workshop_institution,
                'maps_wi': maps_wi,
                'df_instructor_affiliation_region': df_instructor_affiliation_region,
                'df_instructorUKregion': df_instructorUKregion,
                'instructors_per_region_df': instructors_per_region_df,
                'maps_iaUK': maps_iaUK,
                'df_instructor_affiliation': df_instructor_affiliation,
                'maps_cia': maps_cia,
                'instructors_affiliatons': instructors_affiliatons,
                'maps_ia': maps_ia}
