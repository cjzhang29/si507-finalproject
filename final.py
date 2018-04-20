#final.py
import requests
from bs4 import BeautifulSoup
from requests_oauthlib import OAuth1
import json
import secrets
import sqlite3
from sqlite3 import Error
import plotly.plotly as py
import plotly.graph_objs as go
import sys

access_token = secrets.access_token
CACHE_FNAME = 'eatstreet_cache.json'
DBNAME = 'final.db'

class Coordinates:
    def __init__(self, lat, lng):
        self.lat = lat
        self.lng = lng

try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()
except:
    CACHE_DICTION = {}

# Retrieve the longitude and latitude of the top 10 most populated cities
# in the US by scraping the Wikipedia page of U.S. cities by population
def retrieve_cities():
    url = 'https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population'
    page_text = requests.get(url).text
    page_soup = BeautifulSoup(page_text, 'html.parser')
    page_soup.prettify()
    table = page_soup.find(class_='wikitable')
    table_rows = table.find_all('tr')
    coordinates_list = []
    for i in range(1,16): #top 15
        entries = table_rows[i].find_all('td')
        coordinates = entries[10].text
        i = coordinates.index(';')
        j = coordinates.index('(')
        lat = coordinates[i-7:i]
        lng = coordinates[i+2:j-2]
        coordinates_list.append(Coordinates(lat, lng))
    return coordinates_list

# A helper function that accepts 2 parameters
# and returns a string that uniquely represents the request
# that could be made with this info (url + params)
def params_unique_combination(baseurl, params):
    alphabetized_keys = sorted(params.keys())
    res = []
    for k in alphabetized_keys:
        res.append("{}-{}".format(k, params[k]))
    return baseurl + "_".join(res)

# function checks if data is already in cache before requesting new data
def make_request_using_cache(baseurl, params):
    unique_ident = params_unique_combination(baseurl, params)

    ## first, look in the cache to see if we already have this data
    if unique_ident in CACHE_DICTION:
        print("Fetching cached data...")
        return CACHE_DICTION[unique_ident]

    ## if not, fetch the data afresh, add it to the cache,
    ## then write the cache to file
    else:
        print("Making a request for new data...")
        # Make the request and cache the new data
        resp = requests.get(baseurl, params)
        CACHE_DICTION[unique_ident] = json.loads(resp.text)
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close() # Close the open file
        return CACHE_DICTION[unique_ident]

# Retrive restaurants selling Pad Thai within a 10-mile radius of the retrieved
# coordinates for each major city using the EatStreet API
def get_restaurants(lat, lng):
    url = 'https://api.eatstreet.com/publicapi/v1/restaurant/search'
    params = {'access-token': access_token, 'latitude': lat, 'longitude': lng,
    'pickup-radius': 10, 'search': 'Pad Thai'}
    #return requests.get(url, params).json()
    return make_request_using_cache(url, params)

# Retrieve menu for each restaurant with each restaurants API key using the
# EatStreet API
def get_restaurant_menu(api_key):
    baseurl = 'https://api.eatstreet.com/publicapi/v1/restaurant/'
    url = baseurl + api_key + '/menu'
    params = {'access-token': access_token}
    #return requests.get(url, params).json()
    return make_request_using_cache(url, params)

# Initialize DB
def db_initialization():
    try:
        conn = sqlite3.connect(DBNAME)
    except Error as e:
        print(e)
    cur = conn.cursor()
    statement = '''
        DROP TABLE IF EXISTS 'Restaurants';
    '''
    cur.execute(statement)
    statement = '''
        DROP TABLE IF EXISTS 'PadThaiItems';
    '''
    cur.execute(statement)
    conn.commit()

    new_statement = '''
        CREATE TABLE 'Restaurants' (
            'APIKey' TEXT PRIMARY KEY,
            'RestaurantName' TEXT,
            'City' TEXT,
            'State' TEXT,
            'Latitude' REAL,
            'Longitude' REAL
        );
        CREATE TABLE 'PadThaiItems'(
            'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'RestaurantAPIKey' TEXT,
            'ItemName' TEXT,
            'BasePrice' REAL,
            'ItemAPIKey' TEXT
        );
    '''
    cur.executescript(new_statement)
    conn.close()

