import pytest
import os
import map_instructor_affiliations_per_UK_regions as mapiaUK

class TestMapInstAffUKRegion(object):

    ## Assert if dataframe given is not empty and gives a certain known value
    def test_df_instructors_per_affiliation_region(self):
        assert pytest.df_instructor_affiliation_region.empty == False
        assert pytest.df_instructor_affiliation_region['nearest_airport_code'].isnull().any().any()== False
        assert pytest.df_instructor_affiliation_region['affiliation'].isnull().any().any()== False        
    
    ## Assert if region column was added to the dataframe
    def test_add_region_column(self):
        assert {'region'}.issubset(pytest.df_instructorUKregion) == True

    ## Assert if dataframe given is not empty and gives a certain known value
    def test_df_instructors_per_region(self):
        assert pytest.instructors_per_region_df.empty == False
        ## MISSING KNOWN VALUE

    ## Assert if map not none type
    def test_map(self):
        assert type(pytest.maps_3) != None      

    def pytest_sessionfinish(self):
        print("*** test run reporting finishing")


if __name__ == "__main__":    
    pytest.main("-s")
