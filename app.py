from tkinter.tix import Tree
import dash
import dash_bootstrap_components as dbc
from dash import dcc, ALL, callback_context
from dash import html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from pymongo import MongoClient
from dotenv import load_dotenv, find_dotenv
from itertools import product
from datetime import datetime
import pprint
from dotenv import load_dotenv, find_dotenv
import os
import random
import requests
from functools import lru_cache
import concurrent.futures


from requests import options

load_dotenv(find_dotenv())
password = os.environ.get("MONGO_DB")


import plotly.graph_objs as go

# Example usage
api_key = os.environ.get("GOOGLE_API_KEY")

connection_string = f"mongodb+srv://courseserv:{password}@uiuc-schedule.qhi3i2e.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(connection_string)

dbs_names = client.list_database_names()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUMEN])
app.config['suppress_callback_exceptions'] = True
app.config['prevent_initial_callbacks'] = 'initial_duplicate'

printer = pprint.PrettyPrinter()

# Array for first dropdown
arr_drop1 = []

# Dictionary for second dropdown
dict_drop2 = {}

# Dictionary with all the information
#format: {subject: {"course: {"Meeting Type": [list_of_all_sections]}}
course_info = {}

# Coordinates of the main quad in Champaign, IL
champaign_lat = 40.1075
champaign_lon = -88.2272

# Longitude and Latitude to adjust the width of the map
lat_span = 1
lon_span = 1

# List with all the courses selected in the dropdown 
selected_courses_list = []

# Count of old clicks to decide whether to change the map or not
old_n_clicks = 0

# List of possible schedules
possible_schedules = []

# Dictionary with days of the week
days_dictionary = {
    'M': 'Monday',
    'T': 'Tuesday',
    'W': 'Wednesday',
    'R': 'Thursday',
    'F': 'Friday'
}

locations_dictionary = {
    'M': [],
    'T': [],
    'W': [],
    'R': [],
    'F': []
}


#need to populate the two arrays with the given for the two dropdowns
def populate_dropdowns():
    courses = []

    for subject in dbs_names:
        if subject.isupper():
            subject_database = client[subject]
            courses = subject_database.list_collection_names()


            arr_drop1.append({'label': subject, 'value': subject})

            for course in courses:
                if course.isdigit():
                    

                    

                    if subject not in dict_drop2:
                        dict_drop2[subject] = [course]
                    else:
                        dict_drop2[subject].append(course)

            dict_drop2[subject].sort()

def populate_course_info():

    #set with all the subject that don't follow format
    subjects_format = set()

    for subject in dict_drop2.keys():
        course_info[subject] = {}
        for course in dict_drop2[subject]:
            course_dict = {}

            #get all course info from client
            course_info_collection = client[subject][course]

            #make iterable
            infos = course_info_collection.find()

            #iterate thru each info
            for info in infos:
                if course not in course_dict:
                    #print(info)
                    course_dict[course] = [info]
                else:
                    course_dict[course].append(info)
            
            type_meeting_dict = {}

            for information in course_dict[course]:
                if "Meeting Type" in information.keys():
                    
                    meeting_type = information["Meeting Type"]

                    #if information is "Start Time" or information is "End Time" or 
                    #print(information)

                    if meeting_type not in type_meeting_dict.keys():
                        type_meeting_dict[meeting_type] = [information]
                    else:
                        type_meeting_dict[meeting_type].append(information)
                    #print(subject)
                    subjects_format.add(subject)

            if subject in subjects_format:
                #print(subject)
                course_dict[course] = type_meeting_dict
            else:
                course_dict[course] = {'None': course_dict[course]}



            if course not in course_info[subject]:
                ##print(subject)
                ##print(course)
                course_info[subject][course] = course_dict[course]
            else:
                course_info[subject][course].update(course_dict[course])


def get_distance(api_key, origin, destination):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origin,
        "destinations": destination,
        "key": api_key
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def time_to_minutes(time_str):
    period = time_str[-2:]
    hours, minutes = map(int, time_str[:-2].split(':'))
    if period == 'PM' and hours != 12:
        hours += 12
    elif period == 'AM' and hours == 12:
        hours = 0
    return hours * 60 + minutes

