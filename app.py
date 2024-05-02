# Import packages
from dash import Dash, html, dash_table, dcc, callback, Input, Output, State, ctx, no_update
from datetime import date
from lifelines.datasets import load_waltons
from lifelines import KaplanMeierFitter
from json import JSONEncoder
import dash_daq as daq
import numpy
import plotly.graph_objs as go
import oracledb
import os
from lifelines.utils import datetimes_to_durations
import local_settings
import strain_dropdown
import locations
import licenses
import pandas as pd
import redis
import json 
import uuid
import datetime
from datetime import date
import logging
import sys
from logging.handlers import RotatingFileHandler

#
logger = logging.getLogger('my_logger')
handler = RotatingFileHandler('dash.log', maxBytes=1000000, backupCount=1)
logger.addHandler(handler)
#handler.setLevel(logging.WARNING)
handler.setLevel(logging.ERROR)
new = 1

# select dateofbirth, dayofdeath from vanimal WHERE SPECIESID = 40291147 
# AND DATEOFBIRTH < TO_DATE('2021-01-01','YYYY-MM-DD') 
# AND DAYOFDEATH > TO_DATE('2021-01-01','YYYY-MM-DD') 
# fetch first 4 rows only;


#picture = x.get_figure().savefig("plot.png")

#https://pynative.com/python-serialize-numpy-ndarray-into-json/
class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, numpy.ndarray):
            return obj.tolist()
        if isinstance(obj, (datetime.date, datetime.datetime)):
                return obj.isoformat()
        return JSONEncoder.default(self, obj)


# Initialize the app
app = Dash(__name__)

canvas_width = 500
# App layout
# https://www.crosstab.io/articles/survival-plots/
#fig = go.Figure()
#fig.add_trace(go.Scatter(
#    x=kmf.survival_function_.index, y=kmf.survival_function_['KM_estimate'],
#    line=dict(shape='hv', width=3, color='rgb(31, 119, 180)'),
#    showlegend=False
#))
server = app.server
app.scripts.config.serve_locally = True
app.css.config.serve_locally = True
app.server.logger.addHandler(handler)
fish_filter=1


def description_card():
    """

    :return: A Div containing dashboard title & descriptions.
    """
    return html.Div(
        id="description-card",
        children=[
            html.H5("Fish Lifelines - Kaplan Meier Curve"),
            html.H3("Create Lifelines From The Tick@lab Database"),
            html.Div(
                id="intro",
                children="An webapp developed at the Leibniz Institute on Aging - Fritz Lipmann Institute (FLI)",
            ),
        ],
    )


