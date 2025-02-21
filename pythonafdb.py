import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

# -------------- APP CONFIGURATION --------------
st.set_page_config(
    page_title="Employment & Workforce Dashboard",
    page_icon="📊",
    layout="wide",
)

# -------------- APP TITLE --------------
st.markdown(
    "<h1 style='text-align: center; color: #4A90E2;'>📊 Employment & Workforce Analysis Dashboard</h1>",
    unsafe_allow_html=True,
)

st.markdown(
    "<h5 style='text-align: center; color: #6D6D6D;'>Interactive employment insights across different regions & years</h5>",
    unsafe_allow_html=True,
)
st.markdown("---")

# -------------- LOAD DATA --------------
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

    # Define continent mapping based on World Bank codes
    continent_mapping = {
        'AFR': 'Africa', 'ECS': 'Europe & Central Asia', 'LCN': 'Latin America & Caribbean',
        'MEA': 'Middle East & North Africa', 'SAS': 'South Asia', 'EAS': 'East Asia & Pacific', 'OCE': 'Oceania'
    }
    df['Continent'] = df['Region'].map(continent_mapping)

    # Backup mapping for missing values
    country_to_continent = {
        # Africa
        "Mali": "Africa", "Burkina Faso": "Africa", "Nigeria": "Africa", "Ghana": "Africa", "Kenya": "Africa",
        "Ethiopia": "Africa", "Tanzania": "Africa", "South Africa": "Africa", "Egypt": "Africa",
        # North America
        "United States": "North America", "Canada": "North America", "Mexico": "North America",
        # Europe
        "France": "Europe & Central Asia", "Germany": "Europe & Central Asia", "United Kingdom": "Europe & Central Asia",
        # Asia
        "China": "East Asia & Pacific", "Japan": "East Asia & Pacific", "India": "South Asia",
        # Oceania
        "Australia": "Oceania", "New Zealand": "Oceania",
    }
    df['Continent'] = df.apply(lambda row: country_to_continent.get(row['Country'], row['Continent']), axis=1)
    df['Continent'].fillna("Unknown", inplace=True)

    # Store in SQLite
    conn = sqlite3.connect("employment_data.db")
    df.to_sql("employment", conn, if_exists="replace", index=False)
    conn.close()

    return df

df = load_data()

# -------------- SIDEBAR: FILTERS --------------
st.sidebar.markdown("### 🔍 Filters")
st.sidebar.markdown("---")

# Year Selection
available_years = sorted(df["Year"].dropna().unique(), reverse=True)
selected_year = st.sidebar.selectbox("📅 Select Year", available_years, index=0)

# Display Selection
display_type = st.sidebar.radio("🌍 Select to Display", ["Countries", "Continents"])

# Country or Continent Selection
if display_type == "Countries":
    selected_countries = st.sidebar.multiselect(
        "🌎 Select Countries", df["Country"].dropna().unique(), default=df["Country"].dropna().unique()[:3]
    )
    filtered_df = df[(df["Country"].isin(selected_countries)) & (df["Year"] == selected_year)]
else:
    selected_continent = st.sidebar.multiselect(
        "🌍 Select Continent", df["Continent"].dropna().unique(), default=df["Continent"].dropna().unique()[:2]
    )
    filtered_df = df[(df["Continent"].isin(selected_continent)) & (df["Year"] == selected_year)]

st.sidebar.markdown("---")

# -------------- MAIN CONTENT --------------
col1, col2 = st.columns([1, 3])

with col1:
    st.markdown("### 📋 Filtered Data Table")
    st.dataframe(filtered_df[['Country', 'Continent', 'Year', 'Employment Rate', 'Unemployment Rate', 
                              'Labor Force Participation Rate', 'Youth Unemployment Rate']],
                 use_container_width=True, height=400)

# -------------- VISUALIZATIONS --------------
st.markdown("### 📊 Employment & Workforce Insights")
fig_box = px.box(
    filtered_df.melt(id_vars=['Country' if display_type == "Countries" else 'Continent'], 
                     value_vars=['Employment Rate', 'Unemployment Rate', 'Labor Force Participation Rate', 'Youth Unemployment Rate'],
                     var_name='Metric', value_name='Value'),
    x='Metric', y='Value', color='Country' if display_type == "Countries" else 'Continent',
    title=f'{display_type} Employment & Workforce Statistics for {selected_year}',
    template="plotly_white"
)
st.plotly_chart(fig_box, use_container_width=True)

st.markdown("### 🌍 Geographic Representation")
fig_map = px.scatter_geo(
    filtered_df, locations="Country Code", hover_name="Country" if display_type == "Countries" else "Continent",
    title=f'Selected {display_type} on the Map ({selected_year})',
    size_max=10, color='Country' if display_type == "Countries" else 'Continent',
    template="plotly_dark"
)
st.plotly_chart(fig_map, use_container_width=True)

# -------------- FOOTER --------------
st.markdown(
    "<h6 style='text-align: center; color: #6D6D6D;'>🚀 This dashboard is hosted on Streamlit and provides employment insights across different regions.</h6>",
    unsafe_allow_html=True,
)
