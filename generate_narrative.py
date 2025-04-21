import pandas as pd

df = pd.read_csv('data/clean_incidents.csv')
with open('data_narrative.md', 'w') as f:
    f.write('# Police Incident Data Narrative Summary\n\n')
    f.write(f'This summary is based on {len(df):,} police incident records for Pocatello, ID.\n\n')
    # Time span
    if 'year' in df.columns:
        f.write('## Time Span\n')
        f.write(f'- Years covered: {df["year"].min()} to {df["year"].max()}\n')
        f.write('\n')
    if 'reported_dt' in df.columns:
        f.write(f'- First incident: {df["reported_dt"].min()}\n')
        f.write('\n')
    # Overall trends
    if 'year' in df.columns:
        f.write('## Overall Trends\n')
        by_year = df.groupby('year').size()
        f.write('- Incidents per year:\n')
        for y, n in by_year.items():
            f.write(f'    - {y}: {n:,}\n')
        f.write('\n')
    if 'nature_grp' in df.columns:
        f.write('## Incident Type Breakdown\n')
        for grp, n in df["nature_grp"].value_counts().items():
            f.write(f'- {grp}: {n:,} incidents\n')
        f.write('\n')
    if 'area' in df.columns:
        f.write('## Incidents by Area\n')
        for area, n in df["area"].value_counts().items():
            f.write(f'- {area}: {n:,} incidents\n')
        f.write('\n')
    if 'address' in df.columns:
        top_addr = df["address"].value_counts().idxmax()
        f.write('## Most Common Address\n')
        f.write(f'- {top_addr}\n')