def generate_control_card():
    """
    :return: A Div containing controls / filter for graphs.
    """
    return html.Div(id="control-card",
        children=[
            html.H3('Strain', style={'font-family': 'Source Sans Pro'}),
            dcc.Dropdown(
                options=strain_dropdown.strain_data,
                value='00000000',
                id='strain'),
            html.H3('Criteria', style={'font-family': 'Source Sans Pro'}),
            dcc.Dropdown(
                [
                    {
                        "label":'Alle / All',
                        "value":'0'
                    }, 
                    {
                        "label":'Abbruchkriterium erreicht / Humane endpoint',
                        "value":'170, 177'
                    }, 
                    {
                        "label":'Tot aufgefunden / Found dead',
                        "value":'171,175'
                    },
                    {
                        "label":'Gesundheitskontrolle / Health Monitoring',
                        "value":'173'
                    },
                    {
                        "label":'Falsches Geschlecht / Wrong sex',
                        "value":'192'
                    },
                    {
                        "label":'Hygienerisiko / Hygiene risk',
                        "value":'195'
                    },
                    {
                        "label":'Nicht geeignet für die Zucht / Not suitable for breeding',
                        "value":'199,200'
                    },
                    {
                        "label":'Genetische Sanierung / Genetic sanitation',
                        "value":'201'
                    },
                    {
                        "label":'Hygienische Sanierung / Hygienic sanitation',
                        "value":'198'
                    },
                    {
                        "label":'Zu alt für die Zucht / Exbreeder',
                        "value":'185'
                    },
                    {
                        "label":'Falscher Genotyp / Wrong genotype',
                        "value":'187,188'
                    },
                    {
                        "label":'Organentnahme / Organ removal',
                        "value":'190,191'
                    },
                    {
                        "label":'Hygienerisiko / Hygiene risk',
                        "value":'186'
                    },
                    {
                        "label":'Ende Experiment / End Experiment',
                        "value":'189'
                    },
                ], 
                value =["0"], 
                multi=True,
                id='exitreason'
            ),
            html.H3('Censored Criteria', style={'font-family': 'Source Sans Pro'}),
            html.Span('Censored criteria have to be a subset from the criteria above', style={'font-family': 'Source Sans Pro'}),
            dcc.Dropdown(
                [
                    {
                        "label":'Alle / All',
                        "value":'0'
                    }, 
                    {
                        "label":'Abbruchkriterium erreicht / Humane endpoint',
                        "value":'170'
                    }, 
                    {
                        "label":'Tot aufgefunden / Found dead',
                        "value":'171,175'
                    },
                    {
                        "label":'Gesundheitskontrolle / Health Monitoring',
                        "value":'173'
                    },
                    {
                        "label":'Falsches Geschlecht / Wrong sex',
                        "value":'192'
                    },
                    {
                        "label":'Hygienerisiko / Hygiene risk',
                        "value":'195'
                    },
                    {
                        "label":'Nicht geeignet für die Zucht / Not suitable for breeding',
                        "value":'199,200'
                    },
                    {
                        "label":'Genetische Sanierung / Genetic sanitation',
                        "value":'201'
                    },
                    {
                        "label":'Hygienische Sanierung / Hygienic sanitation',
                        "value":'198'
                    },
                    {
                        "label":'Zu alt für die Zucht / Exbreeder',
                        "value":'185'
                    },
                    {
                        "label":'Abbruchkriterium erreicht / Humane endpoint',
                        "value":'177'
                    },
                    {
                        "label":'Falscher Genotyp / Wrong genotype',
                        "value":'187,188'
                    },
                    {
                        "label":'Organentnahme / Organ removal',
                        "value":'190,191'
                    },
                    {
                        "label":'Hygienerisiko / Hygiene risk',
                        "value":'186'
                    },
                    {
                        "label":'Ende Experiment / End Experiment',
                        "value":'189'
                    },
                ], 
                value =[], 
                multi=True,
                id='exitcensored'
            ),
            html.H3('Date range date of birth', style={'font-family': 'Source Sans Pro'}),
            dcc.DatePickerRange(
                id='date-picker-range',
                display_format='D-M-Y',
                min_date_allowed=date(1995, 1, 1),
                max_date_allowed=date(9999, 12, 21),
                initial_visible_month=date(2023, 8, 24),
                start_date=date(2022, 1, 1),
                end_date=date.today()
            ),
            html.H3('Sex', style={'font-family': 'Source Sans Pro'}),    
            dcc.Checklist(
                options={'0': 'unknown', '1': 'male', '2': 'female'}, value=['0', '1', '2'], inline=True, id='sex'),
            html.H3('Include animals used in previous experiments?', style={'font-family': 'Source Sans Pro'}),
            dcc.Checklist(['True'], ['True'], id='isused'),
            html.H3('Locations', style={'font-family': 'Source Sans Pro'}),
            dcc.Dropdown(
                options=locations.locations,
                value=['All'],
                multi=True,
                id='locations'),
            html.H3('License', style={'font-family': 'Source Sans Pro'}),
            dcc.Dropdown(
                options=licenses.licenses,
                value=['All'],
                multi=True,
                id='licenses'),
            html.H3('Genotype', style={'font-family': 'Source Sans Pro'}),
            dcc.Input(id="genotype", type="text", placeholder="",debounce=True,inputMode ='full-width-latin',style={'font-family': 'Source Sans Pro','width':'25em'},value=""),
            html.I(' Enter exact genotype as you can see in the table at the bottom seperated by semicolon', style={'font-family': 'Source Sans Pro'},),
            html.H3('Outlier', style={'font-family': 'Source Sans Pro'}),
            dcc.Input(id="outlier", type="text", placeholder="",debounce=True,inputMode ='full-width-latin',style={'font-family': 'Source Sans Pro','width':'25em'},value=""),
            html.I(' Enter IDs from outlier you want to exclude seperated by semicolon wihtout space (e.g.010140;010138/001//OTC)', style={'font-family': 'Source Sans Pro'},),
        ],
    )

app.layout = html.Div(
    id="app-container",
    children=[
        # Left column
        html.Div(
            id="left-column",
            className="four columns",
            children=[description_card(), generate_control_card()]
            + [
                html.Div(
                    ["initial child"], id="output-clientside", style={"display": "none"}
                )
            ],
        ),
        html.Div(
            id="right-column",
            className="eight columns",
            children=[
                html.H3('Graph', style={'font-family': 'Source Sans Pro'},),
                
                #dcc.Graph(figure=fig)
                dcc.Graph(id='plot'),
                html.Br(),
                html.Br(),
                html.H3('Selected Strain', style={'font-family': 'Source Sans Pro'}),
                dcc.Dropdown(
                    options={'00000000': 'new',},
                    value='00000000',
                    id='plotline'),
                html.Br(),
                html.Button('Add new strain', id='btn-new-plot', n_clicks=0),
                html.Button('Delete strain', id='btn-delete-plot', n_clicks=0, style={'margin-left':'50px'}),
                html.Br(),
                html.H3('Color Line', style={'font-family': 'Source Sans Pro'}),
                daq.ColorPicker(id='color_picker', size = 190, value=dict(hex='#119DFF')), #https://dash.plotly.com/dash-daq/colorpicker
                html.H3('Individual Legend Text', style={'font-family': 'Source Sans Pro'}),
                dcc.Input(id="line_legend_text", type="text", placeholder="",debounce=True,inputMode ='full-width-latin',style={'font-family': 'Source Sans Pro','width':'25em'},value=""),
                html.Br(),
                html.Br(),
                html.Br(),
                html.Br(),
                html.Br(),
                html.Br(),
                html.Br(),
                html.Br(),
                html.Br(),
                html.Br(),
                html.Br(),
                html.Br(),

            ],
        ),
        html.Footer(
            className="footer",
            children=[
                html.Hr(),
                html.H3('Data', style={'font-family': 'Source Sans Pro'}),
                dash_table.DataTable(id='table', page_size=10,export_format="xlsx"),
                html.Br(),
                html.H3('Statistic', style={'font-family': 'Source Sans Pro'}),
                dash_table.DataTable(id='statistic_data', page_size=10,export_format="xlsx"),
                html.Br(),
                html.Hr(),

                html.Table([
                    html.Tbody([
                        html.Tr([
                            html.Td(html.H3("Version: 1.0", style={'text-align':'left', 'font-family': 'sans-serif', 'font-size':'15px', 'margin-left':'10px'}), style={'width':'40%'}),
                            html.Td(html.Img(src='assets/logo.png', style={'height': '100px', 'width': '100px', 'margin': '0 auto'}), style={'text-align': 'center', 'width':'20%'}),
                            html.Td(html.H3('by Beate Hoppe, Uta Naumann, Joana Langer, Fabian Monheim', style={'text-align':'right', 'font-family': 'sans-serif', 'font-size':'15px', 'margin-right':'10px'}), style={'width':'40%'}),
                        ]),
                    ]),
                ], style={'width': '100%'}),
                
                html.Span('', id='session-id', hidden=True, title=''),
                html.Span('', id='new_strain_info', hidden=True, title='0'),
            ],
        ),

    ]
)

