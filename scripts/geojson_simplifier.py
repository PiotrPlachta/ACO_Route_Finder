#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import argparse
import os
import math
from collections import defaultdict
import numpy as np
from shapely.geometry import LineString, mapping

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate haversine distance between two points in meters"""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_line_hash(coords, precision=5):
    """Create a hash of the line geometry (simplified) for duplicate detection"""
    if len(coords) < 2:
        return None
    
    # Take first, middle, and last point to represent line
    start = coords[0]
    middle = coords[len(coords) // 2]
    end = coords[-1]
    
    # Round coordinates for comparison
    start = (round(start[0], precision), round(start[1], precision))
    middle = (round(middle[0], precision), round(middle[1], precision))
    end = (round(end[0], precision), round(end[1], precision))
    
    # Sort endpoints to make hash direction-agnostic
    if start > end:
        start, end = end, start
        
    return f"{start[0]}:{start[1]}:{middle[0]}:{middle[1]}:{end[0]}:{end[1]}"

def simplify_geojson(input_file, output_file, tolerance=10, min_length=50, 
                    keep_highway_types=None, remove_duplicates=True):
    """
    Simplify a GeoJSON file by:
    1. Reducing coordinate points using Douglas-Peucker algorithm
    2. Removing duplicate roads
    3. Filtering by road type and minimum length
    
    Args:
        input_file: Path to input GeoJSON
        output_file: Path to output simplified GeoJSON
        tolerance: Simplification tolerance in meters
        min_length: Minimum length of road segment to keep (meters)
        keep_highway_types: List of highway types to keep (e.g. ['primary', 'secondary']) or None to keep all
        remove_duplicates: Whether to attempt to remove duplicate roads
    """
    print(f"Loading GeoJSON from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features = data['features']
    total_features = len(features)
    print(f"Found {total_features} road segments in original file")
    
    # Convert tolerance to approximate degrees
    # Rough approximation: 1 degree ~ 111km at equator
    tolerance_degrees = tolerance / 111000
    
    simplified_features = []
    unique_lines = {}  # For duplicate detection
    
    stats = {
        'total_original': total_features,
        'skipped_highway_type': 0,
        'skipped_too_short': 0,
        'skipped_duplicate': 0,
        'kept': 0
    }
    
    print(f"Processing and simplifying road segments...")
    for i, feature in enumerate(features):
        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/{total_features} segments...")
        
        if feature['geometry']['type'] != 'LineString':
            continue
        
        # Check highway type
        highway_type = feature['properties'].get('highway')
        if keep_highway_types and highway_type not in keep_highway_types:
            stats['skipped_highway_type'] += 1
            continue
        
        # Get coordinates and simplify
        coords = feature['geometry']['coordinates']
        
        # Skip if too few points
        if len(coords) < 2:
            continue
            
        # Calculate segment length
        segment_length = 0
        for i in range(len(coords) - 1):
            segment_length += haversine_distance(
                coords[i][1], coords[i][0],
                coords[i+1][1], coords[i+1][0]
            )
            
        # Skip if too short
        if segment_length < min_length:
            stats['skipped_too_short'] += 1
            continue
        
        # Create LineString and simplify with Douglas-Peucker algorithm
        line = LineString(coords)
        simplified_line = line.simplify(tolerance_degrees)
        
        # Skip if simplified too aggressively
        if len(simplified_line.coords) < 2:
            continue
            
        # Update feature with simplified geometry
        simplified_coords = list(mapping(simplified_line)['coordinates'])
        feature['geometry']['coordinates'] = simplified_coords
        
        # Check for duplicates
        if remove_duplicates:
            line_hash = get_line_hash(simplified_coords)
            if line_hash in unique_lines:
                stats['skipped_duplicate'] += 1
                continue
            unique_lines[line_hash] = True
        
        simplified_features.append(feature)
        stats['kept'] += 1
    
    # Create new GeoJSON
    data['features'] = simplified_features
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Write the output
    print(f"Writing simplified GeoJSON to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    
    # Print statistics
    print("\nSimplification Statistics:")
    print(f"Original segments: {stats['total_original']}")
    print(f"Skipped (wrong highway type): {stats['skipped_highway_type']}")
    print(f"Skipped (too short): {stats['skipped_too_short']}")
    print(f"Skipped (duplicate): {stats['skipped_duplicate']}")
    print(f"Kept segments: {stats['kept']}")
    print(f"Reduction: {round(100 * (1 - stats['kept'] / stats['total_original']), 1)}%")
    
    print(f"\nSimplification completed successfully!")
    return stats

def parse_arguments():
    parser = argparse.ArgumentParser(description='Simplify GeoJSON road networks for ACO Route Creator')
    
    parser.add_argument('input', help='Path to input GeoJSON file')
    parser.add_argument('-o', '--output', help='Path to output simplified GeoJSON file (default: input_simplified.geojson)')
    parser.add_argument('-t', '--tolerance', type=float, default=10.0, 
                        help='Simplification tolerance in meters (default: 10)')
    parser.add_argument('-m', '--min-length', type=float, default=50.0,
                        help='Minimum road segment length in meters to keep (default: 50)')
    parser.add_argument('--highway-types', nargs='+', 
                        default=['motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified'],
                        help='Highway types to keep (default: motorway trunk primary secondary tertiary unclassified)')
    parser.add_argument('--keep-all-types', action='store_true', 
                        help='Keep all highway types (overrides --highway-types)')
    parser.add_argument('--keep-duplicates', action='store_true',
                        help='Do not attempt to remove duplicate road segments')
    
    args = parser.parse_args()
    
    # Handle default output file
    if not args.output:
        base, ext = os.path.splitext(args.input)
        args.output = f"{base}_simplified{ext}"
    
    return args

if __name__ == "__main__":
    args = parse_arguments()
    
    highway_types = None if args.keep_all_types else args.highway_types
    
    simplify_geojson(
        args.input, 
        args.output,
        tolerance=args.tolerance,
        min_length=args.min_length,
        keep_highway_types=highway_types,
        remove_duplicates=not args.keep_duplicates
    )
