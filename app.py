# importting libraries
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
import psycopg2
from psycopg2 import Error
import os
import folium
# update script to check whether data is new
import update_tble
# connecting to database and getting lots data
try:
    connection = psycopg2.connect(os.environ.get("DATABASE_URL"))
    print("PostgreSQL connection is opened")
    query = "SELECT * FROM lots"
    lots = pd.read_sql_query(query, connection)
except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
finally:
    if (connection):
        connection.close()
        print("PostgreSQL connection is closed")
# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()
#------------------------------------------------------------------
# loading data into dataframe without using database
#lots = pd.read_csv("data/Thruway_Commuter_Park_and_Ride_Lots.csv")
#------------------------------------------------------------------
# creating dash app
app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)
server = app.server
# setting filtering by operators option
run_by_options = [
    {"label": str(owner), "value": str(owner)}
    for owner in lots["operator"].unique()
]
# setting filtering by is_paved option
paved_status_options = [
    {"label": str(option), "value": str(option)}
    for option in lots["is_paved"].unique()
]
# setting filtering by light option
lighted_status_options = [
    {"label": str(option), "value": str(option)}
    for option in lots["light"].unique()
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
                                html.H2(
                                    "New York Thruway Commuter Park and Ride Lots",
                                    style={"margin-bottom": "10px"},
                                ),
                            ]
                        ),
                    ],
                    className="twelve columns",
                    id="title",
                ),
                html.Div(
                    [
                        html.Div(
                            html.P(
                                "The Commuter Park Lots Listing provides travelers along the Thruway System with a listing of available locations in which to park their vehicle and commute from." + "\n" +
                                "The Thruway Authority does offer several commuter Park and Ride lots across the system. Parking at these commuter lots is posted for a maximum stay of 16 hours, and are not designated for multiple stays. Lengthy stays defeat the purpose of Commuter Park and ride lots. Traffic personnel and State Police Police strictly enforce these parking regulations. There are no overnight or long-term parking facilities on the System. "
                            )
                        )
                    ],
                    className="six columns offset-by-three",
                    id="basic_info",
                    style={"margin-top": "10px"}
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.A(
                                        html.Button("Learn More", id="learn-more-button"),
                                        href="https://data.ny.gov/Transportation/Thruway-Commuter-Park-and-Ride-Lots/nvxe-b625",
                                        )
                            ],
                        ),
                    ],
                    className="one column offset-by-five",
                    id="button_row",
                    style={"margin-bottom": "10px"}
                )
            ],
            id="header",
            className="row inline-block-display",
        ),
        # controls and first row of plots
        html.Div(
            [
                # controller
                html.Div(
                    [
                        html.P("Filter by Number of Available Spaces:", className="control_label"),
                        html.P(id='output-container-range-slider', className="control_label"),
                        dcc.RangeSlider(
                            id="avail_spaces_slider",
                            min=0,
                            max=lots["available_spaces"].max()+1,
                            value=[0, lots["available_spaces"].max()],
                            className="dcc_control",
                        ),
                        html.P("Filter by Operator:", className="control_label"),
                        dcc.Dropdown(
                            id="run_by",
                            options=run_by_options,
                            multi=True,
                            value=lots["operator"].unique(),
                            className="dcc_control",
                        ),
                        html.P("Filter by Paved Status:", className="control_label"),
                        dcc.Dropdown(
                            id="paved_status",
                            options=paved_status_options,
                            multi=True,
                            value=lots["is_paved"].unique(),
                            className="dcc_control",
                        ),
                        html.P("Filter by Lighted Status:", className="control_label"),
                        dcc.Dropdown(
                            id="lighted_status",
                            options=lighted_status_options,
                            multi=True,
                            value=lots["light"].unique(),
                            className="dcc_control",
                        ),
                    ],
                    className="pretty_container three columns",
                    id="cross-filter-options",
                ),
                # operator plot container
                html.Div(
                    children=[],
                    id="count-graph",
                    className="five columns"
                ),
                # geopandas plot container
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
                    style={"margin":"auto"}
                ),
            ],
            className="row flex-display",
        ),
        # table container
        html.Div(
            [
                html.Div(
                    children=[],
                    id="table",
                    className="twelve columns",
                ),
            ],
            className="row flex-display",
        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)

# displaying available spaces range
@app.callback(
    Output("output-container-range-slider", "children"),
    [
        Input("avail_spaces_slider", "value"),
    ]
)
def update_output(spaces_range):
    output_range = "Between " + str(spaces_range[0]) + " and " + str(spaces_range[1]) + " Available Spaces"
    return output_range