"""
Initiale Funktion zum Setzen der Session ID
"""

@callback(
    Output(component_id='session-id', component_property='title'),
    Input(component_id='session-id', component_property='title'),
)
def initial_set_sessionid(session_id):
    if ctx.triggered[0]['value']:
        return no_update
    else:
        session_id = str(uuid.uuid4())
        jsonlist = {
            "session_id":session_id,
            "lines" : [
                {
                    "strain"        :'',
                    "isused"        :[],
                    "startdate"     :'',
                    "enddate"       :'',
                    "sex"           :[],
                    "exitreasonlist":[],
                    "exitcensored"  :[],
                    "locationlist"  :[],
                    "licenselist"   :[],
                    "genotype"      :'',
                    "outlier"       :'',
                }
            ]
        }
        x = json.dumps(jsonlist)
        redis_instance = redis.StrictRedis.from_url(os.environ.get("REDIS_URL", "redis://127.0.0.1:6379"))
        redis_instance.hset("data", session_id, x)
        return session_id

"""
Wird ausgeführt, wenn der Nutzer in der linken Seite das Feld Strain aktualisiert. Daraufhin wird auch der Wert in dem Feld Selected Strain akualisiert. 
Sofern vorher die Option new aktiv war, wird diese durch die neue Auswahl aktualsiert
"""
@callback(
    Output(component_id='plotline',component_property='options',allow_duplicate=True),
    Output(component_id='plotline',component_property='value', allow_duplicate=True),
    Output(component_id='new_strain_info', component_property='title', allow_duplicate=True),
    Input(component_id='strain', component_property='value'),
    State(component_id='plotline',component_property='options'),
    State(component_id='plotline',component_property='value'),
    State(component_id='session-id', component_property='title'),
    State(component_id='new_strain_info', component_property='title'),
    prevent_initial_call=True
)
def update_strain(strain,options, plotline_value,session_id,new_strain_info):
    try:
        if strain == "00000000":
            logger.warning('update_strain: no update')
            return no_update
        if options.get("00000000",False):   # Wenn bisher new aktiv war
            #print("pop new")
            options.pop('00000000')
            logger.warning('update_strain: pop new from plotline')
            #options[strain] = strain_dropdown.strain_data[strain]
            
            keysList = list(options.keys())
            strain_id_exist = 1
            strain_id = ""
            i = 0
            while strain_id_exist == 1: 
                strain_id = "{}-{}".format(strain,i)
                if strain_id in keysList:
                    i += 1
                    strain_id_exist = 1
                else:
                    strain_id_exist = 0
            options[strain_id] = strain_dropdown.strain_data[strain] 
            #print(options)
            new_strain_info = "1" 
        else:  
            #try:  # Falls der Nutzer unter selected strain auf einen bereits bestehenden zurück springt, soll nichts geändert werden
            #    if options[strain] == strain_dropdown.strain_data[strain]:  
            #        return options, strain, "0"  
            #except:
            #    pass
            logger.warning('update_strain: new_strain_info = 0')
            new_strain_info = "0"
            options.pop(plotline_value) # Entferne bisherien Strain und aktualisiere ihn mit dem Wert aus dem Feld Strain von der linken Seite
            keysList = list(options.keys())
            strain_id_exist = 1
            strain_id = ""
            i = 0
            while strain_id_exist == 1: 
                strain_id = "{}-{}".format(strain,i)
                if strain_id in keysList:
                    i += 1
                    strain_id_exist = 1
                else:
                    strain_id_exist = 0
            options[strain_id] = strain_dropdown.strain_data[strain]
            redis_instance = redis.StrictRedis.from_url(os.environ.get("REDIS_URL", "redis://127.0.0.1:6379"))
            var_session = json.loads(redis_instance.hget("data", session_id)) # hole die bisher gespeicherten Filterwerte zu der Session
            #print(var_session)
            for i in range(0,len(var_session['lines'])): # Falls eine bereits gespeicherter Datensatz verändert wurde
                if var_session['lines'][i]["strain_id"] == plotline_value: # Suche den passenden Datensatz
                    var_session['lines'][i]["strain_id"] = strain_id
                    var_session['lines'][i]["strain"] = strain
                    var_session = json.dumps(var_session, cls=NumpyArrayEncoder)
                    redis_instance.hset("data", session_id, var_session)
        #print("options: {}, strain: {}, new_strain_info: {}".format(options, strain_id, new_strain_info))
        return options, strain_id, new_strain_info
    except BaseException as e:
        logger.error('update_strain, error {}'.format(e))
        return no_update

