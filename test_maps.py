import pytest
import os
import map_clustered_workshop_venues as mapcwv
import map_workshop_venues_per_UK_regions as mapwvUK
import map_clustered_instructor_affiliations as mapcia
import map_instructor_affiliations as mapia
import map_instructor_affiliations_per_UK_regions as mapiaUK

class TestMaps(object):
    
    ## Assert if map not none type
    def test_MapClustWorkVen(self):
        assert type(pytest.maps_2) != None

    ## Assert if region column was added to the dataframe
    def test_add_region_column(self):
        assert {'region'}.issubset(pytest.df_workshopUKregions) == True

    ## Assert if dataframe given is not empty and gives a certain value
    def test_df_workshops_per_region(self):
        assert pytest.workshops_per_region_df.empty == False
        ## MISSING THE CERTAIN VALUE

    ## Assert if map not none type
    def test_MapWorkVenUKRegion(self):
        assert type(pytest.maps_1) != None

    ## Assert if dataframe given is not empty and gives a certain known value
    def test_df_instructors_per_affiliation(self):
        assert pytest.df_instructor_affiliation.empty == False
        assert pytest.df_instructor_affiliation['affiliation'].isnull().any().any()== False
                
    ## Assert if map not empty
    def test_MapClustInstructAff(self):
        assert type(pytest.maps_4) != None
    
    ## Assert if dictionary not empty and a certain value exists
    def test_instructors_affiliation_dict(self):
        assert bool(pytest.instructors_affiliatons_dict) == True
        ## MISSING KNOWN VALUE
    
    ## Assert if map not empty
    def test_MapInstructAff(self):
        assert type(pytest.maps_5) != None

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
    def test_MapInstAffUKRegion(self):
        assert type(pytest.maps_3) != None

    def pytest_sessionfinish(self):
        print("*** test run reporting finishing")


if __name__ == "__main__":    
    pytest.main("-s")
