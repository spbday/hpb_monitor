import dash
import dash_auth
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
from dash_table import DataTable
from flask import request
import sqlalchemy as db
from sqlalchemy.sql import text
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import locale
from datetime import datetime
import pandas as pd
import plotly.express as px
#import os
#import glob
#import csv
#from xlsxwriter.workbook import Workbook
import xlsxwriter

locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")

engine = db.create_engine("sqlite:///monitor")
connection = engine.connect()
metadata = db.MetaData()
users = db.Table("Users", metadata, autoload=True, autoload_with=engine)
users_query = db.select([users])
users_ResultProxy = connection.execute(users_query)
users_ResultSet = users_ResultProxy.fetchall()
connection.close()

VALID_USERNAME_PASSWORD_PAIRS = []
for item in users_ResultSet:
    if item[2] == 1 or item[2] == 2:
        VALID_USERNAME_PASSWORD_PAIRS.append([item[0], item[1]])


ph_min = []
ph_max = []
albumen_min = []
albumen_max = []
bioactivity_min = []
bioactivity_max = []


def load_series_param():
    connection = engine.connect()
    df = pd.read_sql_query(
        "SELECT DISTINCT series, Series.name, MAX(date_param), ph, albumen, bioactivity_invivo, bioactivity_if FROM Series_param, Series WHERE Series_param.series=Series.id GROUP BY series",
        connection,
    )
    connection.close()
    for item in df["name"]:
        ph_min.append(6.5)
        ph_max.append(7.5)
        albumen_min.append(2)
        albumen_max.append(3)
        bioactivity_min.append(80)
        bioactivity_max.append(120)
    return df


# def get_min_max():
# 	connection = engine.connect()
# 	df = pd.read_sql_query("SELECT * FROM Series_param_limit", connection)
# 	connection.close()
# 	return df

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "НИИ ОЧБ СМП"
auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)

product_input = dbc.FormGroup(
    [
        dbc.Label("Препарат: ", html_for="product-row", width=4, align="left"),
        dbc.Col(
            dbc.Select(
                id="product_select1",
                options=[{"label": "Эпокрин", "value": "0"}],
                value="0",
            ),
            width=7,
        ),
    ],
    row=False,
)

param_input = dbc.FormGroup(
    [
        dbc.Label("Параметр: ", html_for="parametr-row", width=4, align="left"),
        dbc.Col(
            dbc.Select(
                id="param_select",
                options=[
                    {"label": "Ph", "value": "ph"},
                    {"label": "Общий белок", "value": "albumen"},
                    {"label": "Биокативность (in vivo)", "value": "bioactivity_invivo"},
                    {"label": "Биокативность (ИФ)", "value": "bioactivity_if"},
                ],
                value="ph",
            ),
            width=7,
        ),
    ],
    row=False,
)

inl_form = dbc.Form([product_input, param_input], inline=True)

reload_button = html.Button("Обновить данные", id="reload_button")
# download_button = [html.Button("Загрузить данные", id="download_button"), dcc.Download(id="download_text")]
# inl_form2 = dbc.Form([reload_button, download_button], inline=True)

series_df = load_series_param()
graph = (
    dcc.Graph(
        id="param_graph",
        figure={
            "data": [
                {
                    "x": series_df["name"],
                    "y": series_df["ph"],
                    "type": "lines",
                    "name": "Ph",
                },
                {
                    "x": series_df["name"],
                    "y": ph_min,
                    "type": "lines",
                    "name": "Допустимый минимум",
                },
                {
                    "x": series_df["name"],
                    "y": ph_max,
                    "type": "lines",
                    "name": "Допустимый максимум",
                },
            ],
            "layout": {
                "title": "Динамика показателя",
                "width": "1300",
                "height": "500",
            },
        },
    ),
)
app.layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.Div(html.Img(src="assets/logo_mini.png")),
                    width={"size": "auto", "offset": 1},
                ),
                dbc.Col(
                    [
                        html.Div(html.H2("Система мониторинга показателей")),
                        html.Div(html.H3("Динамика показателей")),
                    ],
                    width={"size": "auto", "align": "center"},
                ),
            ],
            align="center",
        ),
        dbc.Row(dbc.Col(html.Div(html.Hr())), align="center"),
        dbc.Row(
            dbc.Col(
                html.Div([inl_form, html.P(""), reload_button, html.P(""), html.Hr()]),
                style={"width": "100%"},
                width={"offset": 1},
            )
        ),
        dbc.Row(
            dbc.Col(
                html.Div(graph, style={"width": "100%"}),
                width={"offset": 1},
                style={"width": "100%"},
            )
        ),
        dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.Button("Загрузить данные", id="download_button"),
                        dcc.Download(id="download_xlsx"),
                    ]
                ),
                style={"width": "100%"},
                width={"offset": 1},
            )
        ),
        dbc.Row(dbc.Col(html.Div(id="output"))),
    ],
    style={"width": "100%"},
)


