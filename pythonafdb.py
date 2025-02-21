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

    # Define continent mapping
    continent_mapping = {
        'AFR': 'Africa', 'ECS': 'Europe & Central Asia', 'LCN': 'Latin America & Caribbean',
        'MEA': 'Middle East & North Africa', 'SAS': 'South Asia', 'EAS': 'East Asia & Pacific', 'OCE': 'Oceania'
    }

    # Assign continents
    df['Continent'] = df['Region'].map(continent_mapping)

    # Fix missing continent values using country groups
    country_to_continent = {
        "United States": "North America", "Canada": "North America", "Mexico": "North America",
        "Brazil": "Latin America & Caribbean", "Argentina": "Latin America & Caribbean",
        "France": "Europe & Central Asia", "Germany": "Europe & Central Asia", "United Kingdom": "Europe & Central Asia",
        "Russia": "Europe & Central Asia", "China": "East Asia & Pacific", "Japan": "East Asia & Pacific",
        "India": "South Asia", "Pakistan": "South Asia", "South Africa": "Africa", "Nigeria": "Africa",
        "Egypt": "Middle East & North Africa", "Saudi Arabia": "Middle East & North Africa", "Australia": "Oceania"
    }

    # Assign continent based on country if not mapped before
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
