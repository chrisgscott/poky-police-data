import pandas as pd

df = pd.read_csv('data/clean_incidents.csv')
print('Total incidents:', len(df))
if 'year' in df.columns:
    print('Years:', df['year'].min(), 'to', df['year'].max())
if 'reported_dt' in df.columns:
    print('First incident date:', df["reported_dt"].min())
print('\nIncidents per year:')
if 'year' in df.columns:
    print(df.groupby('year').size().to_string())
print('\nIncident type breakdown:')
if 'nature_grp' in df.columns:
    print(df['nature_grp'].value_counts().to_string())
print('\nIncidents by area:')
if 'area' in df.columns:
    print(df['area'].value_counts().to_string())
print('\nMost common address:')
if 'address' in df.columns:
    print(df['address'].value_counts().idxmax())
