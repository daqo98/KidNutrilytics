import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pathlib
from app import app
import dash_bootstrap_components as dbc
# colombian map dependencies
from utils import mapcolombia
from utils import plot_by_year
import pandas as pd
from urllib.request import urlopen
import requests
import math
import ssl
import json
import pyodbc


ssl._create_default_https_context = ssl._create_unverified_context

with urlopen('https://raw.githubusercontent.com/namonroyr/colombia_mapa/master/co_2018_MGN_DPTO_POLITICO.geojson') as response:
    colombia = json.load(response)

"""
-------------------------------------------SQL Connection------------------------------------
"""
server = 'ds4a-server2.database.windows.net'
database = 'ds4a'
username = 'namonroyr'
password = 'ds4a123*'
driver= '/opt/microsoft/msodbcsql17/lib64/libmsodbcsql-17.8.so.1.1'

conn = pyodbc.connect('DRIVER='+driver+';SERVER=tcp:'+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password)

def execute_azure_query(query, with_cursor=False):
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        res = cursor.fetchall()
        if with_cursor:
            return (res, cursor)
        else:
            return res
    finally:
        pass
        cursor.close()


def pandas_df_from_azure_query(query):
    df = pd.read_sql(query,conn)
    return df

#Se filtran beneficiarios cuyo target de relapse para los próximos 6 meses sea 1
df_base_target_2018 = pandas_df_from_azure_query(
"""
SELECT IdBeneficiario, Marca_Target_Reincidencia_F6M, Marca_Target_EntroEnDesnutricion_F6M,
cod_dpto, nom_dpto
FROM ICBF.base_target_2018
"""
)

df_base_target_2019 = pandas_df_from_azure_query(
"""
SELECT IdBeneficiario, Marca_Target_Reincidencia_F6M, Marca_Target_EntroEnDesnutricion_F6M,
cod_dpto, nom_dpto
FROM ICBF.base_target_2019
"""
)

df_base_target_2018['Año'] = 2018
df_base_target_2019['Año'] = 2019

df_base_target = pd.concat(df_base_target_2018, df_base_target_2019)

#Se filtran beneficiarios cuyo target de relapse para los próximos 6 meses sea 1
df_target1_relapse = base_target[base_target['Marca_Target_Reincidencia_F6M']==1]
#Se filtran beneficiarios cuyo target de desnutrición para los próximos 6 meses sea 1
df_target1_mal = base_target[base_target['Marca_Target_EntroEnDesnutricion_F6M']==1]

#Se agrupan los target de relapse por dpto para obtener el count
dpts_count_target1_relapse = df_target1_relapse.groupby(['cod_dpto', 'nom_dpto']).size().to_frame('Count_Dpto_Relapse').reset_index()

#Se agrupan los target de malnutrition por dpto para obtener el count
dpts_count_target1_mal = df_target1_mal.groupby(['cod_dpto', 'nom_dpto']).size().to_frame('Count_Dpto_Malnutrition').reset_index()

#Se agrupan el count total de registros suministrados por dpto
dpts_count_total = base_target.groupby(['cod_dpto', 'nom_dpto']).size().to_frame('Count_Dpto_Total').reset_index()

#Se unen los 3 dfs creados anteriormente
data_frames = [dpts_count_total, dpts_count_target1_mal, dpts_count_target1_relapse]
dpts_count = reduce(lambda  left,right: pd.merge(left,right,on=["cod_dpto", "nom_dpto"]), data_frames)

#Se crea una columna con el ratio entre count relapse y total por dept
dpts_count["Relapse_Percentage"] = dpts_count["Count_Dpto_Relapse"]/dpts_count["Count_Dpto_Total"]*100
#Se crea una columna con el ratio entre count malnutrition y total por dept
dpts_count["Malnutrition_Percentage"] = dpts_count["Count_Dpto_Malnutrition"]/dpts_count["Count_Dpto_Total"]*100
#Casting y cambios de formato
dpts_count['cod_dpto']=pd.to_numeric(dpts_count['cod_dpto'])
dpts_count['cod_dpto']=dpts_count['cod_dpto'].astype(int).apply(lambda x: '{0:0>2}'.format(x))

#mapa = requests.get("https://mapsmicroservice-zbca65qbuq-nn.a.run.app/api/v1/maps")
#dpts_count = pd.DataFrame.from_dict(mapa.json())

####PLot by year
base_pivot = pandas_df_from_azure_query(
"""
SELECT *
FROM ICBF.tomas_pivot
"""
)

fig_years_dist = plot_by_year.ploting_distribution(base_pivot)

years = dpts_count['Año'].unique()
slider_items = {int(math.floor(years[i])):str(math.floor(years[i])) for i in range(len(years))}

"""
controlslider = html.Div([
    dcc.RangeSlider(
        id='slider-year',
        min=2017,
        max=2020,
        step=None,            # True, False - insert dots, only when step>1
        allowCross=False,
        marks=slider_items,
        value=2017,
    )
])
"""

card_map = dbc.Card(
    dbc.CardBody([
        html.H4("Malnutrition Relapse % by Department"),
        html.Hr(id="hr_1"),
        # html.Div(control_dropdown),
        html.Div(
            dcc.Graph(
                id='colombia_plot',
                figure={}
            )
        )
    ])
,color="primary", outline=True)

card_map2 = dbc.Card(
    dbc.CardBody([
        html.H4("Malnutrition % by Department"),
        html.Hr(id="hr_1"),
        html.Div(
            dcc.Graph(
                id='colombia_plot_2',
                figure={}
            )
        )
    ])
,color="primary", outline=True)

card_graph_distribution = dbc.Card(
    dbc.CardBody([
        dbc.Card([
            dbc.CardBody([
                html.H4("Malnutrition Relapse by Year", className="card-title"),
                html.Hr(id="hr_1"),
                dcc.Graph(
                    id='years_dist_plot',
                    figure=fig_years_dist
                )
            ])
        ],color="primary", outline=True)
    ])
,color="light", outline=True)

colombian_maps = dbc.Card([
    dbc.CardBody([
        dbc.Row([
            dbc.Col(
                dcc.Slider(
                    id='slider-year',
                    min=2017,
                    max=2020,
                    step=None,
                    marks=slider_items,
                    value=2017,
                ), width=12
            )
        ]),
        dbc.Row([
            dbc.Col(
                card_map2, width = 6
            ),
            dbc.Col(
                card_map, width = 6
            )
        ])
    ])
],color="light", outline=True)


layout = dbc.Container([
    dbc.Row(dbc.Col(colombian_maps, width=12), className="mb-4",),
    dbc.Row([
        dbc.Col(
            card_graph_distribution, width=12
        )
      ])
], fluid=True)


@app.callback([Output('colombia_plot', 'figure'),
              Output('colombia_plot_2', 'figure'),],
              [Input('slider-year', 'value')])
def display_maps(value):
    dpts_count_filtered = dpts_count[dpts_count['Año']==value]
    figmap_rel = mapcolombia.getfigmap(dpts_count_filtered, 'Relapse_Percentage', 'peach', colombia)
    figmap_mal = mapcolombia.getfigmap(dpts_count_filtered, 'Malnutrition_Percentage', 'emrld', colombia)
    return figmap_rel, figmap_mal
