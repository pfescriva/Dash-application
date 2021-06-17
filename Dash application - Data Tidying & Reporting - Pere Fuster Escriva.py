# -*- coding: utf-8 -*-




"""
Created on Thu Jun 17 21:04:32 2021

@author: peescriv
date: 6/17/2021

Pere Fuster Dash App

"""


import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px

from statsmodels.tsa.stattools import pacf
import plotly.graph_objects as go



## Preprocessing


# Tidying

path = 'https://raw.githubusercontent.com/pfescriva/PyDash-App/main/raw_sales.csv'
df = pd.read_csv(path)

df['Date'] = df['datesold']


# Aggregate sales (USD) by area and date
df["dateRep"] = pd.to_datetime(df["datesold"])
data = df.groupby(["dateRep", "postcode"])["price"].sum().reset_index()

# Obtain the series for each area 
historical_data = data.pivot_table(index=['dateRep'], columns='postcode').reset_index()
historical_data.columns = historical_data.columns.droplevel().rename(None)
historical_data.insert(0, 'dateRep', historical_data[''])
del historical_data[''] 

historical_data = historical_data.fillna(0)

historical_data

groups = historical_data.columns[1:]


# Satistical Application: Seasonal Autoregressive Model


from statsmodels.tsa.statespace.sarimax import SARIMAX

gv_forecasts = pd.DataFrame()

for j in list(historical_data.columns[1:]): 
    
    model = SARIMAX(historical_data[j], order = (0, 0, 0), seasonal_order = (3, 0, 0, 7))
    
    model_fit = model.fit()
    
    yhat = model_fit.forecast(steps = 30)

    gv_forecasts[j] = yhat
	
	print(j)


gv_forecasts.values[gv_forecasts.values < 0] = 0

gv_forecasts.insert(0, 'Date', pd.date_range(start = max(historical_data['dateRep']) + pd.DateOffset(days = 1), end = max(historical_data['dateRep']) + pd.DateOffset(days = 30))) 




# Dash App

app = dash.Dash(
  external_stylesheets = [dbc.themes.SUPERHERO]
)

part1 = html.Div([
    dcc.Dropdown(
        id="ticker1",
        options=[{"label": x, "value": x} 
                 for x in historical_data.columns[1:]],
        value=historical_data.columns[1],
        clearable=False,
    ),
    dcc.Graph(id="time-series-chart1"),
])

@app.callback(
    Output("time-series-chart1", "figure"), 
    [Input("ticker1", "value")])
def display_time_series(ticker):
    fig = px.line(historical_data, x='dateRep', y=ticker)
    return fig

  
part2 = html.Div([
    dcc.Dropdown(
        id="ticker",
        options=[{"label": x, "value": x} 
                 for x in historical_data.columns[1:]],
        value=historical_data.columns[1],
        clearable=False,
    ),
    dcc.Graph(id="PACF"),
])

@app.callback(
    Output("PACF", "figure"), 
    [Input("ticker", "value")])
def display_time_series(ticker):
    df_pacf = pacf(historical_data[2600], nlags=100)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x= np.arange(len(df_pacf)),y= df_pacf,name= 'PACF'))
    fig.update_xaxes(rangeslider_visible=True)
    fig.update_layout(title="Partial Autocorrelation",xaxis_title="Lag", yaxis_title="Partial Autocorrelation", height=500)
    return fig


part3 = html.Div([
    dcc.Dropdown(
        id="ticker2",
        options=[{"label": x, "value": x} 
                 for x in gv_forecasts.columns[1:]],
        value=gv_forecasts.columns[1],
        clearable=False,
    ),
    dcc.Graph(id="time-series-chart2"),
])
                      
@app.callback(
    Output("time-series-chart2", "figure"), 
    [Input("ticker2", "value")])
def display_time_series(ticker):
    fig = px.line(gv_forecasts, x='Date', y=ticker)
    return fig
  


SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#092745"
}

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem"
}

sidebar = html.Div(
    [
        html.H2("House Sales US", className="display-4"),
        html.Hr(),
        html.P(
            "Data Tidying and reporting", className="lead"
        ),
        dbc.Nav(
            [
                dbc.NavLink("Home", href="/", active="exact"),
                dbc.NavLink("Analyse", href="/Analyse", active="exact"),
                dbc.NavLink("Predict", href="/Predict", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE
)


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/":
      return part1
    elif pathname == "/Analyse":
        return part2
    elif pathname == "/Predict":
        return part3
    # If the user tries to reach a different page, return a 404 message
    return dbc.Jumbotron(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ]
    )


# Define the layout of the app. It is kind of the html
content = html.Div(id="page-content", style=CONTENT_STYLE)

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])



if __name__ == "__main__":
  app.run_server()





