import pytest
import os
import map_instructor_affiliations as mapia

class TestMapInstructAff(object):
        
    ## Assert if dictionary not empty and a certain value exists
    def test_instructors_affiliation_dict(self):
        assert bool(pytest.instructors_affiliatons_dict) == True
        ## MISSING KNOWN VALUE
    
    ## Assert if map not empty
    def test_map(self):
        assert type(pytest.maps_5) != None      
     

    def pytest_sessionfinish(self):
        print("*** test run reporting finishing")


if __name__ == "__main__":    
    pytest.main("-s")
