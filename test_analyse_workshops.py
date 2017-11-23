import pytest
import os
import analyse_workshops as aw

class TestAnalyseWorkshops(object):
    
    ## Assert if dataframe created is not empty
    def test_dataframe(self):
        assert os.path.isfile(pytest.file_path_workshops) == True
        assert pytest.df_workshops.empty == False
        assert len(pytest.df_workshops['latitude'].index) == len(pytest.df_workshops.index)
        assert len(pytest.df_workshops['longitude'].index) == len(pytest.df_workshops.index)

    ## Assert if column was added and badges value is not null
    def test_start_year(self):
        assert {'start_year'}.issubset(pytest.df_badges_workshops) == True
        assert pytest.df_badges_workshops['start_year'].isnull().any().any()== False
        col = pytest.df_badges_workshops['start_year'].tolist()
        assert 2015 in col == True

    ## Assert if workshop column added
    def test_workshop_type(self):
        assert {'tags'}.issubset(pytest.df_global_workshops) == True

    ## Assert if cancelled, stalled and unresponsive rows removed
    def test_removed_stalled_workshops(self):
        list_values = ['stalled', 'cancelled', 'unresponsive']
        for value in list_values:
            assert pytest.df_global_workshops.tags[pytest.df_global_workshops.tags == value].count() == 0

    ## Assert if dataframe is not empty and the value for a certain year
    ## has a certain value.
    def test_df_workshops_per_year(self):
        df_workshops_per_year = aw.workshop_years_analysis(pytest.df_global_workshops,pytest.writer_workshops)
        assert df_workshops_per_year.empty == False
        assert df_workshops_per_year.loc[df_workshops_per_year['start_year'] ==
                                         2013, 'count'].iloc[0] == 11

    ## Assert if dataframe is not empty
    def test_df_workshops_per_institution(self):
        df_workshops_per_institution = aw.workshops_venue_analysis(pytest.df_global_workshops,pytest.writer_workshops)
        assert df_workshops_per_institution.empty == False
        assert df_workshops_per_institution.loc[df_workshops_per_institution['venue'] ==
                                                'University of Southampton',
                                                'count'].iloc[0] == 8
        assert df_workshops_per_institution.loc[df_workshops_per_institution['venue'] ==
                                                'Imperial College London',
                                                'count'].iloc[0] == 5
        
    ## Assert if dataframe is not empty
    def test_df_workshops_type(self):
        df_workshops_type = aw.workshops_type_analysis(pytest.df_global_workshops,pytest.writer_workshops)        
        assert df_workshops_type.empty == False
        assert df_workshops_type.loc[df_workshops_type['workshop_type'] ==
                                                'SWC', 'count'].iloc[0] == 110
    
    ## Assert if dataframe is not empty and value for a specific year
    def test_df_workshops_per_venue_year(self):
        df_workshops_per_venue_year = aw.number_workshops_per_venue_year(pytest.df_global_workshops,pytest.writer_workshops)
        assert df_workshops_per_venue_year.empty == False

    ## Assert if dataframe is not empty and value for a specific year
    def test_df_workshops_per_type_year(self):
        df_workshops_per_type_year = aw.number_workshops_per_type_year(pytest.df_global_workshops,pytest.writer_workshops)
        assert df_workshops_per_type_year.empty == False

    ## Assert if dataframe is not empty and value for a specific year
    def test_df_attendees_per_year(self):
        df_attendees_per_year = aw.attendees_per_year_analysis(pytest.df_global_workshops,pytest.writer_workshops)
        assert df_attendees_per_year.empty == False
        assert df_attendees_per_year.loc[df_attendees_per_year['start_year'] ==
                                         2013, 'number_of_attendees'].iloc[0] == 354

    ## Assert if dataframe is not empty
    def test_df_attendees_per_workshop_type(self):
        df_attendees_per_workshop_type = aw.attendees_per_workshop_type_analysis(pytest.df_global_workshops,pytest.writer_workshops)
        assert df_attendees_per_workshop_type.empty == False
        assert df_attendees_per_workshop_type.loc[df_attendees_per_workshop_type['workshop_type'] ==
                                                  'DC', 'number_of_attendees'].iloc[0] == 284

    ## Assert if dataframe is not empty and value for a specific year
    def test_df_attendees_per_workshop_type_over_years(self):
        df_attendees_per_workshop_type_over_years = aw.attendees_per_workshop_type_over_years_analysis(pytest.df_global_workshops,pytest.writer_workshops)
        assert df_attendees_per_workshop_type_over_years.empty == False

    def pytest_sessionfinish(self):
        print("*** test run reporting finishing")


if __name__ == "__main__":    
    pytest.main("-s")
