# hexruns

*Visualizing running data through aggregation with hexagonal binning*

To see hexruns in action, check out [this blog post](http://mesokurtosis.com/posts/2015-03-29-running-viz-fixed.html) and the other posts in the ["running"](http://mesokurtosis.com/tags/running.html) tag.

Its rough purpose is to extract locations from GPS (or whatever it actually is that [RunKeeper](http://runkeeper.com) uses to track your location) tracks, filter to those in a compact area (e.g., Providence, RI), display them in a [2-d histogram with hexagonal binning](http://matplotlib.org/examples/pylab_examples/hexbin_demo.html), and superimpose over a map for context.

A current area of active work is finding colormaps that convey useful information about duration and pace when overlaid on the various [map types](https://developers.google.com/maps/documentation/staticmaps/index#MapTypes) that the Google Static Maps API makes available. I've found this [guide](http://matplotlib.org/users/colormaps.html) useful but I'm still a long way from a really satisfying solution.

## Usage

1. Make sure you have a working Python 3.x setup and all the requirements listed below. (Alternatively, just use the error messages to figure out what needs to be installed.)
2. Place the `hexruns.py` script in a directory with the runs to be analyzed. If acquired from RunKeeper's [data export](https://support.runkeeper.com/hc/en-us/articles/201109886-How-to-Export-your-RunKeeper-data), these should all have filenames and contents that the script won't choke on.
3. Make it executable: `chmod u+x hexruns.py`.
4. Acquire a Google public API key, as per these [instructions](https://github.com/googlemaps/google-maps-services-python).
5. Place the API key into a file: `echo "YOUR-KEY" > google_public_api_key`.
6. Run the script, e.g., `./hexruns.py "Providence, RI"`.

For more control over the output, take a look at `./hexruns.py --help`.

## Requirements

* Python 3.x
* Numpy/Scipy/Matplotlib
* [Pillow](https://python-pillow.github.io/), or equivalent, to provide [PIL](http://www.pythonware.com/products/pil/)
* [gpxpy](https://github.com/tkrajina/gpxpy)
* [Python client for Google Maps Services](https://github.com/googlemaps/google-maps-services-python)
* For movie output: [FFmpeg](https://www.ffmpeg.org/)
