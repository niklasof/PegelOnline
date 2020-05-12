import pandas as pd
import requests
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go

from functools import lru_cache
from plotly.subplots import make_subplots

PLOT_ALL_POSITIONS = False
DESTINATION_AREA = "passau"
URL_ALL_STATIONS = "https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations.json"

TIME_RANGE_IN_DAYS = 2
limit_dict = {700: "Warning level 1", 740: "Warning level 2", 770: "Warning level 3", 850: "Warning level 4"}


@lru_cache(maxsize=None)
def fetch_data(url):
    json_response = requests.get(url)
    if json_response.status_code == 200:
        return json_response.json()
    else:
        return None


def plot_all_positions(input_url):
    input_json = fetch_data(input_url)
    df_stations = pd.DataFrame(input_json)
    df_stations["target"] = 2
    df_stations.loc[df_stations["longname"].str.contains(DESTINATION_AREA.upper()), "target"] = 1

    fig = go.Figure(go.Scattermapbox(
        lat=df_stations.latitude.tolist(),
        lon=df_stations.longitude.tolist(),
        mode='markers',
        marker_color=df_stations["target"],
        marker=go.scattermapbox.Marker(size=10),
        text=df_stations.longname.tolist(),

    ))

    fig.update_layout(
        title="All available water stations, separated by color for PASSAU",
        hovermode='closest',
        mapbox=dict(
            bearing=0,
            style="open-street-map",
            center=dict(lat=48.575208623171456, lon=13.478019136458602,  # one Passau station
                        ),
            pitch=10,
            zoom=5
        ),
    )

    app = dash.Dash(__name__)
    app.layout = html.Div([dcc.Graph(figure=fig)])
    app.run_server()


def plot_current_water_levels_all():
    df_stations = pd.DataFrame(fetch_data(URL_ALL_STATIONS))
    df_temp = df_stations.loc[df_stations["longname"].str.contains(DESTINATION_AREA.upper())]
    df_list = list()
    names_list = list()

    for station in df_temp.shortname.tolist():
        if "DFH" in station:
            station_url = f"https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations/{station}" \
                          f"/DFH/measurements.json?start=P{TIME_RANGE_IN_DAYS}D"
        else:
            station_url = f"https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations/{station}" \
                          f"/W/measurements.json?start=P{TIME_RANGE_IN_DAYS}D"

        dd = (fetch_data(station_url))
        names_list.append(station)
        temp_df = pd.DataFrame(dd)
        df_list.append(temp_df)

    station_id = 1
    fig = make_subplots(rows=4, cols=1, subplot_titles=tuple(names_list))

    for station_df in df_list:
        fig.add_trace(go.Scatter(x=station_df["timestamp"].tolist(), y=station_df["value"].tolist(),
                                 name=f'Water level - {names_list[station_id - 1]}',
                                 line=dict(color='firebrick', width=4)),
                      row=station_id, col=1)

        for limits in limit_dict.keys():
            fig.add_trace(go.Scatter(
                x=[df_list[0]["timestamp"].iloc[0], df_list[0]["timestamp"].iloc[-1]],
                y=[limits, limits],
                name=f"{limit_dict[limits]} - {names_list[station_id - 1]}"), row=station_id, col=1
            )

        fig.update_layout(height=2600, title_text="Passau's water levels:")

        fig['layout']['yaxis1'].update(title='Water measurement', range=[0, 1200])
        fig['layout']['xaxis1'].update(title='Time')

        fig['layout']['yaxis2'].update(title='Water measurement', range=[0, 1200])
        fig['layout']['xaxis2'].update(title='Time')

        fig['layout']['yaxis3'].update(title='Water measurement', range=[0, 1200])
        fig['layout']['xaxis3'].update(title='Time')

        fig['layout']['yaxis4'].update(title='Water measurement', range=[0, 1200])
        fig['layout']['xaxis4'].update(title='Time')

        station_id += 1

    app = dash.Dash(__name__)
    app.layout = html.Div([dcc.Graph(figure=fig)])
    app.run_server()


def plot_current_water_levels_total():
    df_stations = pd.DataFrame(fetch_data(URL_ALL_STATIONS))
    df_temp = df_stations.loc[df_stations["longname"].str.contains(DESTINATION_AREA.upper())]
    df_list = list()
    names_list = list()

    for station in df_temp.shortname.tolist():
        if "DFH" in station:
            station_url = f"https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations/{station}" \
                          f"/DFH/measurements.json?start=P{TIME_RANGE_IN_DAYS}D"
        else:
            station_url = f"https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations/{station}" \
                          f"/W/measurements.json?start=P{TIME_RANGE_IN_DAYS}D"

        dd = (fetch_data(station_url))
        names_list.append(station)
        temp_df = pd.DataFrame(dd)
        df_list.append(temp_df)

    station_id = 1

    fig = go.Figure()
    station_colors = ["#fc0356", "#ffb0ca", "#804659", "#57001c"]
    warning_colors = ["#00db75", "#4fe09c", "#91bda8", "#9da3a0"]

    for idx, limits in enumerate(limit_dict.keys()):
        fig.add_trace(go.Scatter(
            x=[df_list[0]["timestamp"].iloc[0], df_list[0]["timestamp"].iloc[-1]],
            y=[limits, limits], line=dict(color=warning_colors[idx]),
            name=f"{limit_dict[limits]} - {limits}")
        )

    for station_df in df_list:
        fig.add_trace(go.Scatter(x=station_df["timestamp"].tolist(), y=station_df["value"].tolist(),
                                 name=f'Water level - {names_list[station_id - 1]}', mode='lines+markers',
                                 line=dict(color=station_colors[station_id - 1])))

        station_id += 1

    fig.update_layout(title_text="Passau's water levels:")

    fig['layout']['yaxis1'].update(title='Water measurement', range=[0, 1200])
    fig['layout']['xaxis1'].update(title='Time')

    app = dash.Dash(__name__)
    app.layout = html.Div([dcc.Graph(figure=fig)])
    app.run_server()


if __name__ == "__main__":
    # plots all available measurement locations on a map
    if PLOT_ALL_POSITIONS:
        print("You selected the first option of this script which will plot the measurement stations on a geo-map."
              "Please change 'PLOT_ALL_POSITIONS' after you viewed this plot and run the script again.\n")
        plot_all_positions(URL_ALL_STATIONS)

    # plots the four required measurement stations of Passau (2 plotting approaches possible, see uncommented line!)
    else:
        plot_current_water_levels_total()

        # plot_current_water_levels_all()
        # TODO: change from just an executable alternative function to an integrated version with the current plots
