#powiat_route_builder
"""
Turn a GPX *track* that covers all target roads
into a Mapy.cz-ready GPX *route* with points in strict order.

USAGE:
    python powiat_route_builder.py coverage.gpx route_out.gpx \
           --interval 1000   # resample every 1 000 m
"""

import math
import tkinter as tk
from tkinter import filedialog

import gpxpy
import gpxpy.gpx
from geopy.distance import geodesic

def resample(track_points, interval_m):
    """Yield points roughly every <interval_m> along the track."""
    bucket = 0.0
    if not track_points:
        return
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
    print("--- GPX Structure --- ")
    print(f"Number of tracks found: {len(in_gpx.tracks)}")
    if not in_gpx.tracks:
        print("Error: No tracks found in GPX file.")
        raise ValueError("No tracks found in GPX file.")
    
    first_track = in_gpx.tracks[0]
    print(f"Number of segments in first track: {len(first_track.segments)}")
    if not first_track.segments:
        print("Error: The first track contains no segments.")
        raise ValueError("The first track contains no segments.")
        
    first_segment = first_track.segments[0]
    points = first_segment.points
    print(f"Number of points in first segment of first track: {len(points)}")
    
    if not points:
        print("Error: No points found in the first segment of the first track.")
        raise ValueError("No points found in the first segment of the first track.")
    print("-----------------------")

    route = gpxpy.gpx.GPX()
    gpx_rte = gpxpy.gpx.GPXRoute(name="Powiat-loop 200 km")
    route.routes.append(gpx_rte)

    resampled_points = list(resample(points, interval))
    print(f"Number of points after resampling (interval: {interval}m): {len(resampled_points)}")
    
    if not resampled_points:
        raise ValueError("Resampling resulted in no points. Check track data and interval.")

    for p in resampled_points:
        gpx_rte.points.append(gpxpy.gpx.GPXRoutePoint(p.latitude, p.longitude))

    if close_loop and len(gpx_rte.points) > 0:
        first = gpx_rte.points[0]
        # Add the first point to the end only if it's not already the same as the last point
        if len(gpx_rte.points) == 1 or \
           (gpx_rte.points[-1].latitude != first.latitude or \
            gpx_rte.points[-1].longitude != first.longitude):
            gpx_rte.points.append(
                gpxpy.gpx.GPXRoutePoint(first.latitude, first.longitude)
            )
    return route

def main():
    # Set up the root Tkinter window and hide it
    root = tk.Tk()
    root.withdraw()

    # Prompt user for the input GPX track file
    input_gpx_path = filedialog.askopenfilename(
        title="Select Input GPX Track File",
        filetypes=[("GPX files", "*.gpx"), ("All files", "*.*")]
    )
    if not input_gpx_path:
        print("No input file selected. Exiting.")
        return

    # Prompt user for the output GPX route file
    output_gpx_path = filedialog.asksaveasfilename(
        title="Save Output GPX Route File As...",
        filetypes=[("GPX files", "*.gpx")],
        defaultextension=".gpx",
        initialfile="route_output.gpx"
    )
    if not output_gpx_path:
        print("No output file selected. Exiting.")
        return

    # Using default values for interval and close_loop for simplicity.
    interval = 1000
    close_loop = True
    print("-" * 30)
    print(f"Processing {input_gpx_path}...")
    print(f"Using interval: {interval}m")
    print(f"Close loop: {close_loop}")
    print("-" * 30)

    try:
        with open(input_gpx_path, 'r', encoding='utf-8') as fh:
            in_gpx = gpxpy.parse(fh)
    except FileNotFoundError:
        print(f"Error: Input file '{input_gpx_path}' not found.")
        return
    except Exception as e:
        print(f"Error parsing input GPX file: {e}")
        return

    try:
        out_gpx = build_route(in_gpx, interval, close_loop)
        with open(output_gpx_path, 'w', encoding='utf-8') as fh:
            fh.write(out_gpx.to_xml())
        print(f"\nSuccessfully created GPX route: {output_gpx_path}")
        print(f"Total points in route: {len(out_gpx.routes[0].points)}")
    except ValueError as ve:
        print(f"Error building route: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