# Populate the "Restaurants" table in the sqlite db
def populate_restaurants(row):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    insert_statement = '''
        INSERT INTO Restaurants
        VALUES (?, ?, ?, ?, ?, ?)
    '''
    values = (row[0], row[1], row[2], row[3], row[4], row[5])
    cur.execute(insert_statement, values)
    conn.commit()
    conn.close()

# Populate the "PadThaiItems" table in the sqlite db
def populate_pad_thai_items(row):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    insert_statement = '''
        INSERT INTO PadThaiItems
        VALUES (?, ?, ?, ?, ?)
    '''
    values = (None, row[0], row[1], row[2], row[3])
    cur.execute(insert_statement, values)
    conn.commit()
    conn.close()

# Call populate_restaurants and populate_pad_thai_items functions to populate
# the sqlite db
def data_storage(coordinates_list):
    for c in coordinates_list:
        restaurant_data = get_restaurants(c.lat, c.lng)
        restaurants = restaurant_data['restaurants']
        for r in restaurants:
            if r['name'] == 'Thai Thai Restaurant':
                populate_restaurants([r['apiKey'], r['name'] + ' (' + r['state']
                + ')', r['city'], r['state'], r['latitude'], r['longitude']])
            else:
                populate_restaurants([r['apiKey'], r['name'], r['city'], r['state'],
                r['latitude'], r['longitude']])
            menu_data = get_restaurant_menu(r['apiKey'])
            for categories in menu_data:
                items = categories['items']
                for i in items:
                    if 'pad thai' in i['name'].lower():
                        if i['basePrice'] < 30: # exclude party trays
                            populate_pad_thai_items([r['apiKey'], i['name'],
                            i['basePrice'], i['apiKey']])

# Retrieve the restaurants located in a specifed state in our database
def get_restaurants_for_state(state_abbr):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    statement = '''
        SELECT RestaurantName, Latitude, Longitude
        FROM Restaurants
        WHERE State LIKE ?
    '''
    param = (state_abbr, )
    cur.execute(statement, param)
    results = cur.fetchall()
    conn.close()
    return results

# Plot restaurants located in the specified state with plotly scattergeo
def plot_restaurants(state_abbr):
    lat_vals = []
    lng_vals = []
    text_vals = []
    state_restaurants = get_restaurants_for_state(state_abbr)
    for r in state_restaurants:
        lat_vals.append(r[1])
        lng_vals.append(r[2])
        text_vals.append(r[0])

    # Change map scale
    min_lat = 10000
    max_lat = -10000
    min_lon = 10000
    max_lon = -10000
    for str_v in lat_vals:
        v = float(str_v)
        if v < min_lat:
            min_lat = v
        if v > max_lat:
            max_lat = v
    for str_v in lng_vals:
        v = float(str_v)
        if v < min_lon:
            min_lon = v
        if v > max_lon:
            max_lon = v
    center_lat = (max_lat+min_lat) / 2
    center_lon = (max_lon+min_lon) / 2
    max_range = max(abs(max_lat - min_lat), abs(max_lon - min_lon))
    padding = max_range * .10
    lat_axis = [min_lat - padding, max_lat + padding]
    lon_axis = [min_lon - padding, max_lon + padding]

    #Update data layout information for plotting on map
    data = [ dict(
        type = 'scattergeo',
        locationmode = 'USA-states',
        lon = lng_vals,
        lat = lat_vals,
        text = text_vals,
        mode = 'markers',
        marker = dict(
            size = 8,
            symbol = 'star',
        ))]

    if state_abbr == '__':
        title_str = 'Restaurants Serving Pad Thai'
    else:
        title_str = 'Restaurants Serving Pad Thai in ' + state_abbr.upper()
    layout = dict(
        title = title_str,
        geo = dict(
            scope='usa',
            projection=dict(type='albers usa'),
            showland = True,
            landcolor = "rgb(250, 250, 250)", #white
            subunitcolor = "rgb(100, 217, 217)",  #blue
            countrycolor = "rgb(217, 100, 217)",
            lataxis = {'range': lat_axis},
            lonaxis = {'range': lon_axis},
            center= {'lat': center_lat, 'lon': center_lon},
            countrywidth = 3,
            subunitwidth = 3
        ),
    )
    fig = dict(data=data, layout=layout)
    if state_abbr == '__':
        state_abbr = 'us'
    filename = 'restaurants-in-' + state_abbr
    py.plot(fig, validate=False, filename=filename)

