import dash
import dash_auth
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
from flask import request
import sqlalchemy as db
from sqlalchemy.sql import text
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import locale
from datetime import datetime

locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")  # the ru locale is installed

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
            is_data = " * "
        else:
            is_data = "   "
        series_list.append(
            {
                "label": item[1]
                + is_data
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


external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "НИИ ОЧБ СМП"
auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)

product_input = dbc.FormGroup(
    [
        dbc.Label("Препарат: ", html_for="product-row", width=5, align="left"),
        dbc.Col(
            dbc.Select(
                id="product_select", options=[{"label": "Эпокрин", "value": 0}], value=1
            ),
            width=7,
        ),
    ],
    row=True,
)

series_data = load_series()
series_input = dbc.FormGroup(
    [
        dbc.Label("Серия: ", html_for="series-row", width=5, align="left"),
        dbc.Col(
            [
                dbc.Select(
                    id="series_select", options=series_data[0], value=series_data[1]
                ),
                html.Button("Обновить список серий", id="reload_button"),
            ],
            width=7,
        ),
    ],
    row=True,
)
transparency_input = dbc.FormGroup(
    [
        # 		dbc.Label(
        # 			"Раствор прозрачен",
        # 			html_for="transparency-checkbox",
        # 			className="form-check-label",
        # 		),
        dbc.Col(html.Label("Раствор прозрачен"), width=5),
        dbc.Col(
            dbc.Checkbox(
                id="transparency_checkbox", className="form-check-input", checked="0"
            ),
            width=2,
        ),
    ],
    row=True,
)
colorless_input = dbc.FormGroup(
    [
        # 		dbc.Label(
        # 			"Раствор бесцветен",
        # 			html_for="colorless-checkbox",
        # 			className="form-check-label",
        # 		),
        dbc.Col(html.Label("Раствор бесцветен"), width=5),
        dbc.Col(
            dbc.Checkbox(
                id="colorless_checkbox", className="form-check-input", checked="0"
            ),
            width=2,
        ),
    ],
    row=True,
)
ph_input = dbc.FormGroup(
    [
        dbc.Label("Ph: ", html_for="ph-row", width=5),
        dbc.Col(
            dbc.Input(
                id="ph_input", type="number", min=0.1, max=99.9, step=0.1, value="0"
            ),
            width=7,
        ),
    ],
    row=True,
)
albumen_input = dbc.FormGroup(
    [
        dbc.Label("Общий белок: ", html_for="albumen-row", width=5),
        dbc.Col(
            dbc.Input(
                id="albumen_input",
                type="number",
                min=0.1,
                max=99.9,
                step=0.1,
                value="0",
            ),
            width=7,
        ),
    ],
    row=True,
)
bioactivity_invivo_input = dbc.FormGroup(
    [
        dbc.Label(
            "Биоактивность (in vivo): ", html_for="bioactivity_invivo-row", width=5
        ),
        dbc.Col(
            dbc.Input(
                id="bioactivity_invivo_input",
                type="number",
                min=1,
                max=150,
                step=1,
                value="0",
            ),
            width=7,
        ),
    ],
    row=True,
)
bioactivity_if_input = dbc.FormGroup(
    [
        dbc.Label(
            "Биоактивность (иммуноферментная): ", html_for="bioactivity_if-row", width=5
        ),
        dbc.Col(
            dbc.Input(
                id="bioactivity_if_input",
                type="number",
                min=1,
                max=150,
                step=1,
                value="0",
            ),
            width=7,
        ),
    ],
    row=True,
)
comments_input = dbc.FormGroup(
    [
        dbc.Label("Комментарии: ", html_for="comments-row", width=5),
        dcc.Textarea(
            id="comments_input",
            value="",
            style={"width": "100%", "height": "100"},
        ),
    ]
)

save_button = html.Button("Сохранить", id="save_button")
save_modal = dbc.Modal(
    [
        dbc.ModalHeader("Сохранение"),
        dbc.ModalBody("Соханение показателей прошло успешно"),
        dbc.ModalFooter(dbc.Button("Закрыть", id="close", className="ml-auto")),
    ],
    id="modal",
)

form = dbc.Form(
    [
        product_input,
        series_input,
        transparency_input,
        colorless_input,
        ph_input,
        albumen_input,
        bioactivity_invivo_input,
        bioactivity_if_input,
        comments_input,
        save_button,
        save_modal,
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
                        html.Div(html.H3("Показатели серии")),
                    ],
                    width={"size": "auto"},
                    style={"align": "center"},
                ),
            ],
            align="center",
        ),
        dbc.Row(dbc.Col(html.Div(html.Hr())), align="center"),
        dbc.Row(dbc.Col(html.Div(form), width={"offset": 2})),
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
    Output("series_select", "options"),
    [Input("save_button", "n_clicks"), Input("reload_button", "n_clicks")],
    state=[
        State("series_select", "value"),
        State("transparency_checkbox", "checked"),
        State("colorless_checkbox", "checked"),
        State("ph_input", "value"),
        State("albumen_input", "value"),
        State("bioactivity_invivo_input", "value"),
        State("bioactivity_if_input", "value"),
        State("comments_input", "value"),
    ],
)
def save_param(
    save_n_clicks,
    reload_n_clicks,
    series_select,
    transparency_checkbox,
    colorless_checkbox,
    ph_input,
    albumen_input,
    bioactivity_invivo_input,
    bioactivity_if_input,
    comments_input,
):
    local_series_list = series_data[0]
    if save_n_clicks:
        param_connection = engine.connect()
        param_stmt = text(
            "INSERT INTO Series_param (series, transparency, colorless, ph, albumen, bioactivity_invivo, bioactivity_if, username, date_param, comments) VALUES ("
            + str(series_select)
            + ","
            + str(transparency_checkbox)
            + ","
            + str(colorless_checkbox)
            + ","
            + str(ph_input)
            + ","
            + str(albumen_input)
            + ","
            + str(bioactivity_invivo_input)
            + ","
            + str(bioactivity_if_input)
            + ",'"
            + str(request.authorization["username"])
            + "','"
            + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + "','"
            + str(comments_input)
            + "')"
        )
        param_RP = param_connection.execute(param_stmt)
        param_connection.close()

        local_series_list = []
        for series_item in series_data[0]:
            if str(series_item["value"]) == str(series_select):
                local_series_list.append(
                    {
                        "label": series_item["label"].replace("   ", " * "),
                        "value": series_item["value"],
                    }
                )
            else:
                local_series_list.append(
                    {"label": series_item["label"], "value": series_item["value"]}
                )
    if reload_n_clicks:
        tmp = load_series()
        return tmp[0]
    return local_series_list


