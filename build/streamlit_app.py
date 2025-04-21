import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_folium import folium_static
import folium
from folium.plugins import HeatMap, MarkerCluster, Fullscreen
from pathlib import Path

st.set_page_config(page_title="Alameda Police Dashboard", layout="wide")

st.title("Alameda Police Incidents Dashboard")

DATA_PATH = Path('data/clean_incidents.csv')

def load_data():
    df = pd.read_csv(DATA_PATH)
    if 'reported_dt' in df.columns:
        df['reported_dt'] = pd.to_datetime(df['reported_dt'], errors='coerce')
        if 'dayofweek' not in df.columns:
            df['dayofweek'] = df['reported_dt'].dt.day_name()
        if 'month' not in df.columns:
            df['month'] = df['reported_dt'].dt.month
        if 'hour' not in df.columns:
            df['hour'] = df['reported_dt'].dt.hour
    return df

df = load_data()

# --- Tab Setup ---
chart_tabs = [
    "Map",
    "Yearly Trend",
    "Monthly Trend",
    "Day of Week",
    "Hour of Day",
    "Incident Type Bar",
    "Incident Type Pie",
    "Nature Group Bar",
    "Seasonality Heatmap",
    "Incident Location Scatter"
]
tabs = st.tabs(chart_tabs)

# --- Tab 1: Interactive Map ---
with tabs[0]:
    st.markdown('### Hotspot Map')
    all_types = sorted(df['nature_grp'].dropna().unique())
    type_selection = st.multiselect('Incident Types to Show', all_types, default=all_types)
    filtered_df = df[df['nature_grp'].isin(type_selection)]
    if filtered_df.empty:
        st.warning('No data for selected types.')
    else:
        map_df = filtered_df.dropna(subset=['lat','lon'])
        m = folium.Map(location=[map_df['lat'].median(), map_df['lon'].median()], zoom_start=13)
        Fullscreen().add_to(m)
        if not map_df.empty:
            # Heatmap layer
            hm = HeatMap(
                data=map_df[['lat','lon']].values,
                radius=10, blur=7, min_opacity=0.4, max_zoom=1,
                name='Heatmap'
            )
            hm.add_to(m)

            # MarkerCluster layer with interactive popups
            marker_cluster = MarkerCluster(name='Incidents').add_to(m)
            for _, row in map_df.iterrows():
                popup = folium.Popup(f"<b>Date:</b> {row['reported_dt']}<br><b>Type:</b> {row['nature_grp']}<br><b>Address:</b> {row['address']}", max_width=300)
                folium.Marker(
                    location=[row['lat'], row['lon']],
                    popup=popup,
                    tooltip=f"{row['nature_grp']}<br>{row['reported_dt']}"
                ).add_to(marker_cluster)

            # Optional: Add a summary circle marker layer for counts per location
            loc_counts = map_df.groupby(['lat','lon']).size().reset_index(name='count')
            for _, row in loc_counts.iterrows():
                if row['count'] > 1:
                    folium.CircleMarker(
                        location=[row['lat'], row['lon']],
                        radius=6 + row['count']**0.5,
                        color='blue', fill=True, fill_opacity=0.3,
                        popup=folium.Popup(f"{row['count']} incidents at this location", max_width=200),
                        tooltip=f"{row['count']} incidents"
                    ).add_to(m)
        folium.LayerControl().add_to(m)
        import streamlit.components.v1 as components
        folium_map_html = m.get_root().render()
        components.html(folium_map_html, width=1200, height=700)

# --- Tab 2: Yearly Trend ---
with tabs[1]:
    st.markdown('### Yearly Trend (Incidents per Year)')
    chart_types = sorted(df['nature_grp'].dropna().unique())
    chart_type_sel = st.multiselect('Incident Types to Include', chart_types, default=chart_types, key='yearly_trend_types')
    filtered = df[df['nature_grp'].isin(chart_type_sel)]
    yearly = filtered.groupby('year').size().reset_index(name='incidents')
    fig = px.line(yearly, x='year', y='incidents', markers=True, title='Incidents per Year')
    st.plotly_chart(fig, use_container_width=True, key="yearly_trend")
    st.download_button('Download Data', data=yearly.to_csv(index=False), file_name='yearly_trend.csv', mime='text/csv', key='download_yearly_trend')

