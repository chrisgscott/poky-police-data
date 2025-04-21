"""
ETL utilities for Alameda Police Data project.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import re

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import re
import logging

def load_and_clean_xlsx(raw_dir):
    """Load and clean all Excel files from raw_dir."""
    files = list(Path(raw_dir).glob('20*.xlsx'))
    dfs = []
    for f in files:
        df = pd.read_excel(f, dtype=str)
        logging.info(f"Loaded {f.name} with columns: {list(df.columns)}")
        dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)
    logging.info(f"After concatenation: {len(df)} rows\nSample:\n{df.head()}")
    # Standardize columns
    # Map normalized columns to expected names
    col_map = {
        'incident_id': 'incident',
        'nature': 'nature',
        'area': 'area',
        'agency': 'agency',
        'reported_dt_raw': 'reported',
        'address': 'incident_address'
    }
    colnames = [c.lower().strip().replace(' ', '_') for c in df.columns]
    df.columns = colnames
    missing = [v for v in col_map.values() if v not in df.columns]
    if missing:
        logging.error(f"Missing columns after normalization: {missing}")
        logging.error(f"Available columns: {list(df.columns)}")
        raise ValueError(f"Required columns missing: {missing}. Available columns: {list(df.columns)}")
    # Rename columns to match expected names
    df = df.rename(columns={v: k for k, v in col_map.items()})
    df = df[list(col_map.keys())]
    logging.info(f"After renaming/selecting columns: {len(df)} rows\nSample:\n{df.head()}")
    # Clean and parse dates
    df['reported_dt_raw'] = df['reported_dt_raw'].astype(str).str.strip()
    def parse_dt(val):
        for fmt in ('%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M', '%m/%d/%Y %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%H:%M:%S %m/%d/%y'):
            try:
                return datetime.strptime(val, fmt)
            except Exception:
                continue
        return pd.NaT
    df['reported_dt'] = df['reported_dt_raw'].apply(parse_dt)
    logging.info(f"After parsing dates: {len(df)} rows\nSample:\n{df[['reported_dt_raw','reported_dt']].head()}")
    # Drop rows with bad dates or empty address
    before_drop = len(df)
    df = df[~df['reported_dt'].isna()]
    df = df[df['address'].notnull() & (df['address'].astype(str).str.strip() != '')]
    logging.info(f"After dropping bad dates/empty addresses: {len(df)} rows (dropped {before_drop - len(df)})\nSample:\n{df.head()}")
    # Strip business/descriptor after semicolon for geocoding
    df['address'] = df['address'].astype(str).str.split(';').str[0].str.strip()
    # Add city/state/zip context for geocoding
    df['address'] = df['address'] + ', Pocatello, ID 83201'
    logging.info(f"After cleaning and appending city/state/zip: Sample addresses:\n{df['address'].head()}")
    # Derived date parts
    df['year'] = df['reported_dt'].dt.year
    df['month'] = df['reported_dt'].dt.month
    df['day'] = df['reported_dt'].dt.day
    df['hour'] = df['reported_dt'].dt.hour
    df['dow'] = df['reported_dt'].dt.dayofweek
    # Clean nature
    df['nature'] = df['nature'].astype(str).str.strip().str.upper()
    # Drop junk rows
    df = df[df['nature'] != '']
    # Recode nature
    def recode_nature(val):
        if any(x in val for x in ['THEFT','BURGLARY','LARCENY','SHOPLIFT','ROBBERY']):
            return 'PROPERTY'
        if any(x in val for x in ['ASSAULT','BATTERY','WEAPON','DOMESTIC','SEX']):
            return 'VIOLENT'
        if any(x in val for x in ['DISTURBANCE','DISORDERLY','HARASS','NOISE']):
            return 'DISORDER'
        if any(x in val for x in ['DUI','CRASH','TRAFFIC','ABANDONED VEHIC']):
            return 'TRAFFIC'
        if any(x in val for x in ['WELFARE CHECK','MENTAL','SUICIDE','MISSING']):
            return 'SERVICE'
        return 'OTHER'
    df['nature_grp'] = df['nature'].apply(recode_nature)
    df = df.reset_index(drop=True)
    return df
