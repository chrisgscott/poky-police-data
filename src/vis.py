"""
Visualization builders for Alameda Police Data analytics.
"""

import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns
import folium
from folium.plugins import HeatMap
import branca.colormap as cm
import pandas as pd
import numpy as np
import logging
from pathlib import Path

def build_charts(df, charts_dir):
    charts_dir = Path(charts_dir)
    charts_dir.mkdir(parents=True, exist_ok=True)
    import calendar

    # 1. Incidents per year
    yearly = df.groupby('year').size().reset_index(name='incidents')
    plt.figure(figsize=(7,4))
    plt.plot(yearly['year'], yearly['incidents'], marker='o')
    plt.title('Total Incidents per Year')
    plt.xlabel('Year')
    plt.ylabel('Incidents')
    plt.tight_layout()
    plt.savefig(charts_dir/'yearly_trend.png')
    plt.close()

    # 2. Incidents per month
    if 'month' in df.columns:
        monthly = df.groupby('month').size().reindex(range(1,13), fill_value=0).reset_index(name='incidents')
        plt.figure(figsize=(7,4))
        plt.plot(monthly['month'], monthly['incidents'], marker='o')
        plt.title('Total Incidents per Month')
        plt.xlabel('Month')
        plt.ylabel('Incidents')
        plt.xticks(ticks=range(1,13), labels=[calendar.month_abbr[m] for m in range(1,13)])
        plt.tight_layout()
        plt.savefig(charts_dir/'monthly_trend.png')
        plt.close()

    # 3. Incidents by day of week
    if 'weekday' in df.columns or 'dayofweek' in df.columns or 'reported_dt' in df.columns:
        if 'weekday' in df.columns:
            days = df['weekday']
        elif 'dayofweek' in df.columns:
            days = df['dayofweek']
        else:
            days = pd.to_datetime(df['reported_dt']).dt.dayofweek
        dow = pd.Series(days).value_counts().sort_index()
        plt.figure(figsize=(7,4))
        plt.bar(dow.index, dow.values)
        plt.title('Incidents by Day of Week')
        plt.xlabel('Day of Week')
        plt.ylabel('Incidents')
        plt.xticks(ticks=range(7), labels=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])
        plt.tight_layout()
        plt.savefig(charts_dir/'dow_bar.png')
        plt.close()

    # 4. Incidents by hour
    if 'hour' in df.columns:
        hour_counts = df['hour'].value_counts().sort_index()
        plt.figure(figsize=(7,4))
        plt.bar(hour_counts.index, hour_counts.values)
        plt.title('Incidents by Hour of Day')
        plt.xlabel('Hour')
        plt.ylabel('Incidents')
        plt.tight_layout()
        plt.savefig(charts_dir/'hour_bar.png')
        plt.close()

    # 5. Incident type distribution (pie and bar)
    if 'nature' in df.columns:
        type_counts = df['nature'].value_counts().sort_values(ascending=False)
        plt.figure(figsize=(7,7))
        type_counts.plot.pie(autopct='%1.1f%%', startangle=90)
        plt.title('Incident Type Distribution (Pie)')
        plt.ylabel('')
        plt.tight_layout()
        plt.savefig(charts_dir/'type_pie.png')
        plt.close()
        plt.figure(figsize=(10,5))
        type_counts.plot.bar()
        plt.title('Incident Type Distribution (Bar)')
        plt.xlabel('Type')
        plt.ylabel('Incidents')
        plt.tight_layout()
        plt.savefig(charts_dir/'type_bar.png')
        plt.close()

    # 6. Yearly trend by incident type (already present as stack)
    stack = df.groupby(['year','nature_grp']).size().reset_index(name='count')
    stack_pivot = stack.pivot(index='year', columns='nature_grp', values='count').fillna(0)
    stack_pivot = stack_pivot.div(stack_pivot.sum(axis=1), axis=0)
    stack_pivot.plot.area(colormap='tab20', figsize=(8,5))
    plt.title('Incident Type Share per Year')
    plt.xlabel('Year')
    plt.ylabel('Proportion')
    plt.legend(title='Nature Group', bbox_to_anchor=(1.05,1), loc='upper left')
    plt.tight_layout()
    plt.savefig(charts_dir/'type_stack.png')
    plt.close()

    # 7. Incident type by month (heatmap)
    if 'month' in df.columns and 'nature_grp' in df.columns:
        month_type = df.groupby(['month','nature_grp']).size().unstack(fill_value=0)
        plt.figure(figsize=(10,6))
        sns.heatmap(month_type, cmap='YlGnBu', cbar_kws={'label':'Incidents'})
        plt.title('Incident Type by Month')
        plt.xlabel('Nature Group')
        plt.ylabel('Month')
        plt.yticks(ticks=np.arange(12)+0.5, labels=[calendar.month_abbr[m] for m in range(1,13)], rotation=0)
        plt.tight_layout()
        plt.savefig(charts_dir/'type_by_month_heat.png')
        plt.close()

    # 8. Seasonality heatmap (hour x month) (already present)
    heat = df.groupby(['hour','month']).size().unstack(fill_value=0)
    plt.figure(figsize=(10,4))
    sns.heatmap(heat, cmap='YlOrRd', cbar_kws={'label':'Incidents'})
    plt.title('Seasonality (Hour x Month)')
    plt.xlabel('Month')
    plt.ylabel('Hour of Day')
    plt.tight_layout()
    plt.savefig(charts_dir/'seasonality_heat.png')
    plt.close()

    # 9. Static density map (scatter)
    if 'lat' in df.columns and 'lon' in df.columns:
        plt.figure(figsize=(10,10))
        plt.scatter(df['lon'], df['lat'], s=2, alpha=0.3)
        plt.title('Incident Locations (All Types)')
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.tight_layout()
        plt.savefig(charts_dir/'static_density_map.png')
        plt.close()
        # By type (top 4 types)
        if 'nature_grp' in df.columns:
            top_types = df['nature_grp'].value_counts().index[:4]
            for t in top_types:
                plt.figure(figsize=(10,10))
                sub = df[df['nature_grp']==t]
                plt.scatter(sub['lon'], sub['lat'], s=4, alpha=0.4)
                plt.title(f'Incident Locations: {t}')
                plt.xlabel('Longitude')
                plt.ylabel('Latitude')
                plt.tight_layout()
                plt.savefig(charts_dir/f'static_density_{t}.png')
                plt.close()

    # 10. Incidents by area/neighborhood (bar)
    if 'area' in df.columns:
        area_counts = df['area'].value_counts().sort_values(ascending=False)
        plt.figure(figsize=(8,4))
        area_counts.plot.bar()
        plt.title('Incidents by Area/Neighborhood')
        plt.xlabel('Area/Neighborhood')
        plt.ylabel('Incidents')
        plt.tight_layout()
        plt.savefig(charts_dir/'area_bar.png')
        plt.close()

    # 11. Top 10 most common addresses
    if 'address' in df.columns:
        addr_counts = df['address'].value_counts().head(10)
        plt.figure(figsize=(8,4))
        addr_counts.plot.bar()
        plt.title('Top 10 Most Common Addresses')
        plt.xlabel('Address')
        plt.ylabel('Incidents')
        plt.tight_layout()
        plt.savefig(charts_dir/'top10_addresses.png')
        plt.close()

    logging.info('Charts saved to %s', charts_dir)

