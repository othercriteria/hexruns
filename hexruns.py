#!/usr/bin/env python

import argparse
import os
import gpxpy
import matplotlib.pyplot as plt
import numpy as np

# Command line option handling
parser = argparse.ArgumentParser(description = 'Visualize GPX running data.')
parser.add_argument('locality', type = str, nargs = '?',
                    help = 'Limit visualization to selected locality')
args = parser.parse_args()

if args.locality:
    locality = args.locality
    
    print('Limiting to "{0}"'.format(locality))

    api_key = open('google_public_api_key', 'r').readlines()[0][:-1]
    print('Google public API key:', api_key)
    
    import googlemaps
    gmaps = googlemaps.Client(key = api_key)

    geocode_result = gmaps.geocode(locality)[0]['geometry']

    bounds_l = geocode_result['bounds']['southwest']
    bounds_u = geocode_result['bounds']['northeast']

    lat_l, lat_u = bounds_l['lat'], bounds_u['lat']
    lon_l, lon_u = bounds_l['lng'], bounds_u['lng']
    
    print('Latitude:  {0} -- {1}'.format(lat_l, lat_u))
    print('Longitude: {0} -- {1}'.format(lon_l, lon_u))
    
# Accumulate lists of latitude, longitude, and duration
lat, lon, dur = [], [], []

all_files = os.listdir('.')
for file in all_files:
    if not file[-4:] == '.gpx':
        continue

    with open(file, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)

        track = gpx.tracks[0]

        for segment in track.segments:
            first = segment.points[0]
            rest = segment.points[1:]
            
            last = first
            for point in rest:
                new = point

                lat.append(new.latitude)
                lon.append(new.longitude)
                dur.append((new.time - last.time).total_seconds())

                last = new

lat = np.array(lat)
lon = np.array(lon)
dur = np.array(dur)
if args.locality:
    in_bounds = (lat_l < lat) * (lat < lat_u) * (lon_l < lon) * (lon < lon_u)

    lat = lat[in_bounds]
    lon = lon[in_bounds]
    dur = dur[in_bounds]
                
plt.figure()
plt.hexbin(lon, lat, dur, gridsize = 50)
plt.show()