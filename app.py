
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

st.set_page_config(page_title="Urban Mobility Analytics", layout="wide")

st.title("Urban Mobility Analytics Dashboard")
st.markdown("Analyzing peak loads, detecting anomalies, and visualizing interactive zone maps to help planners reduce congestion.")

@st.cache_data
def generate_data():
    np.random.seed(42)
    n = 500
    rng = np.random.default_rng(42)

    passengers = np.random.randint(200, 5000, n).astype(object)
    delay_min = np.random.choice([np.nan, 0, 5, 10, 15, 30], n)
    zone = list(np.random.choice(['North', 'South', 'East', 'West', 'Central'], n))
    route_id = list(np.random.choice([f'R{i:02d}' for i in range(1, 51)], n))
    dates = list(pd.date_range('2022-01-01', periods=n, freq='D'))

    idx = rng.choice(n, size=40, replace=False)
    for i in idx[:15]: passengers[i] = np.nan
    for i in idx[15:25]: passengers[i] = str(passengers[i] or 0).split('.')[0] + ' pax'
    for i in idx[25:32]: zone[i] = zone[i].lower()
    for i in idx[32:37]: route_id[i] = ' ' + route_id[i] + ' '
    for i in idx[37:40]: delay_min[i] = -999
    for i in rng.choice(n, 8): passengers[i] = 99999

    df = pd.DataFrame({
        'route_id': route_id,
        'date': dates,
        'passengers': passengers,
        'delay_min': delay_min,
        'zone': zone
    })
    return df

@st.cache_data
def clean_data(df):
    df = df.copy()
    df['passengers'] = pd.to_numeric(df['passengers'], errors='coerce')
    df['passengers'] = df['passengers'].fillna(df['passengers'].median())

    mean_p = df['passengers'].mean()
    std_p = df['passengers'].std()
    upper_limit = mean_p + 3 * std_p
    p99 = df['passengers'].quantile(0.99)
    df.loc[df['passengers'] > upper_limit, 'passengers'] = p99

    df['delay_min'] = df['delay_min'].replace(-999, np.nan)
    df['route_id'] = df['route_id'].str.strip()

    df['delay_min'] = df.groupby('route_id')['delay_min'].transform(
        lambda x: x.fillna(x.median())
    )
    df['delay_min'] = df['delay_min'].fillna(df['delay_min'].median())
    df['zone'] = df['zone'].str.strip().str.title()

    df['peak_load'] = pd.cut(
        df['passengers'],
        bins=[-np.inf, 1500, 3500, np.inf],
        labels=['Low', 'Medium', 'High']
    )
    df['day_of_week'] = df['date'].dt.day_name()
    return df

raw_df = generate_data()
df = clean_data(raw_df)

st.header("1. Sample Input (Raw Data)")
st.markdown("This is the raw dataset with injected noise and missing values.")
st.write(raw_df.head(10))

st.header("2. Cleaned Data Overview")
st.markdown("This is the dataset after completing the ETL process (handling missing values, standardizing strings, capping outliers).")
st.write(df.head(10))

st.header("3. Route Efficiency Ranking")
def merge_sort(data, key_index):
    if len(data) <= 1: return data
    mid = len(data) // 2
    left = merge_sort(data[:mid], key_index)
    right = merge_sort(data[mid:], key_index)
    return merge(left, right, key_index)

def merge(left, right, key_index):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i][key_index] >= right[j][key_index]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

route_stats = df.groupby('route_id').agg(
    avg_passengers=('passengers', 'mean'),
    avg_delay=('delay_min', 'mean')
).reset_index()

route_list = []
for _, row in route_stats.iterrows():
    route_list.append((row['route_id'], row['avg_passengers'], row['avg_delay']))

efficiency_list = []
for route, avg_passengers, avg_delay in route_list:
    efficiency_score = avg_passengers / (1 + avg_delay)
    efficiency_list.append((route, avg_passengers, avg_delay, efficiency_score))

rank_by_efficiency = merge_sort(efficiency_list, 3)
efficiency_df = pd.DataFrame(rank_by_efficiency, columns=["Route", "Avg Passengers", "Avg Delay", "Efficiency Score"])

col1, col2 = st.columns(2)
with col1:
    st.subheader("Top 5 Routes by Efficiency")
    st.dataframe(efficiency_df.head())