"""
Wird ausgeführt, wenn der Nutzer in der rechten Seite das Feld Selected Strain aktualisiert. 
"""
@callback(
    Output(component_id='strain',component_property='value',allow_duplicate=True),
    Output(component_id='isused', component_property='value',allow_duplicate=True),
    Output(component_id='date-picker-range', component_property='start_date', allow_duplicate=True),
    Output(component_id='date-picker-range', component_property='end_date', allow_duplicate=True),
    Output(component_id='sex', component_property='value', allow_duplicate=True),
    Output(component_id='exitreason', component_property='value', allow_duplicate=True),
    Output(component_id='exitcensored', component_property='value', allow_duplicate=True),
    Output(component_id='locations', component_property='value', allow_duplicate=True),
    Output(component_id='licenses', component_property='value', allow_duplicate=True),
    Output(component_id='genotype', component_property='value', allow_duplicate=True),
    Output(component_id='outlier', component_property='value', allow_duplicate=True),
    Output(component_id='color_picker', component_property='value', allow_duplicate=True),
    Output(component_id='line_legend_text', component_property='value', allow_duplicate=True),
    Output(component_id='table', component_property='data', allow_duplicate=True),
    Output(component_id='statistic_data', component_property='data', allow_duplicate=True),
    Input(component_id='plotline', component_property='value'),
    State(component_id='session-id', component_property='title'),
    prevent_initial_call=True
)
def update_plotline(plotline_value,session_id):
    try:
        if plotline_value == '00000000':
            logger.warning('update_plotline: no_update')
            return no_update
        redis_instance = redis.StrictRedis.from_url(os.environ.get("REDIS_URL", "redis://127.0.0.1:6379"))
        var_session = json.loads(redis_instance.hget("data", session_id)) # hole die bisher gespeicherten Filterwerte zu der Session
        #print("update_plotline",var_session)
        logger.warning('update_plotline: {}, len(session) {}:'.format(session_id, len(var_session['lines'])))
        for i in range(0,len(var_session['lines'])): # Falls eine bereits gespeicherter Datensatz verändert wurde
                if var_session['lines'][i]["strain_id"] == plotline_value: # Suche den passenden Datensatz
                    filter_values   = var_session['lines'][i]
                    isused          = filter_values['isused']
                    start_date      = filter_values['startdate']
                    end_date        = filter_values['enddate']
                    sex             = filter_values['sex']
                    exitreason      = filter_values['exitreasonlist']
                    exitcensored    = filter_values['exitcensored']
                    locations       = filter_values['locationlist']
                    licenses        = filter_values['licenselist']
                    genotype        = filter_values['genotype']
                    outlier         = filter_values['outlier']
                    color           = dict(hex=filter_values['color'])
                    legend_text     = filter_values['legend_text']
                    result_dict     = filter_values['result_dict']
                    statistic_data  = filter_values['statistic_data']
                    return (plotline_value[:8],isused,start_date,end_date,sex,exitreason,exitcensored,locations,licenses,genotype,outlier,color,legend_text,result_dict,statistic_data)
        return no_update
    except BaseException as e:
        logger.error('update_plotline, error {}'.format(e))
        return no_update


"""
Wird nach dem Button "Add new Strain" ausgeführt, wodurch eine neuer Strain new erzeugt wird 

@callback(
    Output(component_id='strain', component_property='value'),
    Output(component_id='strain', component_property='options'),
    Output(component_id='plotline',component_property='options'),
    Output(component_id='plotline',component_property='value'),
    Output(component_id='new_strain_info', component_property='title',allow_duplicate=True),
    Input('btn-new-plot', 'n_clicks'),
    State(component_id='strain', component_property='options'),
    State(component_id='plotline', component_property='options'),
    prevent_initial_call=True
)
def new_plot(clicks1, strain_options, plotline_options):
    try:
        if "btn-new-plot" == ctx.triggered_id:
            logger.warning('new_plot')
            strain_options["00000000"]="new"
            plotline_options["00000000"]="new"
            return("00000000",strain_options, plotline_options,"00000000",'1')
    except BaseException as e:
        logger.warning('new_plot, error {}'.format(e))
        return no_update
"""

