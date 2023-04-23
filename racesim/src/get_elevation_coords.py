"""
ELEVATION PROFILE APP GENERATOR
ideagora geomatics-2018
http://geodose.com
"""

import urllib.request
import urllib.parse
from urllib.error import URLError, HTTPError
import json
import matplotlib.pyplot as plt
import os


def make_remote_request(url: str, json_data: dict):
    """
    Makes the remote request
    Continues making attempts until it succeeds
    """
    user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
    headers = {
        'User-Agent':   user_agent,
        'Content-Type': 'application/json'
               }
    # data = urllib.parse.urlencode(json_data)
    # data = data.encode('ascii')
    req = urllib.request.Request(url, json_data, headers)
    count = 2
    try:
        response = urllib.request.urlopen(req)
    except (URLError) as error:
        print('\n')
        print('*' * 20, 'Error Occured', '*' * 20)
        print(f'Number of tries: {count}')
        print(f'URL: {url}')
        print(error.reason)
        print('\n')
        count += 1
    except HTTPError as error:
        print('The server couldn\'t fulfill the request.')
        print('Error code: ', error.code)
    else:
        return response.read()


def make_json(data):
    # CONSTRUCT JSON
    d_ar = [{}]*len(data)
    for i in np.arange(len(data)):
        d_ar[i] = {"latitude": data[i][0], "longitude": data[i][1]}
    return json.dumps({"locations": d_ar}, skipkeys=int).encode('utf8')


def response_processing(reponse):
    json_str = json.loads(reponse)
    return json_str


# MAIN

url = "https://api.open-elevation.com/api/v1/lookup"
P1 = [[43.9933775, 11.3690729], [43.9932783, 11.3667434]]
reponse = make_remote_request(url, make_json(P1))
reponse = response_processing(reponse)

fileDir = os.path.dirname(os.path.realpath('__file__'))
print(fileDir)

# For accessing the file in a folder contained in the current folder
filename = os.path.join(fileDir, 'racesim\\src\\tracks\\Mugello_2020.geojson')
with open(filename, "r") as fh:
    gps_data = json.load(fh)

    # convert GPS data to xy coordinates
    gps_data_xy = []

    for cur_sec in gps_data["features"]:
        # get angle data out of dict
        tmp_gps = cur_sec["geometry"]["coordinates"]
        print(cur_sec["geometry"]["type"])