def is_conflict(time1, time2, api_key=None, location1=None, location2=None):
    start1, end1 = time_to_minutes(time1['Start Time']), time_to_minutes(time1['End Time'])
    start2, end2 = time_to_minutes(time2['Start Time']), time_to_minutes(time2['End Time'])
    days1, days2 = time1['Days of Week'].strip(), time2['Days of Week'].strip()
    
    if bool(set(days1) & set(days2)) and not (end1 <= start2 or start1 >= end2):
        return True
    
    # Check travel time constraint if applicable
    if api_key and location1 and location2 and start2 - end1 <= 10 and start2 - end1 >= 0:
        if travel_time_too_long(api_key, location1, location2):
            return True
    
    return False

def travel_time_too_long(api_key, location1, location2):
    distance_info = get_distance(api_key, location1, location2)
    if distance_info:
        try:
            duration = distance_info['rows'][0]['elements'][0]['duration']['value'] / 60  # duration in minutes
            return duration > 7
        except (KeyError, IndexError):
            return True  # Default to True if API response is malformed
    return True  # Default to True if API call fails

def is_valid_schedule(schedule, api_key):
    # Flatten the list of tuples to a list of dictionaries
    flattened_schedule = [meeting for section in schedule for meeting in section]
    
    for i in range(len(flattened_schedule)):
        for j in range(i + 1, len(flattened_schedule)):
            location1 = f"{flattened_schedule[i].get('lat', '')},{flattened_schedule[i].get('lng', '')}"
            location2 = f"{flattened_schedule[j].get('lat', '')},{flattened_schedule[j].get('lng', '')}"
            if is_conflict(flattened_schedule[i], flattened_schedule[j], api_key, location1, location2):
                return False
    return True

def backtrack_schedules(api_key, class_sections, current_schedule, index, schedules, limit=20):
    #print(f"Lenght of schedules: {len(schedules)} Current index: {index}, Current schedule length: {len(current_schedule)}")
    
    if len(schedules) >= limit:
        return

    if index == len(class_sections):
        if is_valid_schedule(current_schedule, api_key):
            schedules.append(list(current_schedule))
        return

    for section in class_sections[index]:
        current_schedule.append(section)
        if is_valid_schedule(current_schedule, api_key):
            backtrack_schedules(api_key, class_sections, current_schedule, index + 1, schedules, limit)
        current_schedule.pop()
        #print(f"Lenght of schedules: {len(schedules)} Current index: {index}, Current schedule length: {len(current_schedule)}")
        if len(schedules) >= limit:
            return
    



def generate_schedules(api_key, classes):
    class_sections = [
        list(product(*[
            [{'course': cls, 'type': typ, **details} for details in section]
            for typ, section in sections.items()
        ]))
        for cls, sections in classes.items()
    ]
    schedules = []
    
    backtrack_schedules(api_key, class_sections, [], 0, schedules)
    
    return schedules

populate_dropdowns()
populate_course_info()


# Front-end of application

@app.callback(
    Output('demo-dropdown2', 'options'),
    Input('demo-dropdown1', 'value')
)
def update_second_dropdown(selected_subject):
    if selected_subject is not None:
        options = [{'label': course, 'value': course} for course in dict_drop2[selected_subject]]
        return options
    else:
        return []


