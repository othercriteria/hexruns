#!/usr/bin/env python

import argparse
import os
import gpxpy
import matplotlib.pyplot as plt

# Command line option handling
parser = argparse.ArgumentParser(description = 'Visualize GPX running data.')
parser.add_argument('city', type = str, nargs = '?',
                    help = 'Limit visualization to selected city')
args = parser.parse_args()

if args.city:
    print(args.city)

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

plt.figure()
plt.hexbin(lat, lon, dur, gridsize = 50)
plt.show()
