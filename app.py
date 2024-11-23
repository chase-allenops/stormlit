import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
import numpy as np 
import plotly.express as px

gcp_credentials = service_account.Credentials.from_service_account_file("stormlit-sa.json")

st.set_page_config(page_title='Severe Storm Events in the US', 
                   layout='wide',
                   )

# Create a "client" object
client = bigquery.Client(credentials=gcp_credentials)

# perform a query and turn it into a dataframe

@st.cache_data
def load_data():
    query = "SELECT * FROM `px-data-lab.storms.storms_agg`"
    df = client.query(query).to_dataframe()
    return df

df = load_data()

count_of_events = df['total_event_count'].sum()
max_month = pd.to_datetime(df['event_month']).max().strftime('%B %Y')
states = ["All States"] + sorted([state for state in df['state'].unique() if state is not None])

event_types = sorted([event_type for event_type in df['event_group'].unique() if event_type is not None])

st.title('Severe Storm Events in the US')
st.write('Events in dataset:', count_of_events)
st.write('Most recent month in dataset:', max_month)

df['event_year'] = pd.to_datetime(df['event_month']).dt.year
df['event_year'] = df['event_year'].astype(str)
df['event_month_name'] = pd.to_datetime(df['event_month']).dt.strftime('%B')

with st.sidebar:
    st.image('https://www.noaa.gov/themes/custom/noaa_guswds/images/noaa_digital_logo.svg', width=100)
    st.write('Data Source: NOAA Storm Events Database')
    state_selection = st.selectbox('Select State', states, placeholder='All States')
    event_type_selection = st.multiselect('Select Event Type', event_types)

# filter the dataframe based on the selected state and event type
filtered_df = df.copy()
if state_selection != 'All States':
    filtered_df = filtered_df[filtered_df['state'] == state_selection]
if event_type_selection:
    filtered_df = filtered_df[filtered_df['event_group'].isin(event_type_selection)]


# events by year chart
events_by_year = filtered_df.groupby('event_year')['total_event_count'].sum().reset_index()
events_by_year_fig = px.line(events_by_year, x='event_year', y='total_event_count', 
                             title='Severe Storm Events by Year', 
                             labels={'event_year': '', 'total_event_count': 'Total Events'})
st.plotly_chart(events_by_year_fig)

# deaths by year chart
deaths_by_year = filtered_df.groupby('event_year')['sum_deaths_direct'].sum().reset_index()
deaths_by_year_fig = px.line(deaths_by_year, x='event_year', y='sum_deaths_direct', title='Deaths by Year', labels={'event_year': '', 'sum_deaths_direct': 'Total Deaths'})
st.plotly_chart(deaths_by_year_fig)

# damage by year chart
damages_by_year = filtered_df.groupby('event_year').agg({
    'sum_damage_crops': 'sum',
    'sum_damage_property': 'sum'
}).reset_index()
damages_by_year_fig = px.line(damages_by_year, x='event_year', y=['sum_damage_crops', 'sum_damage_property'], title='Damage by Year', labels={'event_year': '', 'value': 'Total Damage', 'variable': 'Type', 'sum_damage_crops': 'Crops', 'sum_damage_property': 'Property'})
damage_source_naming = {
    'sum_damage_crops': 'Crops',
    'sum_damage_property': 'Property'
}
damages_by_year_fig.for_each_trace(lambda t: t.update(name=damage_source_naming[t.name]))
st.plotly_chart(damages_by_year_fig)

# create a slider to select years and filter the dataframe by the selected year
selected_year = st.slider('Select Year', min_value=1950, max_value=2024)
filtered_df = filtered_df[filtered_df['event_year'] == str(selected_year)]


# events by month in the selected year
events_by_year = filtered_df.groupby('event_month')['total_event_count'].sum().reset_index()
monthly_events_fig = px.line(events_by_year, x='event_month', y='total_event_count', title=f'Severe Storm Events by Month in {selected_year}', text='total_event_count', labels={'event_month': '', 'total_event_count': 'Total Events'})
monthly_events_fig.update_traces(textposition='top center')
st.plotly_chart(monthly_events_fig)