@app.callback(
    Output('selected-courses-container', 'children'),
    [Input('submit-val', 'n_clicks'), Input({'type': 'delete-button', 'index': ALL}, 'n_clicks')],
    [State('demo-dropdown1', 'value'), State('demo-dropdown2', 'value')],
    prevent_initial_call=True
)
def update_output(n_clicks, delete_clicks, value1, value2):
    global old_n_clicks
    global selected_courses_list

    ctx = callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if 'submit-val' in triggered_id:
        if n_clicks is None or value1 is None or value2 is None:
            return 'Select options from dropdowns'

        if n_clicks > old_n_clicks:
            old_n_clicks = n_clicks
            if f'{value1} {value2}' not in selected_courses_list:
                selected_courses_list.append(f'{value1} {value2}')
    else:
        if 'delete-button' in triggered_id:
            index = int(triggered_id.split('.')[0].split('"index":')[1][0])
            if 0 <= index < len(selected_courses_list):
                selected_courses_list.pop(index)

    # Display the accumulated courses vertically in boxes
    selected_courses = [
        dbc.Alert(
            [
                course,
                dbc.Button(
                    "×",
                    id={'type': 'delete-button', 'index': i},
                    color='link',
                    style={'float': 'right', 'padding': '0', 'margin': '0'}
                )
            ],
            color='#13294B',
            style={'margin-bottom': '10px'}
        )
        for i, course in enumerate(selected_courses_list)
    ]


    return selected_courses




def display_options(schedules):
    # Clear the existing content of the display container
    children = []

    # Iterate through the schedule and display information for each course
    for i, schedule in enumerate(schedules, 1):
        
        children.append(html.H3(f"Schedule {i}:"))
        for tuple_schedule in schedule:
        #print(tuple_schedule)
            for meeting in tuple_schedule:
                days_of_week_abbrev = meeting['Days of Week'].strip()
                days_of_week_full = ' '.join([days_dictionary.get(day, day) for day in days_of_week_abbrev])
                children.append(html.P(f"{meeting['course']} Meeting Type: {meeting['type']} Days: {days_of_week_full} Time: {meeting['Start Time']} - {meeting['End Time']}"))

            
        button_id = {'type': 'schedule-button', 'index': i}
        children.append(html.Button(f"Select Schedule {i}", id=button_id, n_clicks=0))
        

    return children






schedules_output_div = html.Div(id='schedules-output')
@app.callback(
    Output('schedules-output', 'children'),
    Input('schedules', 'n_clicks'),
    prevent_initial_call=True
)
def generate_schedules_callback(n_clicks):
    #global courses
    if n_clicks is None:
        raise PreventUpdate

    # Reset the courses list
    courses = {}
    global course_info

    # Iterate through selected_courses_list and create a list of dictionaries
    for selected_course in selected_courses_list:
        # Extract subject and course from the selected course string
        subject, course = selected_course.split(' ')
        # Check if the subject and course exist in course_info
        if subject in course_info and course in course_info[subject]:
            # Add the course information to the courses list
            # Randomize the order schedules
            for type in course_info[subject][course]:
                #print(course_info[subject][course][type])
                random.shuffle(course_info[subject][course][type])
                #print(course_info[subject][course][type])
                #print(type)

            courses[f'{subject} {course}'] = course_info[subject][course]


    
    
    # Generate all possible schedules
    #print(courses)

    global possible_schedules
    possible_schedules = generate_schedules(api_key, courses)
    #print(possible_schedules[0])
    #print(possible_schedules)

    #print("possible schedules printed")
    


    information = display_options(possible_schedules)

    #print(locations_dictionary)
    return information







form = dbc.Form(
    dbc.Row(
        [
            
            html.Div([
                "Subject",
                dcc.Dropdown(
                    arr_drop1,
                    id='demo-dropdown1',
                    placeholder="Select Subject...",
                ),
                
            ],
            className="me-3"),
            
            html.Div([
                "Course",
                dcc.Dropdown(
                    options= [], #second_dropdown_array,
                    id='demo-dropdown2',
                    placeholder="Select Course...",
                ),
                
            ], 
            className="me-3"),
            html.Button('Submit', id='submit-val', n_clicks=0),


            html.Div(id='selected-courses-container', style={'margin-top': '40px'}),
        ],
        className="g-2",
    )
)



map_figure = {
    'data': [
        go.Scattermapbox(
            lat=[champaign_lat],
            lon=[champaign_lon],
            mode='markers',
            marker=dict(size=14, color='red'),
            text='The Main Quad',
            hoverinfo='text',
        ),
    ],
    'layout': go.Layout(
        hovermode='closest',
        margin=go.layout.Margin(l=0, r=0, t=0, b=0),
        mapbox=dict(
            style="open-street-map",
            zoom=16,
            center=dict(
                lat=champaign_lat,
                lon=champaign_lon
            ),
            domain=dict(x=[0, lon_span], y=[0, lat_span]),
    
        ),
    )
}

