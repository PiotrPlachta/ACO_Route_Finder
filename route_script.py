#powiat_route_builder
"""
Turn a GPX *track* that covers all target roads
into a Mapy.cz-ready GPX *route* with points in strict order.

USAGE:
    python powiat_route_builder.py coverage.gpx route_out.gpx \
           --interval 1000   # resample every 1 000 m
"""

import argparse, math, gpxpy, gpxpy.gpx
from geopy.distance import geodesic

def resample(track_points, interval_m):
    """Yield points roughly every <interval_m> along the track."""
    bucket = 0.0
    last = track_points[0]
    yield last
    for pt in track_points[1:]:
        d = geodesic((last.latitude, last.longitude),
                     (pt.latitude,  pt.longitude)).meters
        bucket += d
        if bucket >= interval_m:
            yield pt
            bucket = 0.0
        last = pt

def build_route(in_gpx, interval, close_loop):
    points = []
    for trk in in_gpx.tracks:
        for seg in trk.segments:
            points.extend(seg.points)
    if not points:
        raise ValueError("No <trkpt> data found in GPX.")

    route = gpxpy.gpx.GPX()
    gpx_rte = gpxpy.gpx.GPXRoute(name="Powiat-loop 200 km")
    route.routes.append(gpx_rte)

    for p in resample(points, interval):
        gpx_rte.points.append(gpxpy.gpx.GPXRoutePoint(p.latitude, p.longitude))

    if close_loop:
        first = gpx_rte.points[0]
        gpx_rte.points.append(
            gpxpy.gpx.GPXRoutePoint(first.latitude, first.longitude)
        )
    return route

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_gpx")
    ap.add_argument("output_gpx")
    ap.add_argument("--interval", type=int, default=1000,
                    help="metres between successive route points (default 1000)")
    ap.add_argument("--close-loop", action="store_true",
                    help="repeat the first point at the end")
    args = ap.parse_args()

    with open(args.input_gpx, encoding="utf-8") as fh:
        in_gpx = gpxpy.parse(fh)

    out_gpx = build_route(in_gpx, args.interval, args.close_loop)
    with open(args.output_gpx, "w", encoding="utf-8") as fh:
        fh.write(out_gpx.to_xml())

if __name__ == "__main__":
    main()
