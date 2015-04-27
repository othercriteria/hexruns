#!/usr/bin/env python

import argparse
import gpxpy
import numpy as np
import io
from pathlib import Path
from PIL import Image
import urllib.request
import urllib.parse

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Command line option handling
parser = argparse.ArgumentParser(description = 'Visualize GPX running data.')
parser.add_argument('locality', type = str, nargs = '?',
                    help = 'Limit visualization to selected locality')
parser.add_argument('-delta', metavar = 'd', type = float, default = 12,
                    help = 'Minimum time-delta for durations')
parser.add_argument('-suspicious', metavar = 's', type = float, default = 15,
                    help = 'Suspicious speed (default: 15.0 miles per hour)')
parser.add_argument('-output', type = str, default = 'hexruns_out',
                    help = 'Output filename stem (default: hexruns_out)')
parser.add_argument('-grid', metavar = 'g', type = int, default = 20,
                    help = 'Grid size, in number of hexagons')
parser.add_argument('-entropy', action = 'store_true',
                    help = 'Choose maximum entropy grid size, range 5 to g')
parser.add_argument('-bins', metavar = 'b', type = int, default = 5,
                    help = 'Duration bins to use for entropy (default: 5)')
parser.add_argument('-alpha', metavar = 'a', type = float, default = 0.5,
                    help = 'Opacity of histogram (default: 0.5)')
parser.add_argument('-maptype', metavar = 't', type = str, default = 'roadmap',
                    help = 'Default (roadmap), satellite, hybrid, or terrain')
parser.add_argument('-movie', action = 'store_true',
                    help = 'Generate a movie for the range of grid size')
args = parser.parse_args()

# Base path to be used in various filesystem operations
p = Path('.')

cache = p / 'cache'
if not cache.exists():
    cache.mkdir()

if args.locality:
    locality = args.locality

    print('Limiting to "{0}"'.format(locality))

    # Do lookup in geocode cache; create empty one if it doesn't exist
    import json
    maybe_geocode_cache_json = cache / 'geocode_cache.json'
    if maybe_geocode_cache_json.exists():
        with maybe_geocode_cache_json.open() as geocode_cache_json:
            geocode_cache = json.load(geocode_cache_json)
    else:
        geocode_cache = {}

    if locality in geocode_cache:
        print('Using cached geocode')
        geocode_response = geocode_cache[locality]
    else:
        api_key_file = p / 'google_public_api_key'
        api_key = api_key_file.open().read()
        print('Google public API key:', api_key)
    
        import googlemaps
        gmaps = googlemaps.Client(key = api_key)

        geocode_response = gmaps.geocode(locality)[0]['geometry']

        geocode_cache[locality] = geocode_response
        with maybe_geocode_cache_json.open('w') as outfile:
            json.dump(geocode_cache, outfile)

    bounds_l = geocode_response['bounds']['southwest']
    bounds_u = geocode_response['bounds']['northeast']

    lat_l, lat_u = bounds_l['lat'], bounds_u['lat']
    lon_l, lon_u = bounds_l['lng'], bounds_u['lng']
    
    print('Latitude:  {0} -- {1}'.format(lat_l, lat_u))
    print('Longitude: {0} -- {1}'.format(lon_l, lon_u))
    
# Accumulate lists of latitude, longitude, duration, and speed
lat, lon, dur, spd = [], [], [], []

# Accumulate paths
lat_paths = []
lon_paths = []

