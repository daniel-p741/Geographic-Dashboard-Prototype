import os
import plotly.graph_objects as go
from dash import dcc, html, Dash
from dash.dependencies import Input, Output, State
import pickle
import json
import time
from flask import Flask
import dash
from IPython.display import clear_output

# Get a list of file names in the "combined_graphs/" directory
graph_files = os.listdir("combined_graphs_2/")
# Find the longest file name and split it by commas
longest_file_name = max(graph_files, key=len).replace(".pkl", "").split(", ")

app = Dash(
    __name__, suppress_callback_exceptions=True, server=Flask(__name__)
)  # Disable caching for the entire app


def load_graph_data(file_path):
    with open(file_path, "rb") as file:
        loaded_figure_data = pickle.load(file)
    return loaded_figure_data


# Set response headers to disable caching
@app.server.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, max-age=0, must-revalidate"
    return response


app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),  # Disable caching for dcc.Location
        dcc.Checklist(
            id="checkboxes",
            options=[{"label": item, "value": item} for item in longest_file_name],
            value=[],  # Set a default value or values if needed
        ),
        html.Button("Update Graph", id="update-button", n_clicks=0),
        html.H3(id="title-text"),  # Display the selected file name as a title
        dcc.Graph(
            id="output-graph",
            figure=go.Figure(),
            config={"staticPlot": False, "displaylogo": False},
            style={"height": "60vh"},
            clear_on_unhover=False,
        ),
        html.Div(id="clear-screen", children=[]),  # Component to clear the screen
        html.Div(
            id="selected-values-store", style={"display": "none"}, children="[]"
        ),  # Hidden div to store selected values
        html.Div(
            id="timestamp-div", style={"display": "none"}
        ),  # Hidden div to store timestamp
        dcc.Store(id="page-refresh-trigger-output"),
    ]
)


@app.callback(
    [
        Output("output-graph", "figure"),
        Output("title-text", "children"),
        Output("selected-values-store", "children"),
        Output("checkboxes", "value"),
        Output("timestamp-div", "children"),
        Output("page-refresh-trigger-output", "data"),
    ],
    [Input("update-button", "n_clicks")],
    [State("checkboxes", "value")],
    prevent_initial_call=False,
)
def update_graph(n_clicks, selected_values):
    # Check if the button was clicked
    if n_clicks is None:
        # Return initial/default values
        return (
            go.Figure(),
            "No selection",
            "[]",
            [],
            dash.no_update,
            dash.no_update,
        )

    fig_map = go.Figure()

    stored_values = []

    # Update the children property of selected-values-store
    stored_values_json = json.dumps(stored_values)

    checkboxes_value = []

    # Introduce a unique identifier (timestamp) for each callback invocation
    timestamp_div = html.Div(time.perf_counter())

    # Check if selected values are empty
    if not selected_values:
        return (
            fig_map,
            "No selection",
            stored_values_json,
            checkboxes_value,
            timestamp_div,
            dash.no_update,
        )

    # Find matching files based on selected values
    matching_files = [
        file_name
        for file_name in graph_files
        if all(value in file_name for value in selected_values)
        and all(
            value not in file_name
            for value in longest_file_name
            if value not in selected_values
        )
    ]

    if len(matching_files) == 1:

        selected_file_name = matching_files[0]
        file_path = f"combined_graphs_2/{selected_file_name}"
        title_text = f"File Name: {file_path}"

        try:
            # Load the graph data synchronously
            loaded_figure_data = load_graph_data(file_path)

            fig_map.data = []

            for trace in loaded_figure_data["data"]:
                fig_map.add_trace(trace)

            fig_map.update_layout(loaded_figure_data["layout"])

        except FileNotFoundError:
            return (
                go.Figure(),
                f"File not found: {file_path}",
                stored_values_json,
                checkboxes_value,
                timestamp_div,
                dash.no_update,
            )

        stored_values = selected_values

        # Update the children property of selected-values-store
        stored_values_json = json.dumps(stored_values)

        return (
            fig_map,
            title_text,
            stored_values_json,
            checkboxes_value,
            timestamp_div,
            "true",  # Trigger page refresh
        )

    else:
        result = (
            go.Figure(),
            "No or multiple matching files found",
            stored_values_json,
            checkboxes_value,
            timestamp_div,
            dash.no_update,
        )

    clear_output(wait=True)
    return result


if __name__ == "__main__":
    app.run_server(debug=True)
