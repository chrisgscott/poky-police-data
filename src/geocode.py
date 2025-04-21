"""
Geocoding helper for Alameda Police Data ETL.
"""

import pandas as pd
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import logging


def geocode_addresses(df, cache_path):
    """Geocode unique addresses in df, using cache_path for results."""
    # Load cache
    try:
        cache = pd.read_csv(cache_path, dtype={'address': str, 'lat': float, 'lon': float})
    except Exception:
        cache = pd.DataFrame(columns=['address', 'lat', 'lon'])
    cache = cache.drop_duplicates('address').set_index('address')
    geolocator = Nominatim(user_agent='poky-police-data')
    addresses = df['address'].unique()
    new_rows = []
    STREET_TYPES = ["St", "Ave", "Dr", "Rd", "Blvd", "Pl", "Ct", "Ln", "Way", "Cir", "Ter"]
    intersection_addresses = []
    for addr in addresses:
        if addr in cache.index and pd.notnull(cache.loc[addr, 'lat']) and pd.notnull(cache.loc[addr, 'lon']):
            continue
        if '&' in addr:
            intersection_addresses.append(addr)
            logging.info(f'Skipping intersection address: {addr}')
            continue
        orig_addr = addr
        tried_fallback = False
        # 1. Try as-is
        try:
            location = geolocator.geocode(addr, timeout=10)
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            location = None
            logging.warning(f'Geocode failed for {addr}: {e}')
        # 2. If fail and not intersection, try appending street types
        if not location:
            tried_fallback = True
            # Only try if address before first comma is missing a street type
            street_part = addr.split(',')[0].strip()
            if not any(street_part.upper().endswith(f" {stype.upper()}") for stype in STREET_TYPES):
                base = ','.join(addr.split(',')[1:]).strip()
                for stype in STREET_TYPES:
                    mod_addr = f"{street_part} {stype}, {base}"
                    try:
                        location = geolocator.geocode(mod_addr, timeout=10)
                        if location:
                            logging.info(f'Geocoded (added type): {mod_addr} -> ({location.latitude:.5f}, {location.longitude:.5f})')
                            break
                    except Exception:
                        continue
        # 3. Save result (success or fail)
        if location:
            lat, lon = location.latitude, location.longitude
            new_rows.append({'address': orig_addr, 'lat': lat, 'lon': lon})
            if tried_fallback:
                logging.info(f'Geocoded (with fallback): {orig_addr} -> ({lat:.5f}, {lon:.5f})')
            else:
                logging.info(f'Geocoded: {orig_addr} -> ({lat:.5f}, {lon:.5f})')
        else:
            new_rows.append({'address': orig_addr, 'lat': None, 'lon': None})
            logging.warning(f'No geocode result: {orig_addr}')
        time.sleep(1)  # Be nice to Nominatim
    # Save skipped intersection addresses for manual review
    if intersection_addresses:
        pd.DataFrame({'address': intersection_addresses}).to_csv('cache/intersection_addresses.csv', index=False)
        logging.info(f'Saved {len(intersection_addresses)} intersection addresses to cache/intersection_addresses.csv for manual review.')
    if new_rows:
        new_cache = pd.DataFrame(new_rows).set_index('address')
        cache = pd.concat([cache, new_cache])
        cache = cache[~cache.index.duplicated(keep='last')]
        cache.reset_index().to_csv(cache_path, index=False)
    # Merge geocodes into main df
    cache = cache.reset_index()
    df = df.merge(cache, on='address', how='left')
    return df