@app.callback(
    [
        Output("transparency_checkbox", "checked"),
        Output("colorless_checkbox", "checked"),
        Output("ph_input", "value"),
        Output("albumen_input", "value"),
        Output("bioactivity_invivo_input", "value"),
        Output("bioactivity_if_input", "value"),
        Output("comments_input", "value"),
    ],
    [Input("series_select", "value")],
)
def change_values(series_num):
    param_connection = engine.connect()
    is_data_stmt = text(
        "SELECT COUNT(DISTINCT id) FROM Series_param WHERE series=" + str(series_num)
    )
    sp_RP = param_connection.execute(is_data_stmt)
    sp_RS = sp_RP.fetchall()
    if sp_RS[0][0]:
        param_stmt = text(
            "SELECT transparency, colorless, ph, albumen, bioactivity_invivo, bioactivity_if, comments FROM Series_param WHERE series="
            + str(series_num)
            + " ORDER BY date_param DESC"
        )
        param_RP = param_connection.execute(param_stmt)
        param_RS = param_RP.fetchall()
        param_connection.close()
        return [
            param_RS[0][0],
            param_RS[0][1],
            param_RS[0][2],
            param_RS[0][3],
            param_RS[0][4],
            param_RS[0][5],
            param_RS[0][6],
        ]
    else:
        param_connection.close()
        return [0, 0, 0, 0, 0, 0, ""]


app.scripts.config.serve_locally = True


if __name__ == "__main__":
    app.run_server(debug=True, host="192.168.2.27", port="8080")
