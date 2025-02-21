import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import sqlite3

# Load Data and Store in SQLite Database
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
    'Youth Unemployment Rate, aged 15-24': 'Youth Unemployment Rate'
}, inplace=True)

# Convert numeric columns
df[['Employment Rate', 'Unemployment Rate', 'Labor Force Participation Rate', 'Youth Unemployment Rate']] = \
    df[['Employment Rate', 'Unemployment Rate', 'Labor Force Participation Rate', 'Youth Unemployment Rate']].apply(pd.to_numeric, errors='coerce')

# Define continent mapping
continent_mapping = {
    'AFR': 'Africa', 'ECS': 'Europe', 'LCN': 'America', 'MEA': 'Middle East', 'SAS': 'Asia', 'EAS': 'Asia', 'OCE': 'Oceania'
}
df['Continent'] = df['Region Code'].map(continent_mapping)

# Ensure all continents are represented
available_continents = list(continent_mapping.values())
existing_continents = df['Continent'].dropna().unique()
missing_continents = [c for c in available_continents if c not in existing_continents]
for continent in missing_continents:
    df = pd.concat([df, pd.DataFrame({'Continent': [continent], 'Country': ['N/A']})], ignore_index=True)

# Store data in SQLite database
conn = sqlite3.connect("employment_data.db")
df.to_sql("employment", conn, if_exists="replace", index=False)

# Dash app setup
app = dash.Dash(__name__, external_stylesheets=["https://cdnjs.cloudflare.com/ajax/libs/bootswatch/5.1.3/lux/bootstrap.min.css"])
app.layout = html.Div([
    html.H1("Employment & Workforce Analysis Dashboard", className='text-center text-white bg-dark py-4 rounded'),
    
    html.Div([
        html.Label("Select to display:", className='font-weight-bold'),
        dcc.RadioItems(
            id='display-selector',
            options=[
                {'label': 'Countries', 'value': 'countries'},
                {'label': 'Continents', 'value': 'continents'}
            ],
            value='countries',
            inline=True,
            className='mb-3'
        )
    ], className='text-center bg-light p-3 rounded shadow-sm'),
    
    html.Div(id='selection-container', className='mb-3 p-3 rounded shadow-sm bg-white'),
    html.Button("Submit", id='submit-button', className='btn btn-success mt-3 btn-lg d-block mx-auto'),
    
    html.Div(id='table-container', className='p-3 bg-white shadow rounded mt-4'),
    
    html.Div([
        html.H4("Data Insights", className='text-center text-info mt-4 mb-3'),
        dcc.Graph(id='boxplot-graph', className='shadow p-3 bg-light rounded'),
        dcc.Graph(id='map-graph', className='shadow p-3 bg-light rounded')
    ])
])

@app.callback(
    Output('selection-container', 'children'),
    Input('display-selector', 'value')
)
def update_selection(display_type):
    if display_type == 'countries':
        return html.Div([
            html.Label("Select up to 3 Countries:", className='font-weight-bold'),
            dcc.Dropdown(
                id='selection',
                options=[{'label': c, 'value': c} for c in df['Country'].dropna().unique()],
                multi=True
            )
        ], className='col-md-6 mx-auto')
    else:
        return html.Div([
            html.Label("Select Continent:", className='font-weight-bold'),
            dcc.Dropdown(
                id='selection',
                options=[{'label': c, 'value': c} for c in available_continents],
                multi=True
            )
        ], className='col-md-6 mx-auto')

@app.callback(
    [Output('table-container', 'children'), Output('boxplot-graph', 'figure'), Output('map-graph', 'figure')],
    [Input('submit-button', 'n_clicks')],
    [State('display-selector', 'value'), State('selection', 'value')]
)
def display_data(n_clicks, display_type, selected):
    if not n_clicks or not selected:
        return html.Div("Select at least one option and submit.", className='text-danger font-weight-bold'), px.Figure(), px.Figure()
    
    data_df = df[df['Country'].isin(selected)] if display_type == 'countries' else df[df['Continent'].isin(selected)]
    important_vars = ['Employment Rate', 'Unemployment Rate', 'Labor Force Participation Rate', 'Youth Unemployment Rate']
    
    table = dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in ['Country', 'Continent', 'Year'] + important_vars],
        data=data_df.to_dict('records'),
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '10px', 'fontSize': '14px'},
        style_header={'backgroundColor': 'black', 'color': 'white', 'fontWeight': 'bold'}
    )
    
    fig_box = px.box(data_df.melt(id_vars=['Country' if display_type == 'countries' else 'Continent'], 
                                  value_vars=important_vars,
                                  var_name='Metric', value_name='Value'),
                      x='Metric', y='Value', color='Country' if display_type == 'countries' else 'Continent',
                      title=f'{display_type.capitalize()}-Level Boxplots', 
                      template='plotly_dark')
    
    fig_map = px.scatter_geo(
        data_df, locations='Country Code', hover_name='Country' if display_type == 'countries' else 'Continent',
        title=f'Selected {display_type.capitalize()} on the Map', 
        template='plotly_dark', color='Country' if display_type == 'countries' else 'Continent', size_max=10
    )
    
    return table, fig_box, fig_map

if __name__ == '__main__':
    app.run_server(debug=True)
