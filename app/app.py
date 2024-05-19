import pandas as pd
import streamlit as st
import numpy as np
import plotly.express as px

# Set page configuration to wide mode
st.set_page_config(layout="wide")

# Helper function to convert population strings to numeric values
def convert_population(pop):
    if isinstance(pop, str):
        pop = pop.strip()
        if 'k' in pop:
            return float(pop.replace('k', '').replace(',', '').replace(' ', '')) * 1e3
        elif 'M' in pop:
            return float(pop.replace('M', '').replace(',', '').replace(' ', '')) * 1e6
        elif 'B' in pop:
            return float(pop.replace('B', '').replace(',', '').replace(' ', '')) * 1e9
    return float(pop)

@st.cache_data
def load_and_preprocess_data():
    # File paths (since the files are in the same directory as app.py)
    life_expectancy_path = 'lex.csv'  # Ensure this is the correct filename
    population_path = 'pop.csv'  # Ensure this is the correct filename
    gni_per_capita_path = 'ny_gnp_pcap_pp_cd.csv'  # Ensure this is the correct filename
    
    # Load the CSV files
    life_expectancy_df = pd.read_csv(life_expectancy_path)
    population_df = pd.read_csv(population_path)
    gni_per_capita_df = pd.read_csv(gni_per_capita_path)

    # Fill missing values using forward filling
    life_expectancy_df.ffill(inplace=True)
    population_df.ffill(inplace=True)
    gni_per_capita_df.ffill(inplace=True)

    # Transform each dataframe into tidy data format
    life_expectancy_tidy = life_expectancy_df.melt(id_vars=["country"], var_name="year", value_name="life_expectancy")
    population_tidy = population_df.melt(id_vars=["country"], var_name="year", value_name="population")
    gni_per_capita_tidy = gni_per_capita_df.melt(id_vars=["country"], var_name="year", value_name="gni_per_capita")

    # Convert gni_per_capita to numeric, forcing errors to NaN
    gni_per_capita_tidy['gni_per_capita'] = pd.to_numeric(gni_per_capita_tidy['gni_per_capita'], errors='coerce')
    
    # Convert population to numeric values
    population_tidy['population'] = population_tidy['population'].apply(convert_population)

    # Merge the dataframes on country and year
    merged_df = life_expectancy_tidy.merge(population_tidy, on=["country", "year"]).merge(gni_per_capita_tidy, on=["country", "year"])

    return merged_df

# Load and preprocess the data
merged_df = load_and_preprocess_data()

if merged_df is not None:
    # Convert 'year' column to integer type for slider
    merged_df['year'] = merged_df['year'].astype(int)

    # Add a year slider
    st.sidebar.write("### Select Year")
    year = st.sidebar.slider("Year", int(merged_df['year'].min()), int(merged_df['year'].max()), int(merged_df['year'].min()))

    # Add a multi-select for countries
    st.sidebar.write("### Select Country/Countries")
    countries = st.sidebar.multiselect("Country", merged_df['country'].unique(), merged_df['country'].unique())

    # Filter the dataframe based on user selection
    filtered_df = merged_df[(merged_df['year'] == year) & (merged_df['country'].isin(countries))]

    # Ensure no NaN values in gni_per_capita and population for the log transformation and sizing
    filtered_df = filtered_df.dropna(subset=['gni_per_capita', 'population'])

    # Create the bubble chart
    fig = px.scatter(
        filtered_df,
        x=np.log(filtered_df['gni_per_capita']),
        y='life_expectancy',
        size='population',
        color='country',
        hover_name='country',
        size_max=60,
        labels={'x': 'Log of GNI per Capita', 'y': 'Life Expectancy'},
        title=f'Bubble Chart for Year {year}',
        width=1200,  # Increase chart width
        height=800   # Increase chart height
    )

    # Set the x-axis range to keep it constant
    fig.update_layout(xaxis=dict(range=[np.log(merged_df['gni_per_capita'].min()), np.log(merged_df['gni_per_capita'].max())]))

    # Display the bubble chart
    st.plotly_chart(fig)
else:
    st.write("Data could not be loaded. Please check the error message above.")