# by by lot size plot
@app.callback(
    Output("count-graph", "children"),
    [
        Input("run_by", "value"),
        Input("paved_status", "value"),
        Input("lighted_status", "value"),
        Input("avail_spaces_slider", "value"),
    ]
)
def make_count_figure(run_by, paved_status, lighted_status, spaces_range):
    print(spaces_range)
    y_values = []
    for i in run_by:
        y_values.append(lots[(lots["operator"] == i) & (lots["is_paved"].isin(paved_status)) & (lots["light"].isin(lighted_status)) & (lots["available_spaces"] >= spaces_range[0]) & (lots["available_spaces"] <= spaces_range[1])]["lot_name"].value_counts().sum() )
    total = sum(y_values)
    fig = go.Figure(
            data=[
                    go.Bar(
                        x=run_by, 
                        y=y_values,
                    )
                ]
            )
    fig.update_layout(
            title_text="Parking Lot Operators" +  "       " + str(total) + " Lots",
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

# generate individual location plots
@app.callback(
    Output("drill-down", "children"),
    [
        Input("run_by", "value"),
        Input("paved_status", "value"),
        Input("lighted_status","value"),
        Input("avail_spaces_slider", "value"),
    ]
)
def make_aggregate_figure(run_by, paved_status, lighted_status, spaces_range):
    graphs = [
            html.Div(
                [
                    html.Div(
                        [
                            html.H3("Locations Per Operator",style={"margin-bottom": "15px", "margin-top": "10px"})
                        ],
                        className="three columns offset-by-four"
                    )
                ], 
                className="row"
            ),
            html.Br()
        ]
    iteration=0
    for i in run_by:
        iteration+=1
        df = lots[(lots["operator"] == i) & (lots["is_paved"].isin(paved_status)) & (lots["light"].isin(lighted_status)) & (lots["available_spaces"] >= spaces_range[0]) & (lots["available_spaces"] <= spaces_range[1])]
        fig = go.Figure(
                data=[
                        go.Bar(
                            x=df["lot_name"], 
                            y=df["available_spaces"],
                        )
                    ]
                )
        fig.update_layout(
                title_text=i,
                xaxis_title="Lot Name",
                yaxis_title="Number of Available Spaces in Lot",
                font=dict(
                    size=12,
                )
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
                style={'display': 'inline-block', "margin-right": "10px"},
            )
        graphs.append(spaces_graph)
    return graphs

# update map plot
@app.callback(
    Output("map", "children"),
    [
        Input("run_by", "value"),
        Input("paved_status", "value"),
        Input("lighted_status","value"),
        Input("avail_spaces_slider", "value"),
    ]
)
def get_map(run_by, paved_status, lighted_status, spaces_range):
    df = lots[(lots["operator"].isin(run_by)) & (lots["is_paved"].isin(paved_status)) & (lots["light"].isin(lighted_status)) & (lots["available_spaces"] >= spaces_range[0]) & (lots["available_spaces"] <= spaces_range[1])]
    
    titles = df[df.columns[0]]
    lat =  df[df.columns[7]]
    long =  df[df.columns[8]]
    avg_lat = sum(lat)/len(lat)
    avg_long = sum(long)/len(long)
    print(len(df))
    map = folium.Map(location=[avg_lat, avg_long], zoom_start=6)
    # adding markers
    for i in range(0,len(df)):
        folium.Marker(
            [lat[i], long[i]], popup=f"<i>{titles[i]}</i>"
        ).add_to(map)
    map.save("data/map.html")

    return html.Div([html.Iframe(
        id='map',
        srcDoc=open('data/map.html','r').read(),
        width='100%',
        height="300"
    )],
        id="map container",
        className="pretty_container",
        style={"overflow": "scroll"},)

# update table
@app.callback(
    Output("table", "children"),
    [
        Input("run_by", "value"),
        Input("paved_status", "value"),
        Input("lighted_status","value"),
        Input("avail_spaces_slider", "value"),
    ]
)
def get_table(run_by, paved_status, lighted_status, spaces_range):
    df = lots[(lots["operator"].isin(run_by)) & (lots["is_paved"].isin(paved_status)) & (lots["light"].isin(lighted_status)) & (lots["available_spaces"] >= spaces_range[0]) & (lots["available_spaces"] <= spaces_range[1])].drop(columns=["lot_location","latitutide","longtitude"])
    tble = html.Div(
        [
            dash_table.DataTable(
                id="table-data",
                columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict('records'),
            )
        ],
        id="table container",
        className="pretty_container",
        style={"overflow": "scroll"},
    )
    return tble
# main
if __name__ == "__main__":
    app.run_server(debug=True)