with col2:
    st.subheader("Bottom 5 Routes by Efficiency")
    st.dataframe(efficiency_df.tail())

st.header("4. Statistical Visualization")
fig = plt.figure(figsize=(16, 12))

# Panel 1
plt.subplot(2, 2, 1)
daily = df.groupby('date')['passengers'].sum()
rolling = daily.rolling(7).mean()
plt.plot(daily.index, daily.values, label='Daily Total Passengers')
plt.plot(rolling.index, rolling.values, label='7-Day Rolling Mean')
plt.title('Daily Total Passengers Over Time')
plt.xlabel('Date')
plt.ylabel('Passengers')
plt.legend()

# Panel 2
plt.subplot(2, 2, 2)
zone_peak = df.groupby(['zone', 'peak_load'], observed=True)['passengers'].mean().unstack()
zone_peak.plot(kind='bar', ax=plt.gca())
plt.title('Average Passengers by Zone and Peak Load')
plt.xlabel('Zone')
plt.ylabel('Average Passengers')
plt.legend(title='Peak Load')

# Panel 3
plt.subplot(2, 2, 3)
delays = df['delay_min'].values
mean_delay = np.mean(delays)
std_delay = np.std(delays)
count, bins, ignored = plt.hist(delays, bins=15, density=True, alpha=0.6)
normal_curve = (1 / (std_delay * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((bins - mean_delay) / std_delay) ** 2)
plt.plot(bins, normal_curve, label='Normal Curve')
plt.title('Delay Distribution')
plt.xlabel('Delay in Minutes')
plt.ylabel('Density')
plt.legend()

# Panel 4
plt.subplot(2, 2, 4)
route_zone = df.groupby('route_id')['zone'].agg(lambda x: pd.Series.mode(x)[0]).reset_index()
route_plot = route_stats.merge(route_zone, on='route_id')
zones = route_plot['zone'].unique()
for z in zones:
    temp = route_plot[route_plot['zone'] == z]
    plt.scatter(temp['avg_passengers'], temp['avg_delay'], label=z)

top10 = route_plot.sort_values('avg_passengers', ascending=False).head(10)
for _, row in top10.iterrows():
    plt.text(row['avg_passengers'], row['avg_delay'], row['route_id'])

plt.title('Average Passengers vs Average Delay Per Route')
plt.xlabel('Average Passengers')
plt.ylabel('Average Delay in Minutes')
plt.legend()
plt.tight_layout()

st.pyplot(fig)

st.header("5. Interactive Zone Map")

ZONE_COORDS = {
    'North': [28.8000, 77.2090],
    'South': [28.4595, 77.0266],
    'East': [28.6139, 77.3910],
    'West': [28.6139, 77.0270],
    'Central': [28.6139, 77.2090],
}

m = folium.Map(location=[28.6139, 77.2090], zoom_start=11)
zone_stats = df.groupby('zone').agg(
    zone_avg_passengers=('passengers', 'mean'),
    zone_avg_delay=('delay_min', 'mean'),
    dominant_peak_load=('peak_load', lambda x: pd.Series.mode(x)[0])
).reset_index()

for _, row in zone_stats.iterrows():
    z = row['zone']
    avg_passengers = row['zone_avg_passengers']
    avg_delay = row['zone_avg_delay']
    dominant_peak = row['dominant_peak_load']

    if avg_passengers < 2000:
        color = 'green'
    elif avg_passengers <= 3500:
        color = 'orange'
    else:
        color = 'red'

    popup_text = f"<b>Zone:</b> {z}<br><b>Avg Passengers:</b> {avg_passengers:.2f}<br><b>Avg Delay:</b> {avg_delay:.2f} min<br><b>Dominant Peak Load:</b> {dominant_peak}"

    folium.CircleMarker(
        location=ZONE_COORDS[z],
        radius=avg_passengers / 200,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.6,
        popup=folium.Popup(popup_text, max_width=300)
    ).add_to(m)

heat_data = []
for _, row in df.iterrows():
    base_lat, base_lon = ZONE_COORDS[row['zone']]
    jitter_lat = base_lat + np.random.uniform(-0.02, 0.02)
    jitter_lon = base_lon + np.random.uniform(-0.02, 0.02)
    heat_data.append([jitter_lat, jitter_lon, row['passengers']])

HeatMap(heat_data).add_to(m)

st_folium(m, width=1000, height=600)