# --- Tab 3: Monthly Trend ---
with tabs[2]:
    st.markdown('### Monthly Trend (Average Incidents per Month, All Full Years)')
    chart_types = sorted(df['nature_grp'].dropna().unique())
    chart_type_sel = st.multiselect('Incident Types to Include', chart_types, default=chart_types, key='monthly_trend_types')
    filtered = df[df['nature_grp'].isin(chart_type_sel)]
    if 'month' in filtered.columns and 'year' in filtered.columns:
        df_complete = filtered[filtered['year'] < 2025]  # drop the partial year
        monthly_avg = df_complete.groupby(['year','month']).size().groupby('month').mean().reset_index(name='avg_incidents')
        fig_avg = px.bar(monthly_avg, x='month', y='avg_incidents', title='Average Incidents per Month (Excludes Partial 2025)')
        st.plotly_chart(fig_avg, use_container_width=True, key="monthly_avg_trend")
        st.download_button('Download Data', data=monthly_avg.to_csv(index=False), file_name='monthly_avg_trend.csv', mime='text/csv', key='download_monthly_avg_trend')
        st.caption('This chart shows the average number of incidents per month, excluding partial 2025 data.')
        st.markdown('---')
        st.markdown('#### Raw Monthly Totals (All Data)')
        monthly = filtered.groupby('month').size().reset_index(name='incidents')
        fig_raw = px.bar(monthly, x='month', y='incidents', title='Raw Incident Totals per Month')
        st.plotly_chart(fig_raw, use_container_width=True, key="monthly_trend_raw")
        st.download_button('Download Data', data=monthly.to_csv(index=False), file_name='monthly_trend_raw.csv', mime='text/csv', key='download_monthly_trend_raw')
        st.caption('Counts reflect 6 months of January–March data but only 5 months of October–December; 2025 data are partial.')
    else:
        st.info('No month data available.')