# Retrive average prices of Pad Thai by state
def retrieve_avg_state_prices():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    statement = '''
        SELECT State, AVG(BasePrice)
        FROM Restaurants as r
            JOIN PadThaiItems as m ON r.APIKey = m.RestaurantAPIKey
            GROUP BY r.State
    '''
    cur.execute(statement)
    results = cur.fetchall()
    conn.close()
    return results

# Plot average prices of Pad Thai items for each state with plotly bar chart
def plot_avg_state_pad_thai_prices():
    states = []
    avg_prices = []
    results = retrieve_avg_state_prices()
    for r in results:
        states.append(r[0])
        avg_prices.append(round(r[1],2))

    # Bar chart
    data = [go.Bar(
        x=states,
        y=avg_prices,
        text=states,
        marker=dict(
            color='rgb(158,202,225)',
            line=dict(
                color='rgb(8,48,107)',
                width=1.5),
        ),
        opacity=0.6
    )]
    layout = go.Layout(
        title='Average Pad Thai Prices By State (in USD)',
    )
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, validate=False, filename='pad-thai-prices-by-state')

# Retrieve all base prices from PadThaiItems
def retrieve_all_base_prices():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    statement = '''
        SELECT BasePrice
        FROM PadThaiItems
    '''
    cur.execute(statement)
    results = cur.fetchall()
    conn.close()
    return results

# Plot histogram of all Pad Thai prices with plotly
def plot_pad_thai_prices_histogram():
    base_prices = []
    results = retrieve_all_base_prices()
    for r in results:
        base_prices.append(round(r[0],2))

    # Histogram
    data = [go.Histogram(
        x=base_prices,
        marker=dict(
            color='rgb(158,202,225)',
            line=dict(
                color='rgb(8,48,107)',
                width=1.5),
        ),
        xbins=dict(
            size = 0.5
        )
    )]
    layout = go.Layout(
        title='Histogram of Pad Thai Prices',
        xaxis=dict(
            title='Price'
        ),
        yaxis=dict(
            title='Count'
        ),
        bargap=0.1,
        bargroupgap=0.1
    )
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, validate=False, filename='histogram-pad-thai')

# Retrive average prices of Pad Thai of each restaurant located in the
# specifed state
def retrieve_all_avg_prices(state_abbr):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    statement = '''
        SELECT RestaurantName, AVG(BasePrice)
        FROM Restaurants as r
            JOIN PadThaiItems as m ON r.APIKey = m.RestaurantAPIKey
            GROUP BY m.RestaurantAPIKey
            HAVING r.State LIKE ?
    '''
    param = (state_abbr, )
    cur.execute(statement, param)
    results = cur.fetchall()
    conn.close()
    return results

# Plot scatterplot of average prices of Pad Thai items in each restaurant in
# the specified state with plotly
def plot_pad_thai_prices_scatterplot(state_abbr):
    restaurants = []
    avg_prices = []
    results = retrieve_all_avg_prices(state_abbr)
    for r in results:
        restaurants.append(r[0])
        avg_prices.append(round(r[1],2))

    # Scatterplot
    data = [go.Scatter(
        x = restaurants,
        y = avg_prices,
        text = restaurants,
        marker=dict(
            color='rgb(158,202,225)',
            line=dict(
                color='rgb(8,48,107)',
                width=1.5),
        ),
        mode = 'lines+markers'
    )]
    if state_abbr == '__':
        title_str = 'Average Pad Thai Prices (in USD)'
    else:
        title_str = 'Average Pad Thai Prices in ' + state_abbr.upper() + ' (in USD)'
    layout = go.Layout(
        title=title_str,
    )
    fig = go.Figure(data=data, layout=layout)
    if state_abbr == '__':
        state_abbr = 'us'
    filename = state_abbr + '-pad-thai-prices'
    py.plot(fig, validate=False, filename=filename)

