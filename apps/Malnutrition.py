import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from utils import zscore_plot
from app import app
import ssl
import requests
from urllib.request import urlopen
import joblib
from utils import top10table
from utils import SHAP_Val
import pyodbc
#from azure.storage.blob import BlockBlobService

ssl._create_default_https_context = ssl._create_unverified_context

"""
-------------------------------------------Azure Blob Connection------------------------------------

STORAGEACCOUNTURL= 'https://kidnutrilytics2.blob.core.windows.net'
CONTAINERNAME= 'blob2'
LOCALFILENAME_RELAPSE= 'assets/base_relapse.csv'
BLOBNAME_RELAPSE= 'base_relapse.csv'
LOCALFILENAME_MALNUTRITION= 'assets/base_malnutrition.csv'
BLOBNAME_MALNUTRITION= 'base_malnutrition.csv'

#download from blob
blob_service_client_instance = BlobServiceClient(account_url=STORAGEACCOUNTURL, credential=STORAGEACCOUNTKEY)
blob_client_instance_rel = blob_service_client_instance.get_blob_client(CONTAINERNAME, BLOBNAME_RELAPSE, snapshot=None)
with open(LOCALFILENAME_RELAPSE, "wb") as my_blob:
    blob_data = blob_client_instance_rel.download_blob()
    blob_data.readinto(my_blob)

blob_client_instance_mal = blob_service_client_instance.get_blob_client(CONTAINERNAME, BLOBNAME_MALNUTRITION, snapshot=None)
with open(LOCALFILENAME_MALNUTRITION, "wb") as my_blob:
    blob_data = blob_client_instance_rel.download_blob()
    blob_data.readinto(my_blob)
"""

#-----------------------------------------*Relapse*-------------------------------------
with urlopen('https://kidnutrilytics2.blob.core.windows.net/blob2/Modelo_relapse.sav') as response:
    modelo_relapse = joblib.load(response)

base_relapse = pd.read_csv('https://kidnutrilytics2.blob.core.windows.net/blob2/base_relapse.csv?sp=r&st=2022-01-26T00:57:43Z&se=2022-05-01T08:57:43Z&sip=186.86.32.33&spr=https&sv=2020-08-04&sr=b&sig=HFp5XmZRRxn7JFSTwpIQalhsGvVtEqu1viK2VX1zuck%3D')
top10_df_r = top10table.createTable_top(modelo_relapse, base_relapse)
p_range_r = str(top10_df_r["Range_probability"].iloc[0])
n_children_r = top10_df_r.shape[0]
shap_r = SHAP_Val.plotShapValuesTop(modelo_relapse, top10_df_r)
s_table_r, plot_table_r = top10table.table_to_show(top10_df_r)
show_table_r = s_table_r[s_table_r['AVG ZScore'] > -100].sample(1000)
dist_plot_r = zscore_plot.zscore_distplot(show_table_r)

#-----------------------------------------*Malnutrition*----------------------------------

with urlopen('https://kidnutrilytics2.blob.core.windows.net/blob2/Modelo_malnutrition.sav') as response:
    modelo_malnutrition = joblib.load(response)

base_malnutrition = pd.read_csv('https://kidnutrilytics2.blob.core.windows.net/blob2/base_malnutrition.csv?sp=r&st=2022-01-26T03:02:29Z&se=2022-05-01T11:02:29Z&sip=186.86.32.33&spr=https&sv=2020-08-04&sr=b&sig=lRRXZSvl%2FZX9yMP6IxA1xW70h08Q6mjSKGVOa1%2B81YA%3D')
top10_df_m = top10table.createTable_top(modelo_malnutrition, base_malnutrition)
p_range_m = str(top10_df_m["Range_probability"].iloc[0])
n_children_m = top10_df_m.shape[0]
shap_m = SHAP_Val.plotShapValuesTop(modelo_malnutrition, top10_df_m)
s_table_m, plot_table_m = top10table.table_to_show(top10_df_m)
show_table_m = s_table_m[s_table_m['AVG ZScore'] > -100].sample(1000)
dist_plot_m = zscore_plot.zscore_distplot(show_table_m)