for file in p.glob('*.gpx'):
    with file.open() as gpx_file:
        gpx = gpxpy.parse(gpx_file)

        track = gpx.tracks[0]

        for segment in track.segments:
            first = segment.points[0]
            rest = segment.points[1:]
            
            new_lat_path = [first.latitude]
            new_lon_path = [first.longitude]

            last = first
            for point in rest:
                new = point

                new_lat_path.append(new.latitude)
                new_lon_path.append(new.longitude)

                # Only accumlate points for duration and speed when
                # the minimum time-delta has elapsed, to make these
                # more robust to sensor error and strange movements
                t = (new.time - last.time).total_seconds()
                if t < args.delta:
                    continue

                # TODO: use standard cartographical terminology
                c = 24901 * np.cos(new.latitude * np.pi / 180) / 360
                k = 1 / np.cos(new.latitude * np.pi / 180)
                d = np.sqrt((k*c*(new.latitude  - last.latitude )) ** 2 +
                            (  c*(new.longitude - last.longitude)) ** 2)
                s = 3600 * d / t

                if s > args.suspicious:
                    print('Suspicious speed:', s, last, new)
                    continue

                lat.append(new.latitude)
                lon.append(new.longitude)
                dur.append(t)
                spd.append(s)

                last = new

            lat_paths.append(np.array(new_lat_path))
            lon_paths.append(np.array(new_lon_path))

lat = np.array(lat)
lon = np.array(lon)
dur = np.array(dur)
spd = np.array(spd)
if args.locality:
    in_bounds = (lat_l < lat) * (lat < lat_u) * (lon_l < lon) * (lon < lon_u)

    lat = lat[in_bounds]
    lon = lon[in_bounds]
    dur = dur[in_bounds]
    spd = spd[in_bounds]

# Locate center of GPS points, and calculate local scale factor
center_lat = np.mean(lat)
center_lon = np.mean(lon)
scale_factor = 1 / np.cos(center_lat * np.pi / 180)
    
# Construct Google Maps static image request
url = 'http://maps.googleapis.com/maps/api/staticmap'
dim = 512
max_range = max(scale_factor * (lat.max() - lat.min()), lon.max() - lon.min())
zoom = int(np.log(360 / max_range) / np.log(2) + 1)
request = '{0}?maptype={1}&center={2},{3}&size={4}x{4}&zoom={5}'.\
    format(url, args.maptype, center_lat, center_lon, dim, zoom)

# Use cached image if the request has been made previously
maybe_image = cache / urllib.parse.quote(request, safe = '')
if maybe_image.exists():
    print('Using cached image: {0}'.format(maybe_image))
    contents = maybe_image.open('rb').read()
else:
    # Make the request, grab the response, and cache it
    opened_url = urllib.request.urlopen(request)
    contents = opened_url.read()
    maybe_image.open('wb').write(contents)

# Turn raw data into image
buffer = io.BytesIO(contents)
image = Image.open(buffer)

# Transformation to put lat-lon points onto the same coordinates as the map
lon_scaling = (dim / 360) * (2 ** (zoom - 1))
lat_scaling = lon_scaling * scale_factor
def lat_to_map(lats):
    return -lat_scaling * (lats - center_lat) + (dim / 2)
def lon_to_map(lons):
    return lon_scaling * (lons - center_lon) + (dim / 2)

# Apply transformation
lat = lat_to_map(lat)
lon = lon_to_map(lon)
lat_paths = [lat_to_map(lat_path) for lat_path in lat_paths]
lon_paths = [lon_to_map(lon_path) for lon_path in lon_paths]

# Choose grid size as that which maximizes the entropy of the
# (non-zero) region durations (with the durations coarsened to 6
# possible levels), up to the desired grid size specified by the user
if args.entropy:
    possible_g = []
    entropy = []
    for g in range(5, args.grid + 1):
        h = plt.hexbin(lon, lat, dur, reduce_C_function = np.sum,
                       extent = (0, dim, 0, dim), gridsize = g)

        counts = h.get_array()
        p = np.histogram(counts, bins = args.bins)[0] / len(counts)
        p_nonzero = p[np.nonzero(p)]

        possible_g.append(g)
        entropy.append(-np.sum(p_nonzero * np.log2(p_nonzero)))
    chosen_i = np.argmax(entropy)
    print('Picked g = {0} with entropy {1}'.format(possible_g[chosen_i],
                                                   entropy[chosen_i]))
    args.grid = possible_g[chosen_i]

    plt.figure()
    plt.plot(possible_g, entropy)
    plt.scatter(possible_g[chosen_i], entropy[chosen_i], c = 'red')
    plt.title('Entropy maximization ({0} duration bins)'.format(args.bins))
    plt.xlabel('grid size')
    plt.ylabel('entropy (bits)')
    plt.xlim([0, possible_g[-1]])
    plt.savefig(args.output + '_entropy.png')

