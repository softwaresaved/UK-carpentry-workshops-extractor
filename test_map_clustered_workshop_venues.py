import pytest
import os
import map_clustered_workshop_venues as mapcwv

class TestMapClustWorkVen(object):
    
    ## Assert if map not none type
    def test_map(self):
        assert type(pytest.maps_2) != None

    def pytest_sessionfinish(self):
        print("*** test run reporting finishing")


if __name__ == "__main__":    
    pytest.main("-s")
