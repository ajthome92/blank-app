import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import plotly.colors as pc

st.title("🎈 My new app")
st.write(
    "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)


# Load your actual dataframe
df = pd.read_excel("/Users/anthony.thome/OneDrive - ERM/WSm Folder/Suja Audit/Suja Audit Data.xlsx")

# Function to calculate topic volume percentages for each company
def calculate_top_categories(df, top_n=10):
    # Group by company and category to count the occurrences
    topic_volume = df.groupby(['Company', 'Category']).size().reset_index(name='Counts')

    # Calculate the percentage of each category occurrence by company
    total_counts = topic_volume.groupby('Company')['Counts'].sum().reset_index()
    topic_volume = pd.merge(topic_volume, total_counts, on='Company', suffixes=('', '_total'))
    topic_volume['Percentage'] = (topic_volume['Counts'] / topic_volume['Counts_total']) * 100

    # Average the percentages across companies for each category
    avg_category_percentage = topic_volume.groupby('Category')['Percentage'].mean().reset_index()

    # Get the top N categories
    top_categories = avg_category_percentage.nlargest(top_n, 'Percentage')['Category'].tolist()

    # Filter the original data for these top categories
    filtered_data = topic_volume[topic_volume['Category'].isin(top_categories)]
    
    return filtered_data, top_categories

# Prepare the radar chart data with dynamic scaling and transparent fill, and no scale display
def create_radar_chart(df, top_categories):
    radar_data = []
    max_value = 0  # Keep track of the maximum percentage to adjust the scale dynamically

    # Pivot the data for radar chart plotting
    for company in df['Company'].unique():
        company_data = df[df['Company'] == company]

        # Get the max percentage for this company
        company_max = company_data['Percentage'].max()
        if company_max > max_value:
            max_value = company_max  # Update max_value if the current company's max is higher
        
        # Close the radar chart by adding the first point to the end
        r_values = company_data['Percentage'].tolist()
        theta_values = company_data['Category'].tolist()
        
        # Append the first value at the end to close the loop
        if len(r_values) > 0:
            r_values.append(r_values[0])
            theta_values.append(theta_values[0])
        
        radar_data.append(go.Scatterpolar(
            r=r_values,
            theta=theta_values,
            fill='toself',
            fillcolor='rgba(0,0,0,0)',  # Make the fill transparent
            line=dict(width=2),  # Keep the line colored
            name=company
        ))
    
    # Create radar chart with dynamic max value based on the highest category percentage
    fig = go.Figure(data=radar_data)
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, max_value], showticklabels=False),  # Hide the scale
            angularaxis=dict(showticklabels=True),  # Keep the category labels visible
        ),
        showlegend=True,
        title='Topic Volume by Company'
    )
    
    return fig

# Create clustered bar chart to show category percentages for each company
def create_clustered_bar_chart(df):
    # Group by company and category, and calculate category percentage for each company
    category_counts = df.groupby(['Company', 'Category']).size().reset_index(name='Counts')
    total_counts = category_counts.groupby('Company')['Counts'].sum().reset_index()
    
    # Merge to calculate the percentage of each category for each company
    merged_data = pd.merge(category_counts, total_counts, on='Company', suffixes=('', '_total'))
    merged_data['Percentage'] = (merged_data['Counts'] / merged_data['Counts_total']) * 100

    # Create the clustered bar chart
    fig = px.bar(
        merged_data,
        x='Company',
        y='Percentage',
        color='Category',
        barmode='group',
        title="Category Percentage Distribution per Company",
        labels={'Percentage': 'Category Percentage (%)'},
    )
    
    return fig

# Horizontal bar chart
def create_horizontal_bar_chart(df, selected_categories):
    data = []

    # Generate a color map to assign consistent colors per company
    company_colors = {}
    unique_companies = df['Company'].unique()
    colors = pc.qualitative.Plotly  # Use Plotly's qualitative color scale
    for idx, company in enumerate(unique_companies):
        company_colors[company] = colors[idx % len(colors)]

    first_category = True  # Flag to control legend display for only the first category

    if selected_categories and len(selected_categories) > 0:
        for category in selected_categories:
            category_df = df[df['Category'] == category]
            max_scores = category_df.groupby('Company')['Score'].max().reset_index()

            # Ensure every company has an entry, assign 0 if no score exists
            all_companies = pd.DataFrame(unique_companies, columns=['Company'])
            max_scores = pd.merge(all_companies, max_scores, on='Company', how='left').fillna(0)

            # Offset overlapping points slightly if there are companies with the same score
            score_counts = max_scores['Score'].value_counts()
            offsets = {}
            for score, count in score_counts.items():
                if count > 1:
                    offsets[score] = np.linspace(-0.01, 0.01, count)
                else:
                    offsets[score] = [0]

            for idx, row in max_scores.iterrows():
                score = row['Score']
                offset = offsets.get(score, [0])[idx % len(offsets.get(score, [0]))]

                data.append(go.Scatter(
                    x=[score + offset],
                    y=[category],
                    mode='markers',
                    marker=dict(size=12, color=company_colors[row['Company']]),
                    name=row['Company'],
                    showlegend=first_category
                ))

            first_category = False

        fig = go.Figure(data=data)
        fig.update_layout(
            xaxis=dict(range=[-0.1, 3.1], title='Max Score', dtick=1.0),
            yaxis=dict(title='Category'),
            title="Company Max Scores by Category"
        )
    else:
        fig = go.Figure()
        fig.update_layout(
            title="No Categories Selected",
            xaxis=dict(range=[-0.1, 3.1], title='Max Score', dtick=1),
            yaxis=dict(title='Category'),
        )

    return fig

# Streamlit app setup
st.title("Document Data Dashboard")

# Filter widgets
selected_companies = st.multiselect('Filter by Company:', df['Company'].unique())
selected_categories = st.multiselect('Filter by Category:', df['Category'].unique())
selected_keywords = st.multiselect('Filter by Search Keywords:', df['Search_Keywords'].unique())

# Filter the dataframe based on selections
filtered_df = df.copy()
if selected_companies:
    filtered_df = filtered_df[filtered_df['Company'].isin(selected_companies)]
if selected_categories:
    filtered_df = filtered_df[filtered_df['Category'].isin(selected_categories)]
if selected_keywords:
    filtered_df = filtered_df[filtered_df['Search_Keywords'].isin(selected_keywords)]

# Clustered bar chart
st.plotly_chart(create_clustered_bar_chart(filtered_df))

# Radar chart
radar_data, top_categories = calculate_top_categories(filtered_df)
st.plotly_chart(create_radar_chart(radar_data, top_categories))

# Horizontal bar chart
st.plotly_chart(create_horizontal_bar_chart(filtered_df, selected_categories))

# Display filtered data as a table
st.write(filtered_df)