"""
Wird nach dem Button "Add new Strain" ausgeführt, wodurch die Filter zurückgesetzt werden 
"""
@callback(
    Output(component_id='isused', component_property='value'),
    Output(component_id='date-picker-range', component_property='start_date'),
    Output(component_id='date-picker-range', component_property='end_date'),
    Output(component_id='sex', component_property='value'),
    Output(component_id='exitreason', component_property='value'),
    Output(component_id='exitcensored', component_property='value'),
    Output(component_id='locations', component_property='value'),
    Output(component_id='licenses', component_property='value'),
    Output(component_id='genotype', component_property='value'),
    Output(component_id='outlier', component_property='value'),
    Output(component_id='color_picker', component_property='value'),
    Output(component_id='line_legend_text', component_property='value'),
    Output(component_id='strain', component_property='value'),
    Output(component_id='strain', component_property='options'),
    Output(component_id='plotline',component_property='options'),
    Output(component_id='plotline',component_property='value'),
    Output(component_id='new_strain_info', component_property='title',allow_duplicate=True),
    Input('btn-new-plot', 'n_clicks'),
    State(component_id='strain', component_property='options'),
    State(component_id='plotline', component_property='options'),
    prevent_initial_call=True
)
def set_default_filter(clicks1,strain_options, plotline_options):
    try:
        logger.warning('set_default_filter')
        exitreason_value          =["0"]
        censored_criteria_value =[]
        date_range_start_date   = date(2022, 2, 1)
        date_range_end_date     = date.today()
        sex_value               = ['0', '1', '2']
        isused_value            = ['True']
        locations_value         = ['All']
        licenses_value       = ['All']
        genotype_value          = ""
        outlier_value           = ""
        color                   = dict(hex='#119DFF')
        line_legend_text        = ""
        strain_options["00000000"]="new"
        plotline_options["00000000"]="new"
        return (isused_value,date_range_start_date,date_range_end_date,sex_value,exitreason_value,censored_criteria_value,locations_value,licenses_value,genotype_value,outlier_value,color,line_legend_text,"00000000",strain_options, plotline_options,"00000000",'1')
    except BaseException as e:
        logger.error('set_default_filter, error {}'.format(e))
        return no_update




        

"""
Wird nach dem Button "Delete Strain" ausgeführt, wodurch der Plot der aktuellen Auswahl im Feld Selected Strain gelöscht wird
"""
@callback(
    Output(component_id='plotline',component_property='options',allow_duplicate=True),
    Output(component_id='plotline',component_property='value',allow_duplicate=True),
    Output(component_id='strain', component_property='value',allow_duplicate=True),
    Input('btn-delete-plot', 'n_clicks'),
    State(component_id='plotline',component_property='options'),
    State(component_id='plotline',component_property='value'),
    State(component_id='session-id', component_property='title'),
    prevent_initial_call=True
)
def delete_plot(clicks1,plotline_options, plotline_value, session_id):
    try:
        if "btn-delete-plot" == ctx.triggered_id:
            
            redis_instance = redis.StrictRedis.from_url(os.environ.get("REDIS_URL", "redis://127.0.0.1:6379"))
            var_session = json.loads(redis_instance.hget("data", session_id)) # hole die bisher gespeicherten Filterwerte zu der Session
            for i in range(0,len(var_session['lines'])): # Falls eine bereits gespeicherter Datensatz verändert wurde
                if var_session['lines'][i]["strain_id"] == plotline_value: # Suche den passenden Datensatz
                    var_session['lines'].pop(i)
                    var_session = json.dumps(var_session)
                    redis_instance.hset("data", session_id, var_session)
                    break

            plotline_options.pop(plotline_value)
            plotline_last_key = list(plotline_options)[-1]
            return(plotline_options, plotline_last_key, plotline_last_key)
    except BaseException as e:
        logger.error('delete_plot, error {}'.format(e))
        return no_update
    


"""
Erstellt den Plot neu, wenn etwas am Layout angepasst wurde
"""
@callback(
    Output(component_id='plot', component_property='figure'),
    Output(component_id='plotline', component_property='options', allow_duplicate=True),
    Input(component_id='color_picker', component_property='value'),
    Input(component_id='line_legend_text', component_property='value'),
    State(component_id='session-id', component_property='title'),
    State(component_id='strain', component_property='value'),
    State(component_id='plotline', component_property='value'),
    State(component_id='plotline', component_property='options'),
    prevent_initial_call=True
)
def update_graphic_style(color,legend_text,session_id, strain, plotline_value, plotline_options):
    try:
        redis_instance = redis.StrictRedis.from_url(os.environ.get("REDIS_URL", "redis://127.0.0.1:6379"))
        var_session = json.loads(redis_instance.hget("data", session_id)) 
        logger.warning('update_graphic_style: {}, len(session) {}:'.format(session_id, len(var_session['lines'])))
        for i in range(0,len(var_session['lines'])): # Falls eine bereits gespeicherter Datensatz verändert wurde
            if var_session['lines'][i]["strain_id"] == plotline_value and var_session['lines'][i]["print"] == 1: # Suche den passenden Datensatz und schaue ob auch Datensätze vorliegen
                var_session['lines'][i]["color"] = color["hex"]
                var_session['lines'][i]["legend_text"] = legend_text
                break
        var_session = json.dumps(var_session, cls=NumpyArrayEncoder)
        redis_instance.hset("data", session_id, var_session)
        fig, median_survival = update_graphic(session_id, redis_instance)

        if legend_text != "":
            plotline_options[plotline_value] = legend_text
        return fig, plotline_options
    except BaseException as e:
        logger.error('update_graphic_style, error {}'.format(e))
        return no_update





