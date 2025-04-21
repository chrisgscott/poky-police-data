"""
Main orchestrator for Alameda Police Data ETL, geocoding, and analytics build.
"""

from pathlib import Path
import logging
import pandas as pd
from etl import load_and_clean_xlsx
from geocode import geocode_addresses
from vis import build_charts, build_heatmap

RAW_DIR = Path('data/raw')
OUT_DIR = Path('data')
CACHE_DIR = Path('cache')
CHARTS_DIR = Path('charts')
MAPS_DIR = Path('maps')
BUILD_DIR = Path('build')
CACHE_FILE = CACHE_DIR / 'geocode_cache.csv'
CLEAN_CSV = OUT_DIR / 'clean_incidents.csv'

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

def ensure_dirs():
    for d in [RAW_DIR, OUT_DIR, CACHE_DIR, CHARTS_DIR, MAPS_DIR, BUILD_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def main():
    logging.info('Starting Alameda Police Data build process.')
    ensure_dirs()
    logging.info('Loading and cleaning Excel files...')
    df = load_and_clean_xlsx(RAW_DIR)
    logging.info(f'Loaded {len(df):,} records.')
    logging.info('Geocoding addresses (with cache)...')
    df = geocode_addresses(df, CACHE_FILE)
    logging.info('Building static charts...')
    build_charts(df, CHARTS_DIR)
    logging.info('Building heatmap...')
    build_heatmap(df, MAPS_DIR)
    logging.info(f'Writing tidy CSV to {CLEAN_CSV}')
    df.to_csv(CLEAN_CSV, index=False)
    logging.info('Build complete. See /build for deliverables.')

if __name__ == '__main__':
    main()
