import os
import re
import analyse_workshops as aw
import analyse_instructors as ai
import sys

sys.path.append('/lib')
import lib.helper as helper

STALLED_WORKSHOP_TYPES = ['stalled', 'cancelled', 'unresponsive']

def pytest_namespace():
        current_dir = os.path.dirname(os.path.realpath(__file__))
        
        workshop_data_dir = current_dir + '/data/workshops/'
        file_path_workshops = workshop_data_dir + 'test_file_workshops.csv'
        file_name_workshops = os.path.basename(file_path_workshops)
        file_name_workshops_without_extension = re.sub('\.csv$', '', file_name_workshops.strip())
        df_workshops = helper.load_data_from_csv(file_path_workshops)
        df_badges_workshops = aw.insert_start_year(df_workshops)
        df_global_workshops = aw.insert_workshop_type(df_badges_workshops)
        df_global_workshops = helper.remove_stalled_workshops(df_global_workshops,STALLED_WORKSHOP_TYPES)
        writer_workshops = helper.create_excel_analyses_spreadsheet(file_name_workshops_without_extension, df_badges_workshops, "carpentry_workshops")

        instructor_data_dir = current_dir + '/data/instructors/'
        file_path_instructors = instructor_data_dir + 'test_file_instructors.csv'
        file_name_instructors = os.path.basename(file_path_instructors)
        file_name_instructors_without_extension = re.sub('\.csv$', '', file_name_instructors.strip())
        df_instructors = helper.load_data_from_csv(file_path_instructors)
        df_instructors = helper.drop_null_values_from_columns(df_instructors, ['country_code', 'affiliation'])
        df_badges_instructors = ai.insert_earliest_badge_year(df_instructors)
        df_global_instructors = ai.insert_airport_region(df_badges_instructors)
        writer_instructors = helper.create_excel_analyses_spreadsheet(file_name_instructors_without_extension, df_badges_instructors, "carpentry_instructors")


        
        return {'file_path_workshops': file_path_workshops,
                'df_workshops': df_workshops,
                'df_badges_workshops': df_badges_workshops,
                'df_global_workshops': df_global_workshops,
                'writer_workshops': writer_workshops,
                'file_path_instructors': file_path_instructors,
                'df_instructors': df_instructors,
                'df_badges_instructors': df_badges_instructors,
                'df_global_instructors': df_global_instructors,
                'writer_instructors': writer_instructors}
