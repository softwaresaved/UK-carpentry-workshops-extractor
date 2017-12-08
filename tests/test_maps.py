import pytest
import os

class TestMaps(object):

    ## Assert if workshop institution column was added to the dataframe
    def test_add_region_column(self):
        assert {'workshop_institution'}.issubset(pytest.df_workshop_institution)
    
    ## Assert if map not none type
    def test_MapWorkInstit(self):
        assert type(pytest.maps_wi) != None
    
    ## Assert if map not none type
    def test_MapClustWorkVen(self):
        assert type(pytest.maps_cwv) != None


    ## Assert if region column was added to the dataframe
    def test_add_region_column(self):
        assert {'region'}.issubset(pytest.df_workshopUKregions)

    ## Assert if dataframe given is not empty and gives a certain value
    def test_df_workshops_per_region(self):
        assert not pytest.workshops_per_region_df.empty
        assert pytest.workshops_per_region_df.loc[pytest.workshops_per_region_df['region'] == 'Scotland',
                                                  'count'].iloc[0] == 20
       
    ## Assert if map not none type
    def test_MapWorkVenUKRegion(self):
        assert type(pytest.maps_wvUK) != None


    ## Assert if dataframe given is not empty and gives a certain known value
    def test_df_instructors_per_affiliation(self):
        assert not pytest.df_instructor_affiliation.empty
        assert pytest.df_instructor_affiliation['affiliation'].isnull().any().any()== False
                
    ## Assert if map not empty
    def test_MapClustInstructAff(self):
        assert type(pytest.maps_cia) != None

    
    ## Assert if dataframe not empty and a certain value exists
    def test_instructors_affiliation_dict(self):
        assert not pytest.instructors_affiliatons.empty
    
    ## Assert if map not empty
    def test_MapInstructAff(self):
        assert type(pytest.maps_ia) != None


    ## Assert if dataframe given is not empty and gives a certain known value
    def test_df_instructors_per_affiliation_region(self):
        assert not pytest.df_instructor_affiliation_region.empty
        assert pytest.df_instructor_affiliation_region['nearest_airport_code'].isnull().any().any()== False
        assert pytest.df_instructor_affiliation_region['affiliation'].isnull().any().any()== False        
    
    ## Assert if region column was added to the dataframe
    def test_add_region_column(self):
        assert {'region'}.issubset(pytest.df_instructorUKregion)

    ## Assert if dataframe given is not empty and gives a certain known value
    def test_df_instructors_per_region(self):
        assert not pytest.instructors_per_region_df.empty
        assert pytest.instructors_per_region_df.loc[pytest.instructors_per_region_df['region'] == 'London',
                                                  'count'].iloc[0] == 10

    ## Assert if map not none type
    def test_MapInstAffUKRegion(self):
        assert type(pytest.maps_iaUK) != None


    def pytest_sessionfinish(self):
        print("*** test run reporting finishing")


if __name__ == "__main__":    
    pytest.main("-s")
