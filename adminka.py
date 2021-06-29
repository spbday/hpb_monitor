import dash
import dash_auth
import dash_html_components as html
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
    if item[2] == 1:
        VALID_USERNAME_PASSWORD_PAIRS.append([item[0], item[1]])


def load_series():
    connection = engine.connect()
    stmt = text(
        "SELECT DISTINCT id, name, date_start FROM Series ORDER BY date_start DESC"
    )
    series_ResultProxy = connection.execute(stmt)
    series_ResultSet = series_ResultProxy.fetchall()

    flag = True
    series_list = []
    for item in series_ResultSet:
        is_data_stmt = text(
            "SELECT COUNT(DISTINCT id) FROM Series_param WHERE series=" + str(item[0])
        )
        sp_RP = connection.execute(is_data_stmt)
        sp_RS = sp_RP.fetchall()
        if sp_RS[0][0]:
            series_list.append(
                {
                    "label": item[1]
                    + " ("
                    + str(
                        datetime.strptime(str(item[2]), "%Y-%m-%d %H:%M:%S")
                        .date()
                        .strftime("%d.%m.%Y")
                    )
                    + ") ",
                    "value": item[0],
                }
            )
            if flag:
                series_value = item[0]
                flag = False
    connection.close()
    return [series_list, series_value]


def load_series_param(series_id):
    connection = engine.connect()
    df = pd.read_sql_query(
        "SELECT date_param, username, transparency, colorless, ph, albumen, bioactivity_invivo, bioactivity_if, comments FROM Series_param WHERE series="
        + str(series_id),
        connection,
    )
    tmp_list = []
    for item in df.transparency:
        if item:
            tmp_list.append("Да")
        else:
            tmp_list.append("Нет")
    df.transparency = tmp_list
    tmp_list = []
    for item in df.colorless:
        if item:
            tmp_list.append("Да")
        else:
            tmp_list.append("Нет")
    df.colorless = tmp_list
    tmp_list = []
    for item in df.date_param:
        tmp_list.append(
            datetime.strptime(item, "%Y-%m-%d %H:%M:%S").date().strftime("%d.%m.%Y")
        )
    df.date_param = tmp_list
    # 	tmp_list = []
    # 	for item in df.comments:
    # 		if item != "":
    # 			tmp_list.append(html.Button("Комментарии"))
    # 	df.comments = tmp_list
    df.columns = [
        "Дата",
        "Автор",
        "Прозрачность",
        "Бесцветность",
        "Ph",
        "Белок",
        "Биоактивность (in vivo)",
        "Биоактивность (ИФ)",
        "Комментарии",
    ]
    connection.close()
    return df


external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "НИИ ОЧБ СМП"
auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)

product_input = dbc.FormGroup(
    [
        dbc.Label("Препарат: ", html_for="product-row", width=5),
        dbc.Col(
            dbc.Select(
                id="product_select1",
                options=[{"label": "Эпокрин", "value": 0}],
                value=1,
            ),
            width=7,
        ),
    ],
    row=False,
)

series_data = load_series()
start_value = series_data[1]
series_input = dbc.FormGroup(
    [
        dbc.Label("Серия: ", html_for="series-row", width=3, align="left"),
        dbc.Col(
            dbc.Select(id="series_select", options=series_data[0], value=start_value),
            width=4,
        ),
    ],
    row=False,
)
reload_button = html.Button("Обновить список серий", id="reload_button")
sname_input = dbc.FormGroup(
    [
        #        dbc.Label("Идентификатор серии: ", html_for="sname-row", width=5, style={'align':'left'}),
        html.Label("Идентификатор серии: ", style={"align": "left", "width": "5"}),
        dbc.Col(
            dbc.Input(id="sname_input", type="text", value=""),
            width=4,
        ),
    ],
    row=False,
)
is_test_input = dbc.FormGroup(
    [
        # 		dbc.Label(
        # 			"Тестовая серия",
        # 			html_for="is_test_checkbox",
        # 			className="form-check-label",
        # 			width = 8
        # 		),
        #        html.Label("Тестовая серия", style={'width':'6'}),
        dbc.Col(html.Label("Тестовая серия"), width=10),
        dbc.Col(
            dbc.Checkbox(
                id="is_test_checkbox",
                className="form-check-input",
                checked="unchecked",
            ),
            width=2,
        ),
    ],
    row=True,
)
save_button = html.Button("Добавить", id="save_button")

