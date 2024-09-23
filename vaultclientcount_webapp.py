#!/usr/bin/env python3

import pandas as pd
import json
from dash import Dash, html, dcc, callback_context
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
import numpy as np

# Initialize the Dash app
app = Dash(__name__)

app.layout = html.Div([
    html.Link(href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap", rel="stylesheet"),
    html.H1("Snapshot Data Dashboard"),
    html.H4("This app requires a JSON data payload."),
    html.H4([
        "Follow these steps to retrieve the necessary payload: ", 
        html.A("Manual license utilization reporting", href="https://developer.hashicorp.com/vault/docs/enterprise/license/manual-reporting", target="_blank")
    ]),

    dcc.Upload(
        id='upload-data',
        children=html.Div([html.H3([('Drag and Drop or '), html.A('Select a JSON File')])]),
        className='upload-div',
        multiple=False
    ),

    html.Div([
        html.Label('Specify the additional number of months to estimate trendline:'),
        dcc.Input(id='num-months', type='number', value=0, min=0, placeholder='Additional Months')
    ]),

    html.Div(id='output-file-upload'),
    dcc.Graph(id='output-graph')

])

# Helper function to parse the uploaded JSON data
def parse_json(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    return json.loads(decoded.decode('utf-8'))

# Helper function to process the data and generate a plot
def process_and_plot(json_data, num_months):
    snapshots = json_data.get("snapshots", [])
    
    # Convert snapshots to DataFrame
    df = pd.DataFrame(snapshots)
    
    # Convert 'timestamp' to datetime and handle errors
    df['timestamp'] = pd.to_datetime(df['timestamp'].str.slice(0, 26), errors='coerce')
    df = df.dropna(subset=['timestamp'])
    
    if pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['year_month'] = df['timestamp'].dt.to_period('M').astype(str)
        latest_records = df.loc[df.groupby('year_month')['timestamp'].idxmax()]
        
        output = []
        for _, row in latest_records.iterrows():
            metrics = row['metrics']
            output.append({
                "year_month": str(row['year_month']),
                "current_month_estimate_entity": metrics["clientcount.current_month_estimate.type.entity"]["value"],
                "current_month_estimate_nonentity": metrics["clientcount.current_month_estimate.type.nonentity"]["value"],
                "current_month_estimate_secret_sync": metrics["clientcount.current_month_estimate.type.secret_sync"]["value"],
                "previous_month_complete_entity": metrics["clientcount.previous_month_complete.type.entity"]["value"],
                "previous_month_complete_nonentity": metrics["clientcount.previous_month_complete.type.nonentity"]["value"],
                "previous_month_complete_secret_sync": metrics["clientcount.previous_month_complete.type.secret_sync"]["value"]
            })
        
        # Convert to DataFrame
        output_df = pd.DataFrame(output)

        # Create Plotly figure with subplots
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=("Entity Estimate", "Non-Entity Estimate", "Secret Sync Estimate", 
                            "Previous Month Entity", "Previous Month Non-Entity", "Previous Month Secret Sync")
        )

        # Add titles for the rows
        fig.add_annotation(
            text="Current Month Estimates",
            xref="paper", yref="paper",
            x=0.5, y=1.15,  # Adjust y for vertical spacing
            showarrow=False,
            font=dict(size=22, weight='bold')
        )

        fig.add_annotation(
            text="Previous Month Estimates",
            xref="paper", yref="paper",
            x=0.5, y=0.5,  # Adjust y for vertical spacing
            showarrow=False,
            font=dict(size=22, weight='bold')
        )

        # Function to add trendline and projections
        def add_trendline(fig, x, y, row, col):
            x_numeric = np.arange(len(y))
            z = np.polyfit(x_numeric, y, 2)
            p = np.poly1d(z)
            trendline = p(x_numeric)

            # Future projections based on user input
            future_x = np.arange(len(y), len(y) + num_months)  # Use num_months here
            future_y = p(future_x)
            all_x = np.concatenate((x_numeric, future_x))
            all_y = np.concatenate((trendline, future_y))

            # Create a date range for the x-axis
            future_dates = pd.date_range(start=pd.to_datetime(output_df['year_month'].min() + '-01'), 
                                          periods=len(all_x), freq='ME')
            
            # Add trendline and projections to the plot
            fig.add_trace(go.Scatter(
                x=future_dates, 
                y=all_y, 
                mode='lines', 
                name='Trendline & Projection', 
                line=dict(color='red', dash='dash')
            ), row=row, col=col)

        # Add plots to the subplots and trendlines
        fig.add_trace(go.Bar(x=output_df['year_month'], y=output_df['current_month_estimate_entity'], name="Entity Estimate"), row=1, col=1)
        add_trendline(fig, np.arange(len(output_df['current_month_estimate_entity'])), output_df['current_month_estimate_entity'], 1, 1)

        fig.add_trace(go.Bar(x=output_df['year_month'], y=output_df['current_month_estimate_nonentity'], name="Non-Entity Estimate"), row=1, col=2)
        fig.add_trace(go.Bar(x=output_df['year_month'], y=output_df['current_month_estimate_secret_sync'], name="Secret Sync Estimate"), row=1, col=3)
        
        fig.add_trace(go.Bar(x=output_df['year_month'], y=output_df['previous_month_complete_entity'], name="Previous Month Entity"), row=2, col=1)
        add_trendline(fig, np.arange(len(output_df['previous_month_complete_entity'])), output_df['previous_month_complete_entity'], 2, 1)

        fig.add_trace(go.Bar(x=output_df['year_month'], y=output_df['previous_month_complete_nonentity'], name="Previous Month Non-Entity"), row=2, col=2)
        fig.add_trace(go.Bar(x=output_df['year_month'], y=output_df['previous_month_complete_secret_sync'], name="Previous Month Secret Sync"), row=2, col=3)

        # Update layout
        fig.update_layout(
            height=700,
            showlegend=False
        )

        return fig
    else:
        return None

# Combined callback function to update the graph when a file is uploaded or the number of months changes
@app.callback(
    Output('output-graph', 'figure'),
    [Input('upload-data', 'contents'),
     Input('num-months', 'value')]  # Add the input for number of additional months
)
def update_output(contents, num_months):
    if contents is not None:
        json_data = parse_json(contents)
        # Ensure num_months is valid; default to 0 if None
        num_months = num_months if num_months is not None else 0
        fig = process_and_plot(json_data, num_months)  # Pass the num_months
        return fig
    return {}

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')
