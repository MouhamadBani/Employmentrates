import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

# Title
st.title("📊 Employment & Workforce Analysis Dashboard")

# Load Data and Store in SQLite Database
@st.cache_data
def load_data():
    file_path = "FIdataWB.xlsx"
    df = pd.read_excel(file_path, sheet_name='Sheet1', skiprows=3)

    # Rename essential columns
    df.rename(columns={
        'Country Name': 'Country',
        'Country Code': 'Country Code',
        'Income Level Name': 'Income Level',
        'Year of survey': 'Year',
        'Employment to Population Ratio, aged 15-64': 'Employment Rate',
        'Unemployment Rate, aged 15-64': 'Unemployment Rate',
        'Labor Force Participation Rate, aged 15-64': 'Labor Force Participation Rate',
        'Youth Unemployment Rate, aged 15-24': 'Youth Unemployment Rate',
        'Region Code': 'Region'
    }, inplace=True)

    # Convert numeric columns
    num_cols = ['Employment Rate', 'Unemployment Rate', 'Labor Force Participation Rate', 'Youth Unemployment Rate']
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors='coerce')

    # **Step 1: Assign Continent Based on World Bank Region Code**
    continent_mapping = {
        'AFR': 'Africa', 'ECS': 'Europe & Central Asia', 'LCN': 'Latin America & Caribbean',
        'MEA': 'Middle East & North Africa', 'SAS': 'South Asia', 'EAS': 'East Asia & Pacific', 'OCE': 'Oceania'
    }
    df['Continent'] = df['Region'].map(continent_mapping)

    # **Step 2: Assign Continent Based on Country (for missing cases)**
    country_to_continent = {
        # **Africa**
        "Mali": "Africa", "Burkina Faso": "Africa", "Nigeria": "Africa", "Ghana": "Africa", "Kenya": "Africa",
        "Ethiopia": "Africa", "Tanzania": "Africa", "South Africa": "Africa", "Egypt": "Africa", "Algeria": "Africa",
        "Morocco": "Africa", "Uganda": "Africa", "Rwanda": "Africa", "Senegal": "Africa", "Zambia": "Africa",
        "Cameroon": "Africa", "Niger": "Africa", "Chad": "Africa", "Sudan": "Africa", "Tunisia": "Africa",
        "Democratic Republic of the Congo": "Africa", "Republic of the Congo": "Africa", "Angola": "Africa",

        # **North America**
        "United States": "North America", "Canada": "North America", "Mexico": "North America",

        # **Latin America & Caribbean**
        "Brazil": "Latin America & Caribbean", "Argentina": "Latin America & Caribbean", "Colombia": "Latin America & Caribbean",
        "Chile": "Latin America & Caribbean", "Peru": "Latin America & Caribbean", "Venezuela": "Latin America & Caribbean",

        # **Europe & Central Asia**
        "France": "Europe & Central Asia", "Germany": "Europe & Central Asia", "United Kingdom": "Europe & Central Asia",
        "Russia": "Europe & Central Asia", "Spain": "Europe & Central Asia", "Italy": "Europe & Central Asia",
        "Ukraine": "Europe & Central Asia", "Netherlands": "Europe & Central Asia", "Poland": "Europe & Central Asia",

        # **East Asia & Pacific**
        "China": "East Asia & Pacific", "Japan": "East Asia & Pacific", "South Korea": "East Asia & Pacific",
        "Philippines": "East Asia & Pacific", "Indonesia": "East Asia & Pacific", "Thailand": "East Asia & Pacific",
        "Vietnam": "East Asia & Pacific", "Malaysia": "East Asia & Pacific", "New Zealand": "East Asia & Pacific",

        # **South Asia**
        "India": "South Asia", "Pakistan": "South Asia", "Bangladesh": "South Asia", "Sri Lanka": "South Asia",
        "Nepal": "South Asia", "Bhutan": "South Asia",

        # **Middle East & North Africa**
        "Saudi Arabia": "Middle East & North Africa", "United Arab Emirates": "Middle East & North Africa",
        "Qatar": "Middle East & North Africa", "Kuwait": "Middle East & North Africa", "Iran": "Middle East & North Africa",

        # **Oceania**
        "Australia": "Oceania", "New Zealand": "Oceania", "Fiji": "Oceania", "Papua New Guinea": "Oceania"
    }

    # Assign missing continent values based on country mapping
    df['Continent'] = df.apply(lambda row: country_to_continent.get(row['Country'], row['Continent']), axis=1)

    # Ensure no missing continent values
    df['Continent'].fillna("Unknown", inplace=True)

    # Store data in SQLite database
    conn = sqlite3.connect("employment_data.db")
    df.to_sql("employment", conn, if_exists="replace", index=False)
    conn.close()

    return df

df = load_data()

# Sidebar: Filters
st.sidebar.header("🔍 Filters")

# **Year Selection**
available_years = sorted(df["Year"].dropna().unique(), reverse=True)
selected_year = st.sidebar.selectbox("Select Year", available_years, index=0)

# **Display Selection: Countries or Continents**
display_type = st.sidebar.radio("Select to display:", ["Countries", "Continents"])

if display_type == "Countries":
    selected_countries = st.sidebar.multiselect(
        "Select up to 3 Countries", 
        df["Country"].dropna().unique(), 
        default=df["Country"].dropna().unique()[:3]
    )
    filtered_df = df[(df["Country"].isin(selected_countries)) & (df["Year"] == selected_year)]
else:
    selected_continent = st.sidebar.multiselect(
        "Select Continent", 
        df["Continent"].dropna().unique(), 
        default=df["Continent"].dropna().unique()[:2]
    )
    filtered_df = df[(df["Continent"].isin(selected_continent)) & (df["Year"] == selected_year)]

# Display Data Table
st.subheader("📋 Selected Data Table")
st.dataframe(filtered_df[['Country', 'Continent', 'Year', 'Employment Rate', 'Unemployment Rate', 
                          'Labor Force Participation Rate', 'Youth Unemployment Rate']])

# Boxplot Visualization
st.subheader("📊 Employment & Workforce Insights")
fig_box = px.box(
    filtered_df.melt(id_vars=['Country' if display_type == "Countries" else 'Continent'], 
                     value_vars=['Employment Rate', 'Unemployment Rate', 'Labor Force Participation Rate', 'Youth Unemployment Rate'],
                     var_name='Metric', value_name='Value'),
    x='Metric', y='Value', color='Country' if display_type == "Countries" else 'Continent',
    title=f'{display_type} Employment & Workforce Statistics for {selected_year}'
)
st.plotly_chart(fig_box)

# World Map Visualization
st.subheader("🌍 Global Representation")
fig_map = px.scatter_geo(
    filtered_df, locations="Country Code", hover_name="Country" if display_type == "Countries" else "Continent",
    title=f'Selected {display_type} on the Map ({selected_year})',
    size_max=10, color='Country' if display_type == "Countries" else 'Continent'
)
st.plotly_chart(fig_map)

# Deployment Note
st.markdown("🚀 **This dashboard is hosted on Streamlit and provides employment insights across different regions.**")