# Return the hexbin object for later use, when generated
def do_plot(disp, **kwargs):
    plt.imshow(image)

    if disp == 'duration':
        gridsize = kwargs['gridsize']
        h = plt.hexbin(lon, lat, dur,
                       reduce_C_function = np.sum,
                       extent = (0, dim, 0, dim),
                       gridsize = gridsize,
                       linewidths = (0,),
                       alpha = args.alpha, cmap=plt.cm.Blues)
        plt.title('Total time in region')
    elif disp == 'pace':
        gridsize = kwargs['gridsize']
        h = plt.hexbin(lon, lat, 60 / spd,
                       reduce_C_function = np.min,
                       extent = (0, dim, 0, dim),
                       gridsize = gridsize,
                       linewidths = (0,),
                       alpha = args.alpha, cmap=plt.cm.Reds_r)
        plt.title('Fastest pace in region')
    elif disp == 'paths':
        for lat_path, lon_path in zip(lat_paths, lon_paths):
            plt.plot(lon_path, lat_path)
        plt.xlim([0, dim])
        plt.ylim([dim, 0])
        plt.title('Paths')

    if (dim / lon_scaling) / 5 < 0.01:
        tick_fmt = '%.3f'
    else:
        tick_fmt = '%.2f'

    plt.xticks(np.linspace(0, dim, 5),
               [(tick_fmt % lon)
                for lon in np.linspace((-dim / 2) / lon_scaling + center_lon,
                                       ( dim / 2) / lon_scaling + center_lon,
                                       5)])
    plt.yticks(np.linspace(0, dim, 5),
               [(tick_fmt % lat)
                for lat in np.linspace(( dim / 2) / lat_scaling + center_lat,
                                       (-dim / 2) / lat_scaling + center_lat,
                                       5)])

    if disp == 'paths':
        return None
    else:
        return h

plt.figure()
do_plot('paths')
plt.savefig(args.output + '_paths.png')

plt.figure()
do_plot('duration', gridsize = args.grid)
cb = plt.colorbar()
cb.set_label('seconds')
plt.savefig(args.output + '_duration.png')

plt.figure()
do_plot('pace', gridsize = args.grid)
cb = plt.colorbar()
cb.set_label('min/mile')
plt.savefig(args.output + '_pace.png')

if args.movie:
    import matplotlib.animation as manimation

    FFMpegWriter = manimation.writers['ffmpeg']
    if args.locality:
        title = 'hexruns output: "{0}"'.format(args.locality)
    else:
        title = 'hexruns output'
    metadata = { 'title':   title,
                 'artist':  'https://github.com/othercriteria/hexruns',
                 'comment': 'grid size: 2 - {0}'.format(args.grid) }
    writer = FFMpegWriter(fps = 3, metadata = metadata, bitrate = 1000)

    fig = plt.figure()
    with writer.saving(fig, args.output + '.mp4', 100):
        for i in range(args.grid, 1, -1):
            fig.clf()
            h = do_plot('duration', gridsize = i + 1)

            cb = plt.colorbar(h)
            cb.set_label('seconds')
            min_time = h.get_array().min()
            max_time = h.get_array().max()
            tick_vals = np.linspace(min_time, max_time, 3)
            cb.set_ticks(tick_vals)
            cb.set_ticklabels([str(int(tick_val)) for tick_val in tick_vals])

            writer.grab_frame()
