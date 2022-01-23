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
driver= '{ODBC Driver 17 for SQL Server}'

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
df_target1_relapse = pandas_df_from_azure_query(
"""
SELECT *
FROM base_target_2018
WHERE Marca_Target_Reincidencia_F6M == 1
"""
)

#Se filtran beneficiarios cuyo target de desnutrición para los próximos 6 meses sea 1
df_target1_mal = pandas_df_from_azure_query(
"""
SELECT *
FROM base_target_2018
WHERE Marca_Target_EntroEnDesnutricion_F6M == 1
"""
)

#Se agrupan los target de relapse por dpto para obtener el count
dpts_count_target1_relapse = pandas_df_from_azure_query(
"""
SELECT cod_dpto, nom_dpto, COUNT(0) AS Count_Dpto_Relapse
FROM df_target1_relapse
GROUP BY 1,2
ORDER BY 1,2
"""
)

#Se agrupan los target de malnutrition por dpto para obtener el count
dpts_count_target1_mal = pandas_df_from_azure_query(
"""
SELECT cod_dpto, nom_dpto, COUNT(0) AS Count_Dpto_Malnutrition
FROM df_target1_mal
GROUP BY 1,2
ORDER BY 1,2
"""
)

#Se agrupan el count total de registros suministrados por dpto
dpts_count_total = pandas_df_from_azure_query(
"""
SELECT cod_dpto, nom_dpto, COUNT(0) AS Count_Dpto_Total
FROM base_target_2018
GROUP BY 1,2
ORDER BY 1,2
"""
)

#Se unen los 3 dfs creados anteriormente
df_complete = pandas_df_from_azure_query(
"""
SELECT * FROM dpts_count_target1_relapse UNION ALL
SELECT * FROM dpts_count_target1_mal UNION ALL
SELECT * FROM dpts_count_total
"""
)

#Se crea una columna con el ratio entre count relapse y total por dept
dpts_count = pandas_df_from_azure_query(
"""
SELECT CAST(cod_dpto AS INT), nom_dpto, Count_Dpto_Total, Count_Dpto_Malnutrition, Count_Dpto_Relapse,
  Count_Dpto_Relapse/Count_Dpto_Total AS count_ratio_relapse,
  Count_Dpto_Malnutrition/Count_Dpto_Total AS count_ratio_mal
FROM df_complete
"""
)


#mapa = requests.get("https://mapsmicroservice-zbca65qbuq-nn.a.run.app/api/v1/maps")
#dpts_count = pd.DataFrame.from_dict(mapa.json())

####PLot by year
base_pivot = pandas_df_from_azure_query(
"""
SELECT *
FROM tomas_pivot
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
