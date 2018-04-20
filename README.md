#si507-finalproject

------------ TO RUN THE PROGRAM ------------
+ First initialize the database, run "python final.py --init".
+ Then you may call the interactive prompt by running "python      final.py" in the command line.
+ Follow these instructions to install Plotly for Python in order to output the graphical information: https://plot.ly/python/getting-started/

------------- DATA SOURCES USED -------------
+ Coordinates of the top 15 most populated cities in the U.S.: https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population
+ EatStreet API: https://developers.eatstreet.com/
    + Used the following APIs:
        + Search Restaurants: https://developers.eatstreet.com/endpoint/search
        + Restaurant Menu: https://developers.eatstreet.com/endpoint/restaurant-menu
    + Note: Every request to EatStreet API must be authenticated with an access token. New developers should go to the site linked above and follow the instructions to receive an access token.
    + After obtaining an access token, created a secrets.py file with a single line:
        + access_token = '<insert access token here>'

------------- CODE STRUCTURE -------------
+ Initialization & data storage:
    + db_initialization()
        Drops existing tables in the DB and defines the column name & type in preparation for data population
    + retrieve_cities()
        Scrapes wikipedia page for coordinates of the 15 most populated cities
    + data_storage(city_coordinates)
        Takes the list of coordinates as an input and calls populate_restaurants() and populate_pad_thai_items() functions to populate the sqlite DB with information from the EatStreet API queries.
+ Commands available to user:
    + map <state_abbr>
        + valid inputs: a two-letter state abbreviation or no input
        + available states: AZ, CA, FL, IL, IN, NJ, NY, OH, PA, TX
        + displays geoplot of all restaurants in the specified state
        + if no <stateabbr> is specified, restaurants in all states will be plotted
    + price <state_abbr>
        + valid inputs: a two-letter state abbreviation or no input
        + available states: AZ, CA, FL, IL, IN, NJ, NY, OH, PA, TX
        + displays scatterplot of average prices of all Pad Thai items offered by each restaurant on EatStreet in the specified state
        + if no <stateabbr> is specified, all average Pad Thai prices will be plotted
    + bar
        + displays bar chart of average prices of Pad Thai items by state
    + histogram
        + displays histogram of all Pad Thai prices
    + exit
        + exits the program
    + help
        + lists available commands (these instructions)

---------- HAPPY PAD THAI SEARCHING! ----------