# --- Tab 4: Day of Week ---
with tabs[3]:
    st.markdown('### Day of Week Trend')
    chart_types = sorted(df['nature_grp'].dropna().unique())
    chart_type_sel = st.multiselect('Incident Types to Include', chart_types, default=chart_types, key='dow_trend_types')
    filtered = df[df['nature_grp'].isin(chart_type_sel)]
    if 'dayofweek' in filtered.columns:
        dow = filtered.groupby('dayofweek').size().reset_index(name='incidents')
        fig = px.bar(dow, x='dayofweek', y='incidents', title='Incidents by Day of Week', category_orders={'dayofweek': ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']})
        st.plotly_chart(fig, use_container_width=True, key="dow_trend")
        st.download_button('Download Data', data=dow.to_csv(index=False), file_name='dayofweek_trend.csv', mime='text/csv', key='download_dow_trend')
    else:
        st.info('No day of week data available.')

# --- Tab 5: Hour of Day ---
with tabs[4]:
    st.markdown('### Hour of Day Trend')
    chart_types = sorted(df['nature_grp'].dropna().unique())
    chart_type_sel = st.multiselect('Incident Types to Include', chart_types, default=chart_types, key='hour_trend_types')
    filtered = df[df['nature_grp'].isin(chart_type_sel)]
    if 'hour' in filtered.columns:
        hour = filtered.groupby('hour').size().reset_index(name='incidents')
        fig = px.bar(hour, x='hour', y='incidents', title='Incidents by Hour of Day')
        st.plotly_chart(fig, use_container_width=True, key="hour_trend")
        st.download_button('Download Data', data=hour.to_csv(index=False), file_name='hour_trend.csv', mime='text/csv', key='download_hour_trend')
    else:
        st.info('No hour data available.')

# --- Tab 6: Incident Type Bar ---
with tabs[5]:
    st.markdown('### Incident Type Distribution (Bar)')
    chart_types = sorted(df['nature_grp'].dropna().unique())
    chart_type_sel = st.multiselect('Incident Types to Include', chart_types, default=chart_types, key='type_bar_types')
    filtered = df[df['nature_grp'].isin(chart_type_sel)]
    type_dist = filtered['nature'].value_counts().reset_index()
    type_dist.columns = ['nature', 'incidents']
    fig = px.bar(type_dist, x='nature', y='incidents', title='Incident Type Distribution (Bar)')
    st.plotly_chart(fig, use_container_width=True, key="type_dist_bar")
    st.download_button('Download Data', data=type_dist.to_csv(index=False), file_name='type_dist_bar.csv', mime='text/csv', key='download_type_dist_bar')

# --- Tab 7: Incident Type Pie ---
with tabs[6]:
    st.markdown('### Incident Type Distribution (Pie)')
    chart_types = sorted(df['nature_grp'].dropna().unique())
    chart_type_sel = st.multiselect('Incident Types to Include', chart_types, default=chart_types, key='type_pie_types')
    filtered = df[df['nature_grp'].isin(chart_type_sel)]
    type_dist = filtered['nature'].value_counts().reset_index()
    type_dist.columns = ['nature', 'incidents']
    fig = px.pie(type_dist, names='nature', values='incidents', title='Incident Type Distribution (Pie)')
    st.plotly_chart(fig, use_container_width=True, key="type_dist_pie")
    st.download_button('Download Data', data=type_dist.to_csv(index=False), file_name='type_dist_pie.csv', mime='text/csv', key='download_type_dist_pie')

# --- Tab 8: Nature Group Bar ---
with tabs[7]:
    st.markdown('### Nature Group Distribution (Bar)')
    chart_types = sorted(df['nature_grp'].dropna().unique())
    chart_type_sel = st.multiselect('Incident Types to Include', chart_types, default=chart_types, key='nature_grp_bar_types')
    filtered = df[df['nature_grp'].isin(chart_type_sel)]
    if 'nature_grp' in filtered.columns:
        grp = filtered['nature_grp'].value_counts().reset_index()
        grp.columns = ['nature_grp', 'incidents']
        fig = px.bar(grp, x='nature_grp', y='incidents', title='Nature Group Distribution (Bar)')
        st.plotly_chart(fig, use_container_width=True, key="nature_grp_bar")
        st.download_button('Download Data', data=grp.to_csv(index=False), file_name='nature_grp_bar.csv', mime='text/csv', key='download_nature_grp_bar')
    else:
        st.info('No nature group data available.')

# --- Tab 9: Seasonality Heatmap ---
with tabs[8]:
    st.markdown('### Seasonality Heatmap (Hour x Month)')
    chart_types = sorted(df['nature_grp'].dropna().unique())
    chart_type_sel = st.multiselect('Incident Types to Include', chart_types, default=chart_types, key='seasonality_heatmap_types')
    filtered = df[df['nature_grp'].isin(chart_type_sel)]
    if 'hour' in filtered.columns and 'month' in filtered.columns:
        heatmap_data = filtered.groupby(['month','hour']).size().reset_index(name='incidents')
        heatmap_pivot = heatmap_data.pivot(index='hour', columns='month', values='incidents').fillna(0)
        import plotly.figure_factory as ff
        z = heatmap_pivot.values
        x = [str(m) for m in heatmap_pivot.columns]
        y = [str(h) for h in heatmap_pivot.index]
        fig = ff.create_annotated_heatmap(z, x=x, y=y, colorscale='Viridis', showscale=True, annotation_text=z.astype(int))
        fig.update_layout(title_text='Seasonality Heatmap (Hour x Month)', xaxis_title='Month', yaxis_title='Hour of Day')
        st.plotly_chart(fig, use_container_width=True, key="seasonality_heatmap")
        st.download_button('Download Data', data=heatmap_data.to_csv(index=False), file_name='seasonality_heatmap.csv', mime='text/csv', key='download_seasonality_heatmap')
    else:
        st.info('No hour or month data available for heatmap.')

# --- Tab 10: Incident Location Scatter ---
with tabs[9]:
    st.markdown('### Incident Locations (Scatter Map)')
    chart_types = sorted(df['nature_grp'].dropna().unique())
    chart_type_sel = st.multiselect('Incident Types to Include', chart_types, default=chart_types, key='location_scatter_types')
    filtered = df[df['nature_grp'].isin(chart_type_sel)]
    if 'lat' in filtered.columns and 'lon' in filtered.columns:
        fig = px.scatter_mapbox(filtered.dropna(subset=['lat','lon']), lat='lat', lon='lon', hover_data=['reported_dt','nature','address'],
                               title='Incident Locations', zoom=11, height=600)
        fig.update_layout(mapbox_style="open-street-map")
        st.plotly_chart(fig, use_container_width=True, key="location_scatter")
    else:
        st.info('No location data available.')
