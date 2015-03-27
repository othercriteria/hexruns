# hexruns

*Quick and dirty visualization of aggregated runs*

Rough concept is to extract locations from GPS (or whatever it actually is that [RunKeeper](http://runkeeper.com) uses to track your location) traces, filter to those in a compact area (e.g., Worcester, MA), display them in a [2-d histogram with hexagonal binning](http://matplotlib.org/examples/pylab_examples/hexbin_demo.html), and superimpose over a map for context.
