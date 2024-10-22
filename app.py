#IMPORTS
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input,Output
from dash import dash_table
import io
import requests
from datetime import datetime, timedelta, date


# sheet_id = "1K5W7XFm7JVIG9d7j6RuK37AaH-0h6mNRH0fTUhKyo58”
# sheet_name = "Data”
# url = f”https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

url='https://raw.githubusercontent.com/DuaneIndustries/WestchesterRecycling/refs/heads/main/WestchesterCounty_v2.csv'
s=requests.get(url).content
df=pd.read_csv(io.StringIO(s.decode('utf-8')))

# df = pd.read_csv("/Users/caseyleo/Desktop/Colonial_Coffee_Gantt_3.csv")



df['Start Date'] = pd.to_datetime(df['Start Date'], format="%m/%d/%y")
df['End Date'] = pd.to_datetime(df['End Date'], format="%m/%d/%y")
df['Start Date'] = df['Start Date'].dt.normalize()
df['End Date'] = df['End Date'].dt.normalize()
df['Completion PCT'] = df['Completion PCT'].str.replace("%","").astype(float)

df = df.sort_values(by='Start Date',ascending=False)

dff = df

# Determine the start of each week
start_dates = pd.date_range(start='2024-02-16', end='2024-04-26', freq='W-MON')

# Create a DataFrame with start dates of each week
week_markers = pd.DataFrame({'Start Date': start_dates, 'Week_Start': True})

# Calculate the start and end dates of the current week
today = datetime.today()
start_of_week = today - timedelta(days=today.weekday())
end_of_week = start_of_week + timedelta(days=6)

app = dash.Dash(__name__)
server=app.server


app.layout = html.Div([
    html.H1('Westchester Recycling : Actuator and Controls Installation', style={'color': 'black', 'fontSize': 40,'textAlign': 'center'}),
    html.Div(children=[
        dcc.Dropdown([x for x in sorted(dff['Project Section'].unique())],
                              value=[],
                             clearable=False,
                             multi=True,
                             style={'width':'65%'},
                             id='section-dropdown'),
        dcc.DatePickerRange(
            id='date-picker-range',
            start_date=date(2024,6,17),
            end_date=date(2025,3,31),
            style={'display': 'inline-block', 'float': 'right'}
        ),
    ]),
    html.H3('hover over bars for additional detail', style={'color': 'dimgray', 'fontSize': 15,}),

    html.Br(),
    html.Div(id='gantt-container'),
    html.Br(),
    # html.Div(id='sunburst-container'),
    # html.Br(),
    html.Div([
        dash_table.DataTable(
            id='datatable-interactivity',
            data=dff.to_dict('records'),
            columns=[
                {"name": i, "id": i, "deletable": False, "selectable": False} for i in dff.columns
            ],
            editable=False,
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            row_selectable="multi",
            row_deletable=False,
            selected_rows=[],
            page_action="native",
            page_current= 0,
            page_size= 6,
            style_as_list_view=True,
        )
    ]),
],className='row')

@app.callback(
    Output('datatable-interactivity', 'data'),
    [Input('section-dropdown', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range','end_date')]
)

def update_table(section_value, start_date, end_date):
    dff = df.copy()

    # Filter by section dropdown
    if section_value:
        dff = dff[dff['Project Section'].isin(section_value)]

    # Filter by date range
    if start_date and end_date:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        dff = dff[(dff['Start Date'] >= start_date) & (dff['Start Date'] <= end_date)]

    return dff.to_dict('records')

#Gantt Chart

@app.callback(
#     Output('ganttchart', 'children'),
#     Input('datatable_id', 'selected_rows'),
#     Input("section-dropdown", "value")
     Output(component_id='gantt-container', component_property='children'),
     [Input(component_id='datatable-interactivity', component_property="derived_virtual_data"),
      Input(component_id='datatable-interactivity', component_property='derived_virtual_selected_rows'),
      Input(component_id='datatable-interactivity', component_property='derived_virtual_selected_row_ids'),
      Input(component_id='datatable-interactivity', component_property='selected_rows'),
      Input(component_id='datatable-interactivity', component_property='derived_virtual_indices'),
      Input(component_id='datatable-interactivity', component_property='derived_virtual_row_ids'),
      Input(component_id='datatable-interactivity', component_property='active_cell'),
      Input(component_id='datatable-interactivity', component_property='selected_cells'),
      ]
 )

def update_gantt(all_rows_data, slctd_row_indices, slct_rows_names, slctd_rows,
               order_of_rows_indices, order_of_rows_names, actv_cell, slctd_cell):

    print('***************************************************************************')
    print('Data across all pages pre or post filtering: {}'.format(all_rows_data))
    print('---------------------------------------------')
    print("Indices of selected rows if part of table after filtering:{}".format(slctd_row_indices))
    print("Names of selected rows if part of table after filtering: {}".format(slct_rows_names))
    print("Indices of selected rows regardless of filtering results: {}".format(slctd_rows))
    print('---------------------------------------------')
    print("Indices of all rows pre or post filtering: {}".format(order_of_rows_indices))
    print("Names of all rows pre or post filtering: {}".format(order_of_rows_names))
    print("---------------------------------------------")
    print("Complete data of active cell: {}".format(actv_cell))
    print("Complete data of all selected cells: {}".format(slctd_cell))

    dff = pd.DataFrame(all_rows_data)
    dff['Pattern'] = dff['Completion PCT'].apply(lambda x: 'solid' if 0 < x < 100 else 'none')
    dff['Highlight'] = (dff['Completion PCT'] == 0) & (pd.to_datetime('today') > df['Start Date'])
    fig = dcc.Graph(id='gantt-chart', figure=px.timeline(
            data_frame=dff,
            x_start="Start Date",
            x_end="End Date",
            y="Task",
            color='Project Section',
            hover_name='Task',
            hover_data={'Crew':True,'Project Section':True,'Pattern':False,'Completion PCT':True,'Task':False},
            category_orders={"Task": ["Review + Update Electrical Drawings", "backend programming", "front end programming", "remove existing actuators", "install new actuators",
                                     "run electrical","fabricate control panels","install controls and make terminations","upload and start up"]},
            color_continuous_scale='blackbody',
            color_continuous_midpoint=50,
            opacity=.5,
        ).update_layout(
            paper_bgcolor='whitesmoke',
            plot_bgcolor='whitesmoke',
            hovermode="closest",
            xaxis_title="Schedule",
            yaxis_title="Task",
            showlegend=True,
            title_font_size=24,
            font_color='dimgray',
            hoverlabel=dict(
                bgcolor='gold',
                font_size=9,)
        ).update_traces(line_dash='dot', selector=dict(Highlight=True)))
    return [fig]

#Sunburst
# @app.callback(
#     Output=component
#
# )


if __name__ == '__main__':
    app.run_server(debug=True)