@app.callback(
    Output("download_xlsx", "data"),
    Input("download_button", "n_clicks"),
    prevent_initial_call=True,
)
def func(n_clicks):
    if n_clicks:
        series_df = load_series_param()
        series_df.columns = [
            "ID серии",
            "Серия",
            "Дата и время",
            "Ph",
            "Белок",
            "Биоактивность (in vivo)",
            "Биоактивность (ИФ)",
        ]
        date_str = datetime.now().strftime("%Y-%m-%d")
#        series_df.to_csv("assets/output.csv")
#        workbook = Workbook("assets/output.xlsx")
#        worksheet = workbook.add_worksheet()
#        f = open("assets/output.csv", "rt")
#        reader = csv.reader(f)
#        for r, row in enumerate(reader):
#            for c, col in enumerate(row):
#                worksheet.write(r, c, col)
#        workbook.close()
#        f = open("assets/output.xlsx", "rb")
#        s = f.read()
#        f.close()
#        return dict(content=s, filename=datetime.now().strftime("%Y-%m-%d") + ".xlsx")
        return dcc.send_data_frame(series_df.to_excel, date_str + ".xlsx", sheet_name=date_str)



@app.callback(
    Output("param_graph", "figure"),
    [Input("param_select", "value"), Input("reload_button", "n_clicks")],
)
def change_param(param_name, n_clicks):
    graph_data = []
    graph_layout = {}
    series_df = load_series_param()
    if param_name == "ph":
        graph_data = [
            {
                "x": series_df["name"],
                "y": series_df["ph"],
                "type": "lines",
                "name": "Ph",
            },
            {
                "x": series_df["name"],
                "y": ph_min,
                "type": "lines",
                "name": "Допустимый минимум",
            },
            {
                "x": series_df["name"],
                "y": ph_max,
                "type": "lines",
                "name": "Допустимый максимум",
            },
        ]
        graph_layout = {
            "title": "Динамика показателя [Ph]",
            "width": "1300",
            "height": "500",
        }
    elif param_name == "albumen":
        graph_data = [
            {
                "x": series_df["name"],
                "y": series_df["albumen"],
                "type": "lines",
                "name": "Общий белок",
            },
            {
                "x": series_df["name"],
                "y": albumen_min,
                "type": "lines",
                "name": "Допустимый минимум",
            },
            {
                "x": series_df["name"],
                "y": albumen_max,
                "type": "lines",
                "name": "Допустимый максимум",
            },
        ]
        graph_layout = {
            "title": "Динамика показателя [Общий белок]",
            "width": "1300",
            "height": "500",
        }
    elif param_name == "bioactivity_invivo":
        graph_data = [
            {
                "x": series_df["name"],
                "y": series_df["bioactivity_invivo"],
                "type": "lines",
                "name": "Биоктивность",
            },
            {
                "x": series_df["name"],
                "y": bioactivity_min,
                "type": "lines",
                "name": "Допустимый минимум",
            },
            {
                "x": series_df["name"],
                "y": bioactivity_max,
                "type": "lines",
                "name": "Допустимый максимум",
            },
        ]
        graph_layout = {
            "title": "Динамика показателя [Биоактивность (in vivo)]",
            "width": "1300",
            "height": "500",
        }
    else:
        graph_data = [
            {
                "x": series_df["name"],
                "y": series_df["bioactivity_if"],
                "type": "lines",
                "name": "Биоктивность",
            },
            {
                "x": series_df["name"],
                "y": bioactivity_min,
                "type": "lines",
                "name": "Допустимый минимум",
            },
            {
                "x": series_df["name"],
                "y": bioactivity_max,
                "type": "lines",
                "name": "Допустимый максимум",
            },
        ]
        graph_layout = {
            "title": "Динамика показателя [Биоактивность (иммуноферментная)]",
            "width": "1300",
            "height": "500",
        }
    return {"data": graph_data, "layout": graph_layout}


app.scripts.config.serve_locally = True


if __name__ == "__main__":
    app.run_server(debug=True, host="192.168.2.27", port="8051")
