import pytest
import requests
import amy_data_extract


def setup(self):
    url_parameters = {
        "country": "GB",
        "is_instructor" : "true"
    }
    username = ""
    password = ""

def test_get_workshops():

    response = requests.get(amy_data_extract.AMY_PUBLISHED_WORKSHOPS_API_URL, headers=amy_data_extract.HEADERS, auth=(username, password),
                            params=url_parameters)
    assert(response.status_code, 200)
    num_results = response.json()["count"]

    workshops_df = amy_data_extract.get_workshops(url_parameters, username, password)
    assert(num_results, workshops_df.dize)

    if workshops_df.size > 0:
        assert workshops_df.at[0, "country_code"] == url_parameters.country

def test_get_instructors():

    response = requests.get(amy_data_extract.AMY_PERSONS_API_URL, headers=amy_data_extract.HEADERS, auth=(username, password),
                            params=url_parameters)
    assert(response.status_code, 200)

    num_results = response.json()["count"]

    instructors_df = amy_data_extract.get_instructors(url_parameters, username, password)

    assert(num_results, instructors_df.dize)

    if instructors_df.size > 0:
        instructors_df.at[0, "country_code"] == url_parameters.country

def test_get_airports():
    print


def test_extract_airport_code():
    assert amy_data_extract.extract_airport_code("https://amy.software-carpentry.org/api/v1/airports/MAN/") == "MAN"
    assert amy_data_extract.extract_airport_code("") == None
    assert amy_data_extract.extract_airport_code(None) == None


def test_read_credentials():
    print
