import pytest
import os
import map_clustered_instructor_affiliations as mapcia

class TestMapClustInstructAff(object):

    ## Assert if dataframe given is not empty and gives a certain known value
    def test_df_instructors_per_affiliation(self):
        assert pytest.df_instructor_affiliation.empty == False
        assert pytest.df_instructor_affiliation['affiliation'].isnull().any().any()== False
                
    ## Assert if map not empty
    def test_map(self):
        assert type(pytest.maps_4) != None  

        

    def pytest_sessionfinish(self):
        print("*** test run reporting finishing")


if __name__ == "__main__":    
    pytest.main("-s")
