# Import required libraries
import pickle
import copy
import pathlib
import urllib.request
import dash
import math
import datetime as dt
import pandas as pd
from dash.dependencies import Input, Output, State, ClientsideFunction, MATCH
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import plotly.express as px
import geopandas as gpd
import dash_table
# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()
#------------------------------------------------------------------
# loading data into dataframe
lots = pd.read_csv("data/Thruway_Commuter_Park_and_Ride_Lots.csv")
# creating dash server
app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)
server = app.server
# setting filtering by operators option
run_by_options = [
    {"label": str(owner), "value": str(owner)}
    for owner in lots["Run By"].unique()
]
# setting filtering by operators option
paved_status_options = [
    {"label": str(option), "value": str(option)}
    for option in lots["Paved"].unique()
]
# setting filtering by operators option
lighted_status_options = [
    {"label": str(option), "value": str(option)}
    for option in lots["Lighted"].unique()
]
# app layout
app.layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3(
                                    "New York Thruway Commuter Park and Ride Lots",
                                    style={"margin-bottom": "5px"},
                                ),
                            ]
                        )
                    ],
                    className="twelve columns text-center",
                    id="title",
                )
            ],
            id="header",
            className="row flex-display",
            style={"margin-bottom": "25px"},
        ),
        # controls and first row of plots
        html.Div(
            [
                # controller
                html.Div(
                    [
                        html.P("Filter by Operator:", className="control_label"),
                        dcc.Dropdown(
                            id="run_by",
                            options=run_by_options,
                            multi=True,
                            value=lots["Run By"].unique(),
                            className="dcc_control",
                        ),
                        html.P("Filter by Paved Status:", className="control_label"),
                        dcc.Dropdown(
                            id="paved_status",
                            options=paved_status_options,
                            multi=True,
                            value=lots["Paved"].unique(),
                            className="dcc_control",
                        ),
                        html.P("Filter by Lighted Status:", className="control_label"),
                        dcc.Dropdown(
                            id="lighted_status",
                            options=lighted_status_options,
                            multi=True,
                            value=lots["Lighted"].unique(),
                            className="dcc_control",
                        ),
                    ],
                    className="pretty_container three columns",
                    id="cross-filter-options",
                ),
                # operator plot
                html.Div(
                    children=[],
                    id="count-graph",
                    className="five columns"
                ),
                # gro pandas plot
                html.Div(
                    children=[],
                    id="map",
                    className="four columns"
                )
            ],
            className="row flex-display",
        ),
        # locations per operator
        html.Div(
            [
                html.Div(
                    children=[],
                    id="drill-down",
                    className="twelve columns",
                ),
            ],
            className="row flex-display",
        ),
        # paved and lighted per location
        html.Div(
            [
                html.Div(
                    children=[],
                    id="table",
                    className="twelve columns"
                ),
            ],
            className="row flex-display",
        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)


@app.callback(
    Output("count-graph", "children"),
    [
        Input("run_by", "value"),
        Input("paved_status", "value"),
        Input("lighted_status", "value"),
    ]
)
def make_count_figure(run_by, paved_status, lighted_status):
    y_values = []
    for i in run_by:
        y_values.append(lots[(lots["Run By"] == i) & (lots["Paved"].isin(paved_status)) & (lots["Lighted"].isin(lighted_status))]["Title"].value_counts().sum() )
    fig = go.Figure(
            data=[
                    go.Bar(
                        x=run_by, 
                        y=y_values,
                    )
                ]
            )
    fig.update_layout(
            title_text="Parking Lot Operators",
            xaxis_title="Operator Name",
            yaxis_title="Number of Lots"
        )
    operators = html.Div(
            children = [
                dcc.Graph(id="operators", figure=fig),
            ],
            id="operators container",
            className="pretty_container",
        )
    return operators

@app.callback(
    Output("drill-down", "children"),
    [
        Input("run_by", "value"),
        Input("paved_status", "value"),
        Input("lighted_status","value")
    ]
)
def make_aggregate_figure(run_by, paved_status, lighted_status):
    graphs = [
        html.H3("Locations Per Operator",style={"margin-bottom": "10px", "margin-left": "45%", "margin-top": "10px"})
        ]
    iteration=0
    for i in run_by:
        iteration+=1
        df = lots[(lots["Run By"] == i) & (lots["Paved"].isin(paved_status)) & (lots["Lighted"].isin(lighted_status))]
        fig = go.Figure(
            data=[
                    go.Bar(
                        x=df["Title"], 
                        y=df["Spaces"],
                    )
                ]
            )
        fig.update_layout(
            title_text=i+"\nLocations",
            xaxis_title="Lot Title",
            yaxis_title="Number of Spaces in Lot"
        )
        spaces_graph = html.Div(
            [
                dcc.Graph(
                    id={
                        "type": "operator-graph",
                        "index": iteration
                        }, 
                    figure=fig, 
                    ),
            ],
            id=i+" graph container",
            className="three columns pretty_container",
            style={'display': 'inline-block', "margin-right": "15px"},
        )

        graphs.append(spaces_graph)
    return graphs


@app.callback(
    Output("map", "children"),
    [
        Input("run_by", "value"),
        Input("paved_status", "value"),
        Input("lighted_status","value")
    ]
)
def get_map(run_by, paved_status, lighted_status):
    df = lots[(lots["Run By"].isin(run_by)) & (lots["Paved"].isin(paved_status)) & (lots["Lighted"].isin(lighted_status))]
    fig = px.scatter_geo(
            df,
            lat=df.Latitude,
            lon=df.Longitude,
            scope="usa",
            title="Map",
            center={"lat": df.Latitude.mean(), "lon": df.Longitude.mean()},
            hover_name="Title",
            hover_data=lots.columns.drop("Title","Location")
        )
    map_plot = html.Div(
            [
                dcc.Graph(id="map-plot", figure=fig),
            ],
            id="map container",
            className="pretty_container",
    )
    return map_plot

@app.callback(
    Output("table", "children"),
    [
        Input("run_by", "value"),
        Input("paved_status", "value"),
        Input("lighted_status","value")
    ]
)
def get_table(run_by, paved_status, lighted_status):
    df = lots[(lots["Run By"].isin(run_by)) & (lots["Paved"].isin(paved_status)) & (lots["Lighted"].isin(lighted_status))].drop(columns=["Location","Latitude","Longitude"])
    tble = html.Div(
        [
            dash_table.DataTable(
                id="table-data",
                columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict('records'),
            )
        ],
        id="table",
        className="twelve columns pretty_container",
        style={'display': 'inline-block', "margin-right": "15px", "overflow": "scroll"},
    )
    return tble
# main
if __name__ == "__main__":
    app.run_server(debug=True)