"""
Erstellt den Plot aus den Werten aus der Datenbank passend zur Session
"""
def update_graphic(session_id, redis_instance):
    try:
        var_session = json.loads(redis_instance.hget("data", session_id)) # hole die bisher gespeicherten Filterwerte zu der Session 
        #print("update_graphic",len(var_session['lines']))
        logger.warning('update_graphic: {}, len(session) {}:'.format(session_id, len(var_session['lines'])))
        fig = go.Figure()
        kmf = KaplanMeierFitter(alpha=0.05)
        i = 0
        showalphainlegend = True
        median_survival = []
        for line in var_session['lines']:
            if line["print"]:
                i += 1
                if i == 2:
                    showalphainlegend = False
                T = numpy.asarray(line["T"])
                E = numpy.asarray(line["E"])
                kmf.fit(T, event_observed=E)  # or, more succinctly, kmf.fit(T, E)
                kmf.survival_function_
                median_survival.append(kmf.median_survival_time_)
                kmf.cumulative_density_
                x = kmf.plot_survival_function()       
                legend_text = ""
                if line["legend_text"] == "":
                    legend_text =  strain_dropdown.strain_data[line["strain"]]
                else:
                    legend_text = line["legend_text"]
                
                fig.add_trace(go.Scatter(
                    x=kmf.survival_function_.index, y=kmf.survival_function_['KM_estimate'],
                    line=dict(shape='hv', width=3, color=line["color"]),
                    showlegend=True,name=legend_text
                ))
                fig.add_trace(go.Scatter(
                    x=kmf.confidence_interval_.index, 
                    y=kmf.confidence_interval_['KM_estimate_upper_0.95'],
                    line=dict(shape='hv', width=0),
                    showlegend=False,
                ))
                fig.add_trace(go.Scatter(
                    x=kmf.confidence_interval_.index,
                    y=kmf.confidence_interval_['KM_estimate_lower_0.95'],
                    line=dict(shape='hv', width=0),
                    fill='tonexty',
                    fillcolor='rgba(31, 119, 180, 0.4)',
                    showlegend=showalphainlegend,
                    legendrank=100,
                    name="\u03B1=95{} convidence interval".format('%')
                ))
            else:
                median_survival.append(0)
        fig.update_layout(xaxis_title="Duration (Days)", yaxis_title="Survival probability")
        return fig, median_survival
    except BaseException as e:
        logger.error('update_graphic, error {}'.format(e))
        return no_update