def interactive_prompt():
    valid_states = ['AZ', 'CA', 'FL', 'IL', 'IN', 'NJ', 'NY', 'OH', 'PA', 'TX']
    command_help = '''
map <state_abbr>
    valid inputs: a two-letter state abbreviation or no input
    available states: AZ, CA, FL, IL, IN, NJ, NY, OH, PA, TX
    displays geoplot of all restaurants in the specified state
    if no <stateabbr> is specified, restaurants in all states will be plotted
price <state_abbr>
    valid inputs: a two-letter state abbreviation or no input
    available states: AZ, CA, FL, IL, IN, NJ, NY, OH, PA, TX
    displays scatterplot of average prices of all Pad Thai items offered
    by each restaurant on EatStreet in the specified state
    if no <stateabbr> is specified, all average Pad Thai prices will be plotted
bar
    displays bar chart of average prices of Pad Thai items by state
histogram
    displays histogram of all Pad Thai prices
exit
    exits the program
help
    lists available commands (these instructions)'''
    option = ''
    base_prompt = 'Enter command (or "help" for options): '
    feedback = ''
    while True:
        action = input(feedback + '\n' + base_prompt)
        feedback = ""
        words = action.split()
        if len(words) > 0:
            command = words[0]
        else:
            command = None
        if command == 'exit':
            print('\nBye!\n')
            return
        elif command == 'help':
            print(command_help)
        elif command == 'map':
            if len(words) == 1:
                print('Plotting all restaurants serving Pad Thai in plotly...\n')
                plot_restaurants('__')
            elif len(words) == 2:
                if words[1].upper() in valid_states:
                    state_abbr = words[1].upper()
                    print('Plotting restaurants serving Pad Thai in '
                    + state_abbr + ' in plotly...\n')
                    plot_restaurants(state_abbr)
                else:
                    feedback = '\nPlease input a valid two-letter state abbreviation.\n'
            else:
                feedback = '\nPlease input only a two-letter state abbreviation or nothing.\n'
        elif command == 'price':
            if len(words) == 1:
                print('Plotting all average Pad Thai prices in plotly...\n')
                plot_pad_thai_prices_scatterplot('__')
            elif len(words) == 2:
                if words[1].upper() in valid_states:
                    state_abbr = words[1].upper()
                    print('Plotting average Pad Thai prices in '
                    + state_abbr + ' in plotly...\n')
                    plot_pad_thai_prices_scatterplot(state_abbr)
                else:
                    feedback = '\nPlease input a valid two-letter state abbreviation.\n'
            else:
                feedback = '\nPlease input only a two-letter state abbreviation or nothing.\n'
        elif command == 'bar':
            if len(words) == 1:
                print('Plotting average prices of Pad Thai items by state in plotly...\n')
                plot_avg_state_pad_thai_prices()
            else:
                feedback = '\nPlease input "bar" only.\n'
        elif command == 'histogram':
            if len(words) == 1:
                print('Plotting a histogram of all Pad Thai prices in plotly...\n')
                plot_pad_thai_prices_histogram()
            else:
                feedback = '\nPlease input "histogram" only.\n'
        else:
            feedback = '\nI didn\'t understand that. Please try again.\n'

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--init':
        print('Initializing & populating the DB.')
        db_initialization()
        city_coordinates = retrieve_cities()
        data_storage(city_coordinates)
    else:
        #print('Leaving the DB alone.')
        interactive_prompt()
