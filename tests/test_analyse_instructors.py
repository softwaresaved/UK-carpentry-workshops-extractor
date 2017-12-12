import pytest
import os
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0,parentdir)
import analyse_instructors as ai

class TestAnalyseInstructors(object):
    
    ## Assert if path is a file, dataframe created is not empty and the 
    ## affiliation and nearest_airport_code columns do not have null values.
    def test_dataframe(self):
        assert os.path.isfile(pytest.file_path_instructors)
        assert not pytest.df_instructors.empty
        assert not pytest.df_instructors['nearest_airport_code'].isnull().any().any()
        assert not pytest.df_instructors['affiliation'].isnull().any().any()        

    ## Assert if badges column was added, does not have null and contains a
    ## certain value.
    def test_badges_instructors(self):
        assert {'earliest-badge-awarded-year'}.issubset(pytest.df_badges_instructors)
        col = pytest.df_badges_instructors['earliest-badge-awarded-year']
        assert not col.isnull().any().any()
        assert 2014 in col.tolist()
            
    ## Assert if new column with the region information is added
    def test_airport_region(self):
        assert {'nearest_airport_UK_region'}.issubset(pytest.df_badges_instructors)

    ## Assert if dataframe is not empty and has a cetain value.
    def test_df_instructors_nearest_airport(self):
        df_instructors_nearest_airport = ai.instructors_nearest_airport_analysis(pytest.df_global_instructors,pytest.writer_instructors)
        assert not df_instructors_nearest_airport.empty
        assert df_instructors_nearest_airport.loc[df_instructors_nearest_airport['nearest_airport_name'] ==
                                         'Leeds', 'count'].iloc[0] == 5

    ## Assert if dataframe is not empty and has a cetain value.
    def test_df_instructors_per_UK_region(self):
        df_instructors_per_UK_region = ai.instructors_per_UK_region_analysis(pytest.df_global_instructors,pytest.writer_instructors)
        assert not df_instructors_per_UK_region.empty
        assert df_instructors_per_UK_region.loc[df_instructors_per_UK_region['nearest_airport_UK_region'] ==
                                         'Scotland', 'count'].iloc[0] == 5

    ## Assert if dataframe is not empty and has a cetain value.
    def test_df_instructors_per_year(self):
        df_instructors_per_year = ai.instructors_per_year_analysis(pytest.df_global_instructors,pytest.writer_instructors)
        assert not df_instructors_per_year.empty
        assert df_instructors_per_year.loc[df_instructors_per_year['earliest-badge-awarded-year'] ==
                                         2014, 'count'].iloc[0] == 9
    

    def pytest_sessionfinish(self):
        print("*** test run reporting finishing")


if __name__ == "__main__":    
    pytest.main("-s")