inl_form1 = dbc.Form([sname_input, save_button], inline=True)
inl_form2 = dbc.Form([is_test_input], inline=True)
inl_form3 = dbc.Form([series_input, reload_button], inline=True)

save_modal = dbc.Modal(
    [
        dbc.ModalHeader("Сохранение"),
        dbc.ModalBody("Добавление новой серии прошло успешно"),
        dbc.ModalFooter(dbc.Button("Закрыть", id="close", className="ml-auto")),
    ],
    id="modal",
)

series_df = load_series_param(start_value)
series_param_table = DataTable(
    id="series_param_table",
    editable=False,
    row_deletable=False,
    columns=[{"name": i, "id": i} for i in series_df.columns],
    data=series_df.to_dict("records"),
    style_cell={"textAlign": "center", "padding": "5px"},
    style_header={
        "backgroundColor": "blue",
        "color": "white",
        "fontWeight": "bold",
        "border": "1px solid blue",
    },
    style_data={"border": "1px solid blue"},
)

new_series_form = dbc.Form(
    [html.P(""), inl_form1, html.P(""), inl_form2, html.P(""), html.Hr(), save_modal]
)
history_series_form = dbc.Form(
    [html.P(""), inl_form3, html.P(""), html.Hr(), html.P(""), series_param_table]
)

tabs = dbc.Tabs(
    [
        dbc.Tab(new_series_form, label="Новая серия"),
        dbc.Tab(history_series_form, label="История изменений"),
    ]
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
                        html.Div(html.H3("Интерфейс администратора")),
                    ],
                    width={"size": "auto", "align": "center"},
                    style={"align": "left"},
                ),
            ],
            align="center",
        ),
        dbc.Row(dbc.Col(html.Div(html.Hr())), align="center"),
        dbc.Row(
            dbc.Col(
                html.Div([product_input, tabs]), width={"offset": 1, "size": "auto"}
            )
        ),
        dbc.Row(dbc.Col(html.Div(id="output"))),
    ]
)


@app.callback(
    Output("modal", "is_open"),
    [Input("save_button", "n_clicks"), Input("close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(
    Output("output", "children"),
    [Input("save_button", "n_clicks")],
    state=[
        State("product_select1", "value"),
        State("sname_input", "value"),
        State("is_test_checkbox", "checked"),
    ],
)
def new_series(n_clicks, product_select1, sname_input, is_test_checkbox):
    if n_clicks:
        ns_connection = engine.connect()
        ns_stmt = text(
            "INSERT INTO Series (name, date_start, product_id, username, is_test) VALUES ('"
            + str(sname_input)
            + "','"
            + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + "',"
            + str(product_select1)
            + ",'"
            + str(request.authorization["username"])
            + "',"
            + str(is_test_checkbox)
            + ")"
        )
        ns_RP = ns_connection.execute(ns_stmt)
        ns_connection.close()
    return True


@app.callback(Output("series_param_table", "data"), Input("series_select", "value"))
def change_values(series_num):
    new_df = load_series_param(series_num)
    return new_df.to_dict("records")


@app.callback(Output("series_select", "options"), Input("reload_button", "n_clicks"))
def reload_series(reload_n_clicks):
    local_series_list = series_data[0]
    if reload_n_clicks:
        tmp = load_series()
        return tmp[0]
    return local_series_list


app.scripts.config.serve_locally = True


if __name__ == "__main__":
    app.run_server(debug=True, host="192.168.2.27", port="8050")