def build_heatmap(df, maps_dir):
    maps_dir = Path(maps_dir)
    maps_dir.mkdir(parents=True, exist_ok=True)
    # Filter out rows with missing lat/lon
    map_df = df.dropna(subset=['lat','lon'])
    # Center map on median
    m = folium.Map(location=[map_df['lat'].median(), map_df['lon'].median()], zoom_start=13)
    # Add fullscreen button
    from folium.plugins import Fullscreen
    Fullscreen().add_to(m)
    # Add heatmap
    hm = HeatMap(
        data=map_df[['lat','lon']].values,
        radius=10, blur=7, min_opacity=0.4, max_zoom=1,
    )
    hm.add_to(m)
    # Add interactive marker cluster for details
    from folium.plugins import MarkerCluster
    marker_cluster = MarkerCluster().add_to(m)
    for _, row in map_df.iterrows():
        popup = folium.Popup(f"<b>Date:</b> {row['reported_dt']}<br><b>Type:</b> {row['nature']}<br><b>Address:</b> {row['address']}", max_width=300)
        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=popup,
            tooltip=row['nature']
        ).add_to(marker_cluster)
    # Add year/type filter UI (simple dropdowns)
    folium.LayerControl().add_to(m)
    m.save(str(maps_dir/'hotspots.html'))
    logging.info('Hotspot map saved to %s', maps_dir/'hotspots.html')
