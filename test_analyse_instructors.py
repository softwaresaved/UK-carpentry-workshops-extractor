import pytest
import os
import analyse_instructors as ai

class TestAnalyseInstructors(object):
    
    ## Assert if dataframe created is not empty
    def test_dataframe(self):
        assert os.path.isfile(pytest.file_path_instructors) == True
        assert pytest.df_instructors.empty == False
        assert pytest.df_instructors['nearest_airport_code'].isnull().any().any()== False
        assert pytest.df_instructors['affiliation'].isnull().any().any()== False        

    ## Assert if badges collumn added and doesnt have nulls
    def test_badges_instructors(self):
        assert {'earliest-badge-awarded-year'}.issubset(pytest.df_badges_instructors) == True
        col = pytest.df_badges_instructors['earliest-badge-awarded-year']
        assert col.isnull().any().any()== False
        assert 2014 in col.tolist() == True
            
    ## Assert if new column added
    def test_airport_region(self):
        assert {'nearest_airport_UK_region'}.issubset(pytest.df_badges_instructors) == True

    ## Assert if dataframe is not empty and the value for a certain airport
    ## has a certain value.
    def test_df_instructors_nearest_airport(self):
        df_instructors_nearest_airport = ai.instructors_nearest_airport_analysis(pytest.df_global_instructors,pytest.writer_instructors)
        assert df_instructors_nearest_airport.empty == False
        assert df_instructors_nearest_airport.loc[df_instructors_nearest_airport['nearest_airport_name'] ==
                                         'Leeds', 'count'].iloc[0] == 5

    ## Assert if dataframe is not empty and the value for a certain region
    ## has a certain value.
    def test_df_instructors_per_UK_region(self):
        df_instructors_per_UK_region = ai.instructors_per_UK_region_analysis(pytest.df_global_instructors,pytest.writer_instructors)
        assert df_instructors_per_UK_region.empty == False
        assert df_instructors_per_UK_region.loc[df_instructors_per_UK_region['nearest_airport_UK_region'] ==
                                         'Scotland', 'count'].iloc[0] == 5

    ## Assert if dataframe is not empty and the value for a certain year
    ## has a certain value.
    def test_df_instructors_per_year(self):
        df_instructors_per_year = ai.instructors_per_year_analysis(pytest.df_global_instructors,pytest.writer_instructors)
        assert df_instructors_per_year.empty == False
        assert df_instructors_per_year.loc[df_instructors_per_year['earliest-badge-awarded-year'] ==
                                         2014, 'count'].iloc[0] == 9
    

    def pytest_sessionfinish(self):
        print("*** test run reporting finishing")


if __name__ == "__main__":    
    pytest.main("-s")