"""
Speichert die Filter, Führt die Datenbankanfrage durch und ruft die Funktion update_graphic auf, wodurch der Plot erzeugt wird
"""
@callback(
    Output(component_id='plot', component_property='figure',allow_duplicate=True),
    Output(component_id='table', component_property='data'),
    Output(component_id='statistic_data', component_property='data'),
    Output(component_id='new_strain_info', component_property='title'),
    Input(component_id='isused', component_property='value'),
    Input(component_id='date-picker-range', component_property='start_date'),
    Input(component_id='date-picker-range', component_property='end_date'),
    Input(component_id='sex', component_property='value'),
    Input(component_id='exitreason', component_property='value'),
    Input(component_id='exitcensored', component_property='value'),
    Input(component_id='locations', component_property='value'),
    Input(component_id='licenses', component_property='value'),
    Input(component_id='genotype', component_property='value'),
    Input(component_id='outlier', component_property='value'),
    State(component_id='session-id', component_property='title'),
    State(component_id='new_strain_info', component_property='title'),
    State(component_id='strain', component_property='value'),
    State(component_id='color_picker', component_property='value'),
    State(component_id='line_legend_text', component_property='value'),
    State(component_id='plotline', component_property='value'),
    prevent_initial_call=True
)
def update_plot(isused, startdate, enddate, sex, exitreasonlist,exitcensored,locationlist,licenselist,genotype,outlier,session_id,new_strain_info, strain,color,line_legend_text, plotline):
    try:
        logger.warning('update_plot strain: {}  new_strain_info:{}'.format(strain, new_strain_info))
        #if new_strain_info == '1':
        #    logger.warning('update_plot: no_update')
        #    return no_update
        statistic_data=[]
        string_sex = '('
        for i in sex:
            string_sex = string_sex + i + ','
        string_sex = string_sex[0:-1]
        string_sex = string_sex + ')'

        exitreason =""
        if "0" not in exitreasonlist:
            exitreason = ' AND EXITREASONID in ('
            for r in exitreasonlist:
                exitreason = exitreason + r + ','
            exitreason = exitreason[0:-1]
            exitreason = exitreason + ')'

        exitcensoredlist=[]
        for r in exitcensored:
            templist = r.split(",")
            exitcensoredlist = exitcensoredlist + templist
        exitcensoredlist = [ int(x) for x in exitcensoredlist]

        locations =""
        if "All" not in locationlist:
            locations = ' AND LOCATION in ('
            for l in locationlist:
                locations = locations + '\''+l+'\''+ ','
            locations = locations[0:-1]
            locations = locations + ')'

        licenses =""
        if "All" not in licenselist:
            licenses = ' AND LICENSE in ('
            for l in licenselist:
                licenses = licenses + '\''+l+'\''+ ','
            licenses = licenses[0:-1]
            licenses = licenses + ')'

        genotype_m = genotype
        if len(genotype_m)>4:
            genotypelist = genotype.split(":")
            genotype_m = " AND MUTATION IN = ("
            for g in genotypelist:
                genotype_m = genotype_m + '\''+g+'\''+ ','
                genotype_m = genotype_m[0:-1]
                genotype_m = genotype_m + ')'
        else:
            genotype ="" 

        outlier_m = outlier
        if len(outlier_m)>4:
            outlierlist = outlier.split(";")
            outlier_m = ' AND ANIMALNUMBER NOT IN ('
            for o in outlierlist:
                outlier_m = outlier_m + '\''+o+'\''+ ','
            outlier_m = outlier_m[0:-1]
            outlier_m = outlier_m + ')'
        else:
            outlier =""
        
        numberofexperiments = 1
        if len(isused) > 0:
            numberofexperiments = 100
        with oracledb.connect(user=local_settings.un, password=local_settings.pw, dsn=local_settings.cs) as connection:  # Verbindung zur Datenbank
            with connection.cursor() as cursor:
                sql = """Select DATEOFBIRTH, DAYOFDEATH, NUMBEROFANIMALS, EXITREASONID, '0' AS CENSORED FROM FISH WHERE STRAINID = {} AND DATEOFBIRTH > TO_DATE('{}','YYYY-MM-DD') 
                    AND DATEOFBIRTH < TO_DATE('{}','YYYY-MM-DD') AND NUMBEROFEXPERIMENTS < {} AND SEX in {}{}{}{}{}{}""".format(strain,startdate,enddate, numberofexperiments, string_sex, exitreason, locations, licenses, genotype_m, outlier_m) # Speichern des SQL Befehls in einer Variable
                #print(sql)
                cursor = connection.cursor()
                cursor.execute(sql) # Ausführen des SQL Befehls
                result_list = list(cursor.fetchall()) # Speichere das Ergebnis der SQL Abfrage in  Variable

                # Füge je nach Anzahl der Tiere eines einzelnen Datensatzes (NUNBEROFANIMALS) den gleichen Datensatz der Liste hinzu
                for count, r in enumerate(result_list):
                    censored=0
                    if r[3] in exitcensoredlist:
                        censored=1      
                        result_list[count]=(r[0],r[1],1,r[3],censored)
                    if r[2]>1:
                        for j in range(1,r[2]):
                            result_list.append((r[0],r[1],1,r[3],censored))
                

                # Code to update Data Table            
                sql_data_table = """select ANIMALNUMBER AS ID, NUMBEROFANIMALS, DATEOFBIRTH, DAYOFDEATH, LICENSE, DEAD, SEX, LOCATION, MUTATION AS GENOTYPE, EXITREASON, DAYOFDEATH - DATEOFBIRTH AS AGE,
                NUMBEROFEXPERIMENTS FROM FISH WHERE STRAINID IN {} AND DATEOFBIRTH > TO_DATE('{}','YYYY-MM-DD') 
                    AND DATEOFBIRTH < TO_DATE('{}','YYYY-MM-DD') AND NUMBEROFEXPERIMENTS < {} AND SEX in {}{}{}{}{}{}""".format(strain,startdate,enddate, numberofexperiments, string_sex, exitreason,locations, licenses, genotype_m, outlier_m)
                cursor.execute(sql_data_table)
                #print(sql_data_table)
                columns = [col[0] for col in cursor.description]
                cursor.rowfactory = lambda *args: dict(zip(columns, args))
                result_dict = cursor.fetchall()
                #if len(result_dict)==0:
                #    figure = {}
                #    return figure,result_dict, statistic_data, new_strain_info
                if len(result_dict)>0:
                    for i in result_dict:
                        if i['DEAD'] == 0:
                            i['DEAD'] = "False"
                        else:
                            i['DEAD'] = "True"
                        
                        if i['SEX'] == 0:
                            i['SEX'] = 'u'
                        elif i['SEX'] == 1:
                            i['SEX'] = 'm'
                        else:
                            i['SEX'] = 'f'
                    dateofbirth_list = [i[0] for i in result_list] # Speichere nur die Spalte DATEOFBIRTH als Liste
                    dayofdeath_list = [i[1] for i in result_list] # Speichere nur die Spalte DAYOFDEATH als Liste
                    T, E = datetimes_to_durations(dateofbirth_list, dayofdeath_list) # Umwandeln der Liste für lifelines Funktion siehe https://lifelines.readthedocs.io/en/latest/Quickstart.html?highlight=kaplan#getting-data-in-the-right-format
                    
                    for count, fish in enumerate(result_list):
                        if fish[4]==1:
                            E[count]=False
                    
                    #print(line_legend_text)
                    #color = json.loads(line_legend_text)
                    strain_dict = { # speichere die aktuellen Filterwerte in einem Dictionary
                        "strain_id"     :plotline,
                        "strain"        :strain,
                        "print"         :1,
                        "isused"        :isused,
                        "startdate"     :startdate,
                        "enddate"       :enddate,
                        "sex"           :sex,
                        "exitreasonlist":exitreasonlist,
                        "exitcensored"  :exitcensored,
                        "locationlist"  :locationlist,
                        "licenselist"   :licenselist,
                        "genotype"      :genotype,
                        "outlier"       :outlier,
                        "color"         :color.get('hex'),
                        "legend_text"   :line_legend_text,
                        "T"             :T,
                        "E"             :E,
                        "result_dict"   :result_dict,
                        "statistic_data":"",
                    }
                else:
                    strain_dict = { # speichere die aktuellen Filterwerte in einem Dictionary
                        "strain_id"     :plotline,
                        "strain"        :strain,
                        "print"         :0,
                        "isused"        :isused,
                        "startdate"     :startdate,
                        "enddate"       :enddate,
                        "sex"           :sex,
                        "exitreasonlist":exitreasonlist,
                        "exitcensored"  :exitcensored,
                        "locationlist"  :locationlist,
                        "licenselist"   :licenselist,
                        "genotype"      :genotype,
                        "outlier"       :outlier,
                        "color"         :color.get('hex'),
                        "legend_text"   :line_legend_text,
                        "statistic_data":"",
                    }

                #print(strain_dict)
                redis_instance = redis.StrictRedis.from_url(os.environ.get("REDIS_URL", "redis://127.0.0.1:6379"))
                var_session = json.loads(redis_instance.hget("data", session_id)) # hole die bisher gespeicherten Filterwerte zu der Session 
                #print("update_plot",len(var_session))
                logger.warning('update_plot1: {}, len(session) {}:'.format(session_id, len(var_session['lines'])))
                index_var_session_lines = 0
                if var_session['lines'][0]["strain"]=="":   # Wenn bisher noch keine Werte gespeichert wurden
                    var_session['lines'][0] = strain_dict
                    logger.warning('update_plot: bisher wurden noch keine Werte gespeichert')
                elif new_strain_info == '1':                # Wenn der Nutzer einen neuen Datensatz zugefügt hat bzw. auf vorher auf den Button Add new Strain geklickt hat
                    var_session['lines'].append(strain_dict) # Füge neuen Datensatz hinzu
                    index_var_session_lines = len(var_session['lines'])-1
                    new_strain_info = "0"
                    logger.warning('update_plot: new_strain_info == 1')
                else:
                    logger.warning('update_plot1-2: ein bereits gespeicherter Datensatz wurde verändert')
                    for i in range(0,len(var_session['lines'])): # Falls eine bereits gespeicherter Datensatz verändert wurde
                        logger.warning('update_plot: ein bereits gespeicherter Datensatz wurde verändert')
                        if var_session['lines'][i]["strain_id"] == plotline: # Suche den passenden Datensatz
                            var_session['lines'][i] = strain_dict # Überschreibe den Datensatz mit den angepassten Werten
                            index_var_session_lines = i
                            break
                logger.warning('update_plot2: {}, len(session) {}:'.format(session_id, len(var_session['lines'])))
                var_session = json.dumps(var_session, cls=NumpyArrayEncoder)
                redis_instance.hset("data", session_id, var_session)

        fig, median_survival = update_graphic(session_id, redis_instance)
        """
        kmf = KaplanMeierFitter(alpha=0.05)
        kmf.fit(T, event_observed=E)  # or, more succinctly, kmf.fit(T, E)
        kmf.survival_function_
        median_survival =  kmf.median_survival_time_
        kmf.cumulative_density_
        x = kmf.plot_survival_function()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=kmf.survival_function_.index, y=kmf.survival_function_['KM_estimate'],
            line=dict(shape='hv', width=3, color='rgb(31, 119, 180)'),
            showlegend=True,name=strain_dropdown.strain_data[strain]
        ))
        fig.add_trace(go.Scatter(
            x=kmf.confidence_interval_.index, 
            y=kmf.confidence_interval_['KM_estimate_upper_0.95'],
            line=dict(shape='hv', width=0),
            showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=kmf.confidence_interval_.index,
            y=kmf.confidence_interval_['KM_estimate_lower_0.95'],
            line=dict(shape='hv', width=0),
            fill='tonexty',
            fillcolor='rgba(31, 119, 180, 0.4)',
            showlegend=False
        ))
        fig.update_layout(xaxis_title="Duration (Days)", yaxis_title="Survival probability")
        """        
        #fig.update_layout(xaxis_title="Duration (Days)", yaxis_title="Survival probability", margin=dict(r=0, t=10, l=0),font_size=14,xaxis_title_font_size=18, yaxis_title_font_size=18)

        number_animals = 0
        number_events = 0
        for i in result_list:  # zensiert Tiere sind Tiere ohne Abbruchdatum oder Tiere mit ein Abbruchkriterium haben, welches explizit als zensiert eingehen soll.
            number_animals += 1
            if i[1]:
                number_events +=1 
            if i[4]==1:
                number_events -=1
        statistic_data=[]
        if len(result_dict)>0:
            dataset = {"Graph":strain_dropdown.strain_data[strain],"Number of animals":number_animals,"# censored subjects:":number_animals - number_events, "# death/events":number_events,"Median survival (days)":median_survival[index_var_session_lines]}
            statistic_data.append(dataset)
            var_session = json.loads(redis_instance.hget("data", session_id))
            #print("update_plot",len(var_session))
            logger.warning('update_plot3: {}, len(session) {}:'.format(session_id, len(var_session['lines'])))
            var_session['lines'][index_var_session_lines]["statistic_data"] = statistic_data
            var_session = json.dumps(var_session, cls=NumpyArrayEncoder)
            redis_instance.hset("data", session_id, var_session)
        new_strain_info = "0"
        return fig,result_dict,statistic_data, new_strain_info
    except BaseException as e:
        logger.error('error: {} in procedure {} in line {} '.format(e,'update_plot',sys.exc_info()[2].tb_lineno))
        return no_update


if __name__ == '__main__':
    app.run_server(debug=True,port='8050')
    app.server.logger.addHandler(handler)

# Run the app
#if __name__ == '__main__':
#    app.run(debug=True)