PAGE_SIZE = 20
"""
--------------------------------------------Layout--------------------------------------------
"""
layout = dbc.Container([
    dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                [
                    html.H4("Risk Selection", className="card-title"),
                    html.Hr(id="hr_1"),
                    dbc.Row(
                        dbc.Col(dcc.Dropdown(
                                    id="model",
                                    options=[{'value': 0, 'label': "Malnutrition"}, {'value': 1, 'label': "Relapse"}],
                                    value=1,
                        )), className="mb-3"),
                    dbc.Row(
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                            [
                                dbc.Row([
                                    dbc.Col(html.H5(id ="n_children", className="card-v"), width={"size": 4,"offset": 1}),
                                    dbc.Col(html.H5(id ="p_range", className="card-v"), width={"size": 6, "offset": 1}),
                                ]),
                                dbc.Row([
                                    dbc.Col(html.H6("Children at Risk", className='text-v')),
                                    dbc.Col(html.H6("Probability Range", className='text-v')),
                                ]),
                            ])
                        ,color="primary", outline=True)
                    )),
                ]),color="light", outline=True)
        , width=3),
        dbc.Col(
            dbc.Card(
                dbc.CardImg(src="/assets/happychildren.jpg")
            , color="light", outline=True), width=9)
    ], className="mb-4",),
    dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                [
                    html.H4("SHAP Values", className="card-title"),
                    html.Hr(id="hr_1"),
                    dbc.CardImg(id="shap_fig")
                ]
                ),color="light", outline=True),
        width=5),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                [
                    html.H4("AVG ZScore Distplot for Children", className="card-title"),
                    html.Hr(id="hr_1"),
                    dcc.Graph(id="dist_plot", figure={})
                ]),
            color="light", outline=True)
        , width=7)
    ], className="mb-4",),
    dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                [
                    html.H4("What Characterizes them?", className="card-title"),
                    html.Hr(id="hr_1"),
                    dcc.Dropdown(id="user_choice", options=[{"label": "Education", "value": "ind_estudia"},
                                              {"label": "Water Days Access", "value": "uni_dias_agua"},
                                              {"label": "Avg Income", "value": "ingresos_promp_imp"},
                                              {"label": "No. Privations", "value": "noprivaciones"},
                                              {"label": "Gender", "value": "sexo_persona"},
                                              {"label": "Care Type", "value": "tipo_cuidado"},
                                              {"label": "Class Cod", "value": "cod_clase"}],
                             value="sexo_persona", clearable=False),
                    dcc.Graph(id="my_bar", figure={})
                ]
                ),color="light", outline=True),
        width = 5),
        dbc.Col(
            dbc.Card(
            dbc.CardBody(
            [
                html.H4("Children Information", className="card-title"),
                html.Hr(id="hr_1"),
                dash_table.DataTable(id="datatable-paging-page-count",
                                     columns=[
                                         {"name": i, "id": i} for i in show_table_r.columns
                                     ],
                                     page_current=0,
                                     page_size=PAGE_SIZE,
                                     page_action="custom",
                                     page_count=50,
                                     style_as_list_view=True,
                                     style_cell={"padding": "5px",
                                                 "minWidth": "50px", "width": "50px", "maxWidth": "50px"
                                                 },  # style_cell refers to the whole table
                                     style_header={
                                         "backgroundColor": "#F9FAFD",
                                         "fontWeight": "bold",
                                         "color": "#017EFA"
                                     },
                                     fixed_rows={"headers": True},
                                     style_cell_conditional=[
                                        {"if": {"column_id": "Child ID"},
                                            "textAlign": "left",
                                            "width": "10%",
                                         },
                                        {"if": {"column_id": "MIN ZScore"},
                                            "width": "10%",
                                         },
                                        {"if": {"column_id": "MAX ZScore"},
                                            "width": "10%",
                                         },
                                     ],
                                     style_table={"height": 400},
                                     style_data_conditional=[
                                         {
                                         "if": {"column_id": "Child ID"},
                                            "backgroundColor": "#F0F2F8",
                                         },
                                         {
                                         "if": {"column_id": "Malnutrition Count"},
                                            "backgroundColor": "#F0F2F8",
                                         },
                                         {
                                         "if": {"column_id": "Probability"},
                                            "backgroundColor": "#F0F2F8",
                                         },
                                     ]
                                     ),
                dbc.Button("Download CSV", color="primary", className="mr-1", id="btn_csv"),
                dcc.Download(id="download-dataframe-csv"),
            ]),color="light", outline=True),
        width = 7)
    ], className="mb-4",)
], fluid=True)

"""
--------------------------------------------Callbacks--------------------------------------------
"""
"""
callback to update graphs depending on the model selected
"""
@app.callback(
    [Output(component_id="n_children", component_property="children"),
    Output(component_id="p_range", component_property="children"),
    Output(component_id="shap_fig", component_property="src"),
    Output(component_id="dist_plot", component_property="figure"),],
    [Input(component_id="model", component_property="value"),]
)
def update_graphs(model_choice):
    if model_choice == 0:
        c = n_children_m
        p = p_range_m
        img = shap_m
        dist_p = dist_plot_m
    if model_choice == 1:
        c = n_children_r
        p = p_range_r
        img = shap_r
        dist_p = dist_plot_r
    return c, p, img, dist_p

"""
callback to update data to display on table on the model selected and pages
"""
@app.callback(
    Output('datatable-paging-page-count', 'data'),
    [Input('datatable-paging-page-count', "page_current"),
    Input('datatable-paging-page-count', "page_size"),
    Input(component_id="model", component_property="value"),])
def update_table(page_current,page_size, model):
    if model == 0:
        return show_table_m.iloc[
        page_current*page_size:(page_current+ 1)*page_size
        ].to_dict('records')
    if model == 1:
        return show_table_r.iloc[
        page_current*page_size:(page_current+ 1)*page_size
        ].to_dict('records')

"""
callback to update bar plots according to the user choice on dropdown
"""
@app.callback(
    Output("my_bar", "figure"),
    [Input("user_choice", "value"),
     Input(component_id="model", component_property="value"),]
)

def bar_plots(value, model):
    if model == 0:
        df = plot_table_m
    if model == 1:
        df = plot_table_r
    fig = px.histogram(df, x=value, color_discrete_sequence=['#1CBE4F'])
    fig.update_layout(xaxis_title=value, yaxis_title="Count")
    fig.update_layout({'plot_bgcolor': 'rgba(0, 0, 0, 0)', 'paper_bgcolor': 'rgba(0, 0, 0, 0)'})
    return fig

"""
callback to download .csv file with info of the children at risk
"""
n_clicks = 0

@app.callback(
    Output("download-dataframe-csv", "data"),
    [Input("btn_csv", "n_clicks"),
    Input(component_id="model", component_property="value"),],
    prevent_initial_call=True,
)
def func(n_clicks, model):
    if n_clicks > 0:
        if model == 0:
            df = show_table_m
        if model == 1:
            df = show_table_r
        return dcc.send_data_frame(df.to_csv, "children_at_risk.csv")
