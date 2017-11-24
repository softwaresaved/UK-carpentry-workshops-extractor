import pytest
import os
import map_workshop_venues_per_UK_regions as mapwvUK

class TestMapWorkVenUKRegion(object):

    ## Assert if region column was added to the dataframe
    def test_add_region_column(self):
        assert {'region'}.issubset(pytest.df_workshopUKregions) == True

    ## Assert if dataframe given is not empty and gives a certain value
    def test_df_workshops_per_region(self):
        assert pytest.workshops_per_region_df.empty == False
        ## MISSING THE CERTAIN VALUE

    ## Assert if map not none type
    def test_map(self):
        assert type(pytest.maps_1) != None

    def pytest_sessionfinish(self):
        print("*** test run reporting finishing")


if __name__ == "__main__":
    pytest.main("-s")