selected_schedule_output_div = html.Div(id='selected_schedule_output')
@app.callback(
    Output('selected_schedule_output', 'children'),
    Input({'type': 'schedule-button', 'index': ALL}, 'n_clicks'),
    State('schedules-output', 'children')
)
def update_selected_schedule(n_clicks, schedules_output):
    children = []
    ctx = callback_context

    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    # Get the ID of the triggered button
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if not triggered_id:
        raise dash.exceptions.PreventUpdate

    # Parse the triggered_id to get the index
    triggered_index = int(eval(triggered_id)['index'])

    children.append(html.Div(
            [
                html.H2("Selected Schedule", style={'background-color': '#13294B', 'color': '#F8FAFC'}),
                
            ],
            style={'display': 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'background-color': '#13294B', 'height': '8vh'}
        ))
    
    #children.append(html.P(triggered_index))

    #selected_schedule_num = clicked_schedule[len(clicked_schedule) - 1]
    #print(selected_schedule_num)
    global locations_dictionary
    locations_dictionary = {
        'M': [],
        'T': [],
        'W': [],
        'R': [],
        'F': []
    }
    #print(len(possible_schedules))
    schedule = possible_schedules[triggered_index - 1]
    #print("this is the selected schedule") 
    #print(schedule)
    course_groups = {}

    for tuple_schedule in schedule:
        for meeting in tuple_schedule:
            course = meeting['course']
            if course not in course_groups:
                course_groups[course] = []

            course_groups[course].append(meeting)
            for day in meeting['Days of Week'].strip():
                locations_dictionary[day].append({
                    "Building Name": f"{meeting['Building Name']}, Room {meeting['Room Number']}",
                    "lat": meeting['lat'],
                    "lng": meeting['lng']
                })

    for course, meetings in course_groups.items():
        course_div = [
            html.H3(f"{course}", style={'color': '#13294B'}),
        ]
        
        first = False
        for meeting in meetings:

            if (first is False):
                course_div.append(html.P(f"Description: {meeting['Course Description']}"))
                first = True

            days_of_week_abbrev = meeting['Days of Week'].strip()
            days_of_week_full = ' '.join([days_dictionary.get(day, day) for day in days_of_week_abbrev])


            course_div.append(html.P(f"Meeting Type: {meeting['type']}", style={'font-weight': 'bold'}))
            course_div.append(html.P(f"Section: {meeting['Section Number']}"))
            course_div.append(html.P(f"Days: {days_of_week_full}"))
            course_div.append(html.P(f"Time: {meeting['Start Time']} - {meeting['End Time']}"))
            course_div.append(html.P(f"Location: {meeting['Building Name']}, Room {meeting['Room Number']}"))

        children.append(html.Div(course_div, style={'padding': '10px', 'border': '1px solid #13294B', 'border-radius': '5px', 'margin-bottom': '10px'}))

    for day in locations_dictionary.keys():
        if (len(locations_dictionary[day]) == 0):
            locations_dictionary[day].append({
                        "Building Name": "No classes this day",
                    "lat": champaign_lat,
                    "lng": champaign_lon
                })

    return children



