#!/usr/bin/env python3

import pandas as pd
import json
from dash import Dash, html, dcc, callback_context, dash_table
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
import numpy as np

# Initialize the Dash app
app = Dash(__name__)

app.layout = html.Div([
    html.Link(href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap", rel="stylesheet"),
    html.H1("Vault Manual License Utilisation Dashboard"),
    html.H4("This app requires a JSON data payload."),
    html.H4([
        "Follow these steps to retrieve the necessary payload: ", 
        html.A("Manual license utilization reporting", href="https://developer.hashicorp.com/vault/docs/enterprise/license/manual-reporting", target="_blank")
    ]),

    # Upload JSON section
    dcc.Upload(
        id='upload-data',
        children=html.Div([html.H3([('Drag and Drop or '), html.A('Select a JSON File')])]),
        className='upload-div',
        multiple=False
    ),

    # Input section for trendline options
    html.Div(
        className="input-section",
        children=[
            html.Label('Specify the additional number of months to estimate trendline:'),
            dcc.Input(id='num-months', type='number', value=0, min=0),

            html.Label('Select trendline type (polynomial degree):'),
            dcc.Dropdown(
                id='trendline-degree',
                options=[
                    {'label': 'Linear', 'value': 1},
                    {'label': 'Quadratic', 'value': 2},
                    {'label': 'Cubic', 'value': 3},
                    {'label': 'Quartic', 'value': 4}
                ],
                value=2,  # Default to quadratic
                clearable=False,
                className='dropdown'
            ),

            html.Div(
                className="checklist",
                children=[
                    html.Label("Show Trendline"),
                    dcc.Checklist(
                        id='show-trendline',
                        options=[{'label': '', 'value': 'show'}],  # Empty label so the text appears outside
                        value=[''],  # Default is to show trendline
                        labelStyle={'display': 'inline-block'}
                    )
                ]
            )
        ]
    ),

    # Output section for the estimates table
    html.H3("Monthly Overview of Vault Clients", className='table-title'),
    dash_table.DataTable(id='estimates-table'),
    
    # Average clients display table
    html.H3("Average Vault Clients", className='table-title'),
    dash_table.DataTable(
        id='average-clients-table',
        columns=[
            {"name": "Metric", "id": "metric"},
            {"name": "Avg Current Month Estimate", "id": "current_month_estimate"},
            {"name": "Avg Previous Month Complete", "id": "previous_month_complete"}
        ],
        data=[],  # Initial empty data
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_header={'fontWeight': 'bold'},
    ),

    dcc.Graph(id='output-graph'),

    # Average clients display
    html.Div(id='average-clients')
])

# Helper function to parse the uploaded JSON data
def parse_json(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    return json.loads(decoded.decode('utf-8'))

# Helper function to process the data and generate a plot
def process_and_plot(json_data, num_months, show_trendline, degree):
    snapshots = json_data.get("snapshots", [])
    
    # Convert snapshots to DataFrame
    df = pd.DataFrame(snapshots)
    
    # Convert 'timestamp' to datetime and handle errors
    df['timestamp'] = pd.to_datetime(df['timestamp'].str.slice(0, 26), errors='coerce')
    df = df.dropna(subset=['timestamp'])
    
    if not df.empty and pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['year_month'] = df['timestamp'].dt.to_period('M').astype(str)
        latest_records = df.loc[df.groupby('year_month')['timestamp'].idxmax()]
        
        output = []
        for _, row in latest_records.iterrows():
            metrics = row.get('metrics', {})
            output.append({
                "year_month": str(row['year_month']),
                "current_month_estimate_entity": metrics.get("clientcount.current_month_estimate.type.entity", {}).get("value", 0),
                "current_month_estimate_nonentity": metrics.get("clientcount.current_month_estimate.type.nonentity", {}).get("value", 0),
                "current_month_estimate_secret_sync": metrics.get("clientcount.current_month_estimate.type.secret_sync", {}).get("value", 0),
                "current_month_estimate_acme_client": metrics.get("clientcount.current_month_estimate.type.acme_client", {}).get("value", 0),
                "previous_month_complete_entity": metrics.get("clientcount.previous_month_complete.type.entity", {}).get("value", 0),
                "previous_month_complete_nonentity": metrics.get("clientcount.previous_month_complete.type.nonentity", {}).get("value", 0),
                "previous_month_complete_secret_sync": metrics.get("clientcount.previous_month_complete.type.secret_sync", {}).get("value", 0),
                "previous_month_complete_acme_client": metrics.get("clientcount.previous_month_complete.type.acme_client", {}).get("value", 0),
            })
        
        # Convert to DataFrame
        output_df = pd.DataFrame(output)

        # Calculate average clients over the months evaluated
        average_clients = {
            "Entity": {
                "current_month_estimate": output_df["current_month_estimate_entity"].mean(),
                "previous_month_complete": output_df["previous_month_complete_entity"].mean()
            },
            "Non-Entity": {
                "current_month_estimate": output_df["current_month_estimate_nonentity"].mean(),
                "previous_month_complete": output_df["previous_month_complete_nonentity"].mean()
            },
            "Secret Sync": {
                "current_month_estimate": output_df["current_month_estimate_secret_sync"].mean(),
                "previous_month_complete": output_df["previous_month_complete_secret_sync"].mean()
            },
            "Acme Client": {
                "current_month_estimate": output_df["current_month_estimate_acme_client"].mean(),
                "previous_month_complete": output_df["previous_month_complete_acme_client"].mean()
            }
        }

        # Prepare data for the average clients table
        average_clients_table = [
            {"metric": "Entity", "current_month_estimate": average_clients["Entity"]["current_month_estimate"], 
             "previous_month_complete": average_clients["Entity"]["previous_month_complete"]},
            {"metric": "Non-Entity", "current_month_estimate": average_clients["Non-Entity"]["current_month_estimate"], 
             "previous_month_complete": average_clients["Non-Entity"]["previous_month_complete"]},
            {"metric": "Secret Sync", "current_month_estimate": average_clients["Secret Sync"]["current_month_estimate"], 
             "previous_month_complete": average_clients["Secret Sync"]["previous_month_complete"]},
            {"metric": "Acme Client", "current_month_estimate": average_clients["Acme Client"]["current_month_estimate"], 
             "previous_month_complete": average_clients["Acme Client"]["previous_month_complete"]}
        ]

        # Create Plotly figure with subplots
        fig = make_subplots(
            rows=2, cols=4,
            subplot_titles=("Entity Estimate", "Non-Entity Estimate", "Secret Sync Estimate", "Acme Client Estimate",
                            "Previous Month Entity", "Previous Month Non-Entity", "Previous Month Secret Sync", "Previous Month Acme Client")
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
            text="Previous Month Complete",
            xref="paper", yref="paper",
            x=0.5, y=0.5,  # Adjust y for vertical spacing
            showarrow=False,
            font=dict(size=22, weight='bold')
        )

        # Function to add trendline and projections
        def add_trendline(fig, x, y, row, col, degree):
            if 'show' in show_trendline:  # Only add trendline if checkbox is checked
                x_numeric = np.arange(len(y))
                z = np.polyfit(x_numeric, y, degree)  # Use the degree selected by the user
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
                    name=f'Trendline (Degree {degree}) & Projection', 
                    line=dict(color='red', dash='dash')
                ), row=row, col=col)

        # Add plots to the subplots and trendlines
        fig.add_trace(go.Bar(x=output_df['year_month'], y=output_df['current_month_estimate_entity'], name="Entity Estimate"), row=1, col=1)
        add_trendline(fig, np.arange(len(output_df['current_month_estimate_entity'])), output_df['current_month_estimate_entity'], 1, 1, degree)

        fig.add_trace(go.Bar(x=output_df['year_month'], y=output_df['current_month_estimate_nonentity'], name="Non-Entity Estimate"), row=1, col=2)
        add_trendline(fig, np.arange(len(output_df['current_month_estimate_nonentity'])), output_df['current_month_estimate_nonentity'], 1, 2, degree)

        fig.add_trace(go.Bar(x=output_df['year_month'], y=output_df['current_month_estimate_secret_sync'], name="Secret Sync Estimate"), row=1, col=3)
        add_trendline(fig, np.arange(len(output_df['current_month_estimate_secret_sync'])), output_df['current_month_estimate_secret_sync'], 1, 3, degree)

        fig.add_trace(go.Bar(x=output_df['year_month'], y=output_df['current_month_estimate_acme_client'], name="Acme Client Estimate"), row=1, col=4)
        add_trendline(fig, np.arange(len(output_df['current_month_estimate_acme_client'])), output_df['current_month_estimate_acme_client'], 1, 4, degree)

        fig.add_trace(go.Bar(x=output_df['year_month'], y=output_df['previous_month_complete_entity'], name="Previous Month Entity"), row=2, col=1)
        add_trendline(fig, np.arange(len(output_df['previous_month_complete_entity'])), output_df['previous_month_complete_entity'], 2, 1, degree)

        fig.add_trace(go.Bar(x=output_df['year_month'], y=output_df['previous_month_complete_nonentity'], name="Previous Month Non-Entity"), row=2, col=2)
        add_trendline(fig, np.arange(len(output_df['previous_month_complete_nonentity'])), output_df['previous_month_complete_nonentity'], 2, 2, degree)

        fig.add_trace(go.Bar(x=output_df['year_month'], y=output_df['previous_month_complete_secret_sync'], name="Previous Month Secret Sync"), row=2, col=3)
        add_trendline(fig, np.arange(len(output_df['previous_month_complete_secret_sync'])), output_df['previous_month_complete_secret_sync'], 2, 3, degree)

        fig.add_trace(go.Bar(x=output_df['year_month'], y=output_df['previous_month_complete_acme_client'], name="Previous Month Acme Client"), row=2, col=4)
        add_trendline(fig, np.arange(len(output_df['previous_month_complete_acme_client'])), output_df['previous_month_complete_acme_client'], 2, 4, degree)

        # Update layout
        fig.update_layout(
            height=700,
            showlegend=False,
            # title_text="Vault Client Count Estimates",
            barmode='group'
        )

        return output_df, fig, average_clients_table
    
    return pd.DataFrame(), go.Figure(), []

# Callback for file upload
@app.callback(
    Output('estimates-table', 'data'),
    Output('average-clients-table', 'data'),
    Output('output-graph', 'figure'),
    Input('upload-data', 'contents'),
    Input('num-months', 'value'),
    Input('show-trendline', 'value'),
    Input('trendline-degree', 'value'),
)
def update_output(contents, num_months, show_trendline, degree):
    if contents is None:
        return [], [], go.Figure()

    json_data = parse_json(contents)
    output_df, fig, average_clients_table = process_and_plot(json_data, num_months, show_trendline, degree)
    
    return output_df.to_dict('records'), average_clients_table, fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')