# Callback to update the map based on the selected day
@app.callback(
    Output('champaign-map', 'figure'),
    [Input('monday-val', 'n_clicks'),
     Input('tuesday-val', 'n_clicks'),
     Input('wednesday-val', 'n_clicks'),
     Input('thursday-val', 'n_clicks'),
     Input('friday-val', 'n_clicks')],
    [State('schedules-output', 'children')]
)
def update_map_based_on_day(monday_clicks, tuesday_clicks, wednesday_clicks, thursday_clicks, friday_clicks, schedules_output):
    # Determine which day was clicked
    triggered_id = dash.callback_context.triggered_id

    if triggered_id is None:
        raise PreventUpdate

    # Determine which day was clicked
    clicked_day = triggered_id.split('.')[0]

    if clicked_day == 'monday-val':
        day = 'M'
    elif clicked_day == 'tuesday-val':
        day = 'T'
    elif clicked_day == 'wednesday-val':
        day = 'W'
    elif clicked_day == 'thursday-val':
        day = 'R'
    elif clicked_day == 'friday-val':
        day = 'F'
    else:
        raise PreventUpdate

    # Extract locations from the dictionary based on the selected day
    locations = locations_dictionary[day]

    # Update the map figure
    map_figure = update_map_figure(locations)
    
    return map_figure


def update_map_figure(locations):
    map_figure = {
        'data': [],
        'layout': go.Layout(
            hovermode='closest',
            margin=go.layout.Margin(l=0, r=0, t=0, b=0),
            mapbox=dict(
                style="open-street-map",
                zoom=16,
                center=dict(
                    lat=champaign_lat,
                    lon=champaign_lon
                ),
                domain=dict(x=[0, lon_span], y=[0, lat_span]),

            ),
        )
    }
    for items in locations:
        new_marker = go.Scattermapbox(
                    lat=[items["lat"]],
                    lon=[items["lng"]],
                    mode='markers',
                    marker=dict(size=14, color='red'),
                    text=items["Building Name"],
                    hoverinfo='text',
                )
        map_figure['data'].append(new_marker)
    return map_figure


app.layout = html.Div(
    [
        html.Div(
            [
                html.H1("Add Courses for Spring 2024 Urbana Champaign", style={'background-color': '#13294B', 'color': '#F8FAFC'}),
                html.Img(src='https://brand.illinois.edu/wp-content/uploads/2021/09/block-I-blue-background.png', style={'float': 'right', 'height': '70px', 'width': 'auto'}),
            ],
            style={'display': 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'background-color': '#13294B', 'height': '8vh'}
        ),

        html.Div(
            className="row",
            children=[
                dbc.Col([form, html.Button('Generate schedules', id='schedules', n_clicks=0)], width=6, style={'background-color': '#F8FAFC'}),
                dbc.Col([
                    html.Div(
                        className="row",
                        children=[
                            # Column for user controls
                            dbc.Col([html.H2("Monday", style={'background-color': '#F8FAFC', 'color': '#13294B', 'height': '5vh'}),html.Button(children='Select Day', id='monday-val', n_clicks=0)]),
                            dbc.Col([html.H2("Tuesday", style={'background-color': '#F8FAFC', 'color': '#13294B', 'height': '5vh'}), html.Button(children='Select Day', id='tuesday-val', n_clicks=0)]),
                            dbc.Col([html.H2("Wednesday", style={'background-color': '#F8FAFC', 'color': '#13294B', 'height': '5vh'}), html.Button(children='Select Day', id='wednesday-val', n_clicks=0)]),
                            dbc.Col([html.H2("Thursday", style={'background-color': '#F8FAFC', 'color': '#13294B', 'height': '5vh'}), html.Button(children='Select Day', id='thursday-val', n_clicks=0)]),
                            dbc.Col([html.H2("Friday", style={'background-color': '#F8FAFC', 'color': '#13294B', 'height': '5vh'}), html.Button(children='Select Day', id='friday-val', n_clicks=0)])
                        ]
                    ),
                    dcc.Graph(
                        id='champaign-map',
                        style={'width': '100%', 'height': '80vh'},
                        figure=map_figure
                    )
                ], width=6, style={'background-color': '#F8FAFC'})  
            ],
        ),
        
        html.Div(
            [
                html.H2("Schedules", style={'background-color': '#13294B', 'color': '#F8FAFC'}),
                
            ],
            style={'display': 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'background-color': '#13294B', 'height': '8vh'}
        ),
        html.Div(
            [
                schedules_output_div,
            ],
        ),
        html.Div(
            [
                selected_schedule_output_div,
            ],
        ),
    ]
)


if __name__ == '__main__':
    app.run_server(debug=True)