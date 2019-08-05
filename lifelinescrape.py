import requests
import pandas as pd
import json
import time
from googleplaces import GooglePlaces
from yelp.client import Client


def remove(list_of_removeables, df):
    return df[~df['Category'].isin(list_of_removeables)]


def scrape_yelp(tuple_list, lifeline_num, api_key):
    """
    FEMA has 7 Lifelines. Each Lifeline has between 2 and 7 components that FEMA uses to monitor the status of each lifeline during an incident. This function takes in a city name to find the lifelines in that city.

    This is ONLY for Houston, Texas and
            ONLY for one lifeline at a time

    Parameters
    ----------
    tuple_list : list of tuples, in order to define and unpack into dataframe, this function takes a list of tuples where each tuple is:
        first: a list of strings that are the search words for Yelp API using their prewritten categories
        second: item is a string that is the name of the component you want to be in the column 'Component'
        example: [(component1_list, 'Name of Component 1'), (component2_list, 'Name of Component 2') .. etc]

    apik_key : string, must get from Yelp API.

    lifeline_num : int, discrete number 1-7 that corresponds to lifeline order according to FEMA. Our understanding is that this is not ordinal.

    components = list of strings; strings are used in the GooglePlaces API to search. General search terms are already provdied, but can be redefined to make a stronger and more meaningful map
    """
    counter = 0
    offset = 0
    full_list = []
    run = {'businesses':['one']}
    category_list=[]
    for n in tuple_list:
        for i in n[0]:
            category_list.append(i)
    while len(run['businesses']) > 0:
        endpoint = 'https://api.yelp.com/v3/businesses/search'
        headers = {'Authorization': 'bearer %s' % api_key}
        parameter = {'categories': category_list,
                     'limit': 50,
                     'radius': 40000,
                     'location': 'Houston',
                     'is_claimed': False,
                     'offset': offset}
        res = requests.get(url=endpoint, headers=headers, params=parameter)

        #check yourself before you wreck yourself
        if res.status_code == 200:
            run = res.json()
            print(f"got {len(run['businesses'])}")
            full_list.extend(run['businesses'])
            counter += 1
            offset = counter * 50
            time.sleep(2)
            if len(run['businesses']) == 0:
                print('reached the end')
                print(f'total collected: {len(full_list)}')
                def make_df(category_list, lifeline_num, full_list):

                    #make empty lists for dict
                    names = []
                    categories = []
                    lat = []
                    long = []

                    #for loop to append information for each business to empty lists
                    for i in range(len(full_list)):
                        names.append(full_list[i]['name'])
                        categories.append(full_list[i]['categories'][0]['alias'])
                        lat.append(full_list[i]['coordinates']['latitude'])
                        long.append(full_list[i]['coordinates']['longitude'])

                    def component_builder(tuple_list):
                        def unpack(cell):
                            for n in tuple_list:
                                for i in n[0]:
                                    if cell == i:
                                        return n[1]
                        return df['Category'].map(unpack)

                    #create dataframe
                    df = pd.DataFrame(columns=['Business'])
                    df['Business'] = names
                    df['Category'] = categories
                    df['Source'] = 'Yelp'
                    df['Latitude'] = lat
                    df['Longitude'] = long
                    df['Lifeline'] = lifeline_num
                    df['Component'] = component_builder(tuple_list)

                    #return df
                    return df
                return make_df(category_list, lifeline_num, full_list)
            else:
                continue
        else:
            print(f'something went wrong! status code: {res.status_code}')




def scrape_google(tuple_list, lifeline_num, api_key):
    """
    FEMA has 7 Lifelines. Each Lifeline has between 2 and 7 components that FEMA uses to monitor the status of each lifeline during an incident. This function takes in a city name to find the lifelines in that city.


    This is ONLY for Houston, Texas and
            ONLY for one lifeline at a time

    Parameters
    ----------
    tuple_list : list of tuples, in order to define and unpack into dataframe, this function takes a list of tuples where each tuple is:
        first: a list of strings that are the search words for GooglePlaces API
        second: item is a string that is the name of the component you want to be in the column 'Component'
        example: [(component1_list, 'Name of Component 1'), (component2_list, 'Name of Component 2') .. etc]

    apik_key : string, must get from GooglePlaces API.

    lifeline_num : int, discrete number 1-7 that corresponds to lifeline order according to FEMA. Our understanding is that this is not ordinal.

    components = list of strings; strings are used in the GooglePlaces API to search. General search terms are already provdied, but can be redefined to make a stronger and more meaningful map
    """
    names = []
    categories = []
    lat = []
    long = []
    lifeline = []
    search_term_list=[]
    for n in tuple_list:
        for i in n[0]:
            search_term_list.append(i)
    for search_term in search_term_list:
        query_result = api_key.nearby_search(
            location='Houston, Texas', keyword=search_term,
            radius=40000)

        for place in query_result.places:
            names.append(place.name)
            categories.append(search_term)
            lat.append(place.geo_location['lat'])
            long.append(place.geo_location['lng'])
            lifeline.append(lifeline_num)

        print(f'got 20 for search term: {search_term}')
        time.sleep(2)
        def component_builder(tuple_list):
            def unpack(cell):
                for n in tuple_list:
                    for i in n[0]:
                        if cell == i:
                            return n[1]
            return df['Category'].map(unpack)

    df = pd.DataFrame(columns=['Business'])
    df['Business'] = names
    df['Category'] = categories
    df['Source'] = 'Google'
    df['Latitude'] = lat
    df['Longitude'] = long
    df['Lifeline'] = lifeline
    df['Component'] = component_builder(tuple_list)

    return df

#defining search terms, components, and lifelines first
# LIFELINE 1: SAFTEY AND SECURITY
law_enforcement_security = ['police department','police organization']
search_rescue = ['emergency management']
fire_services = ['fire department']
government_services = ['government services']
responder_safety = []
imminent_hazard_mitigation = []
# # LIFELINE 2: FOOD, WATER, SHELTERING
shelter = ['animalshelters', 'communitycenters', 'homelessshelters', 'stadiumsarenas']
food_potable_water = ['waterpurification', 'fooddeliveryservices', 'foodbanks', 'waterdelivery', 'waterstores']
water_infrastructure = ['watersuppliers']
agriculture = []
durable_goods = []
evacuation = []
# LIFELINE 3: HEALTH AND MEDICAL
public_health= ['counciling and mental health', 'medcenters', 'hospitals', 'emergencyrooms', 'urgent_care']
fatality = ['cremationservices']
health_supply_chain = []
medical_care = []
patient_move = []
# LIFELINE 4: ENERGY
fuel = ['Fuel supplier', 'pipeline', 'gas company']
temp_power = ['Electrical equipment supplier']
power_grid = ['Electrical substation', 'power plant', 'nuclear power plant']
# LIFELINE 5: COMMUNICATION
comm_infrastructure = ['cell towers']
alerts_warnings_messages = ['radiostations', 'televisionstations']
dispatch_911 = []
responder_commmunications = []
financial_services = ['banks']
# LIFELINE 6: TRANSPORTATION
highway = ['roadsideassist', 'towing']
mass_transit = ['buses', 'metrostation','publictransport','metrostations', 'busstations']
railway = ['trainstations']
aviation = ['airport']
maritime = ['port']
pipeline = ['pipeline']
# LIFELINE 7: HAZARDOUS MATERIAL
facilities = ['hazardous waste','nuclear power plant']
hazardous_incident = []
tacos_spots = ['tacos', 'taqueria']





def find_lifelines(city, api_key, location_to_save_csv='datasets/',
law_enforcement_security=law_enforcement_security,
search_rescue=search_rescue,
fire_services=fire_services,
government_services= government_services,
responder_safety=responder_safety,
imminent_hazard_mitigation=imminent_hazard_mitigation,
shelter=shelter,
food_potable_water=food_potable_water,
water_infrastructure=water_infrastructure,
durable_goods = durable_goods,
agriculture = agriculture,
evacuation = evacuation,
public_health=public_health,
fatality=fatality,
health_supply_chain =health_supply_chain,
medical_care = medical_care,
patient_move = patient_move,
fuel=fuel,
temp_power=temp_power,
power_grid=power_grid,
comm_infrastructure=comm_infrastructure,
alerts_warnings_messages=alerts_warnings_messages,
dispatch_911=dispatch_911,
responder_commmunications=responder_commmunications,
financial_services=financial_services,
highway=highway,
mass_transit=mass_transit,
railway=railway,
aviation=aviation,
maritime= maritime,
pipeline=pipeline,
facilities=facilities,
hazardous_incident=hazardous_incident,
tacos = tacos_spots):
    """
    FEMA has 7 Lifelines. Each Lifeline has between 2 and 7 components that FEMA uses to monitor the status of each lifeline during an incident. This function takes in a city name to find the lifelines in that city.

    For each component there is a pre-determined list of general search terms for Google. This function takes in the city parameter and searches over these terms on Google and pulls down the information.

    Parameters
    ----------
    city : string, GooglePlaces API takes this format: 'City, State'

    apik_key : string, must get from GooglePlaces API.

    components = list of strings; strings are used in the GooglePlaces API to search. General search terms are already provdied, but can be redefined to make a stronger and more meaningful map

    Lifeline Components
    -------------------
    These component descriptions are provided by FEMA

    LIFELINE ONE: SAFETY AND SECURITY:

    law_enforcement_security= Evacuation routes, Force protection and security for staff, Security assessments at external facilities, Damaged law enforcement or correctional facilities, Curfew.

    search_rescue= Number and location of missing survivors, Life threatening hazards to responders and survivors, Availability and resources of search and rescue teams, Status of animal assists, structural assessments, and shelter in place checks.

    fire_services= Location of fire, Percent of fire contained, Fire’s rate and direction of spread, Weather conditions, Availability and resources of fire services

    government_services= Status of government offices and schools, Status of continuity of government and continuity of operations

    responder_safety= Safety hazards affecting operations, Requirements for Personal Protective Equipment (PPE), Security issues or concerns, Billeting for responders, Onsite training and policy

    imminent_hazard_mitigation=Status of flood risk grants, Status of area dams, levees, reservoirs

    LIFELINE TWO: FOOD, WATER, SHELTERING:
    shelter= Requirements for emergency shelter, Number and location of open shelters, Current population in shelters, Transitional Sheltering, Assistance options, Potential future sheltering requirements

    food_potable_water = Operating status of Points of Distribution (PODs), Operating status of supermarkets, neighborhood markets, and grocery stores, Operating status of restaurants, Impacts to the food supply chain, Operating status of public and private water supply systems, Operating status of water control systems (e.g., dams, levees, storm drains), Food/water health advisories

    water_infrastructure = Operating status of public wastewater systems and private septic systems, Operating status of wastewater processing facilities, Operating status of public and private water infrastructure (e.g., water mains)

    evacuation = Mandatory or voluntary evacuation orders, Number of people to evacuate, Evacuation routes, Evacuation time frame, Risk to responders and evacuees, Food, water, shelter availability

    durable_goods = Need for PODs, Pre-designated POD locations, Operating status of PODs, Resource distribution at PODs

    agriculture = Status of area agriculture, Status of food stock, Food safety

    LIFELINE THREE: HEALTH AND MEDICAL:
    public_health= Status of state and local health departments, Public health advisories

    fatality=Availability of mortuary and post-mortuary services, Availability of transportation, storage and disposal resources, Status of body recovery and processing, Descendant’s family assistance,

    patient_move = Status of state and local EMS systems, Active patient evacuations, Future patient evacuations

    medical_care =  Status of acute medical care facilities (e.g., level 1 trauma center), Status of chronic medical care facilities (e.g., long term care centers) Status of primary care and behavioral health facilities, Status of home health agencies, Status of VA Health System resources in the affected area

    health_supply_chain = Status of pharmaceutical supply chain

    LIFELINE FOUR: ENERGY:
    fuel=Status of commercial fuel stations, Responder fuel availability, Status of critical fuel facilities, Status of fuel supply line

    temp_power=Status of critical facilities, Availability of temporary power resources

    power_grid= Status of electrical power generation and distribution facilities, Number of people and locations without power, Estimated time to restoration of power, Number of electrically dependent persons (e.g., medical equipment)affected, Status of nuclear power plants, Status of nuclear power plants within 10 miles, Status of natural gas and fuel pipelines in the affected area

    LIFELINE FIVE: COMMUNICATIONS:
    comm_infrastructure= Status of telecommunications service, Reliability of internet service, Reliability of cellular service, Requirements for radio/satellite communication capability

    alerts_warnings_messages=Status of the emergency alert system (e.g., TV, radio, cable, cell), Status of public safety radio communications, Options for dissemination of information to the whole community, External affairs and media communication

    dispatch_911=Status of phone infrastructure and emergency line, Number of callers and availability of staff and facilities, Status of responder communications Availability of communications equipment

    responder_commmunications= Status of EOC(s), dispatcher, and field responder communications, Availability and status of first responder communications equipment

    financial_services= Access to cash, Access to electronic payment, National economic impacts

    LIFELINE SIX: TRANSPORTATION:
    highway=Status of major roads andhighways, Status of critical and noncritical bridges, Status of maintenance and emergency repairs

    mass_transit=Status of public transit systems including underground rail, buses, and ferry services

    railway= Status of area railways and stations

    aviation=Status of area airports, Status of incoming and outgoing flights

    maritime=  Status of area waterways, Status of area ports

    pipline = Status of natural gas and fuel pipelines

    LIFELINE SEVEN: HAZARDOUS MATERIAL:
    facilities=Status of hazardous material facilities, Amount, type, and containment procedures of hazardous materials, Reported or suspected hazardous material/toxic release incidents, Status of hazardous material supply chain

    hazardous_incident=Debris issues affecting the transportation system, Status of debris clearance operations, Reported or suspected hazardous material/toxic release incidents, Actual or potential radiological or nuclear incidents, Monitoring actions planned or underway for HAZMAT incidents


    """
    #defining search terms, components, and lifelines first
    # LIFELINE 1: SAFTEY AND SECURITY
    safety = [(law_enforcement_security, 'Law Enforce/Security'), (search_rescue, 'Search and Rescue'), (fire_services, 'Fire Services'), (government_services, 'Government Services'), (responder_safety, 'Responder Safety'), (imminent_hazard_mitigation, 'Imminent Hazard Mitigation')]

    # # LIFELINE 2: FOOD, WATER, SHELTERING
    fws = [(shelter,'Shelter'), (food_potable_water, 'Food and Potable Water'), (water_infrastructure, 'Water Infrastructure'), (durable_goods, 'Durable Goods'), (agriculture, 'Agriculture'), (evacuation, 'Evacuation')]

    # # LIFELINE 3: HEALTH AND MEDICAL
    health = [(public_health,'Public Health'), (fatality, 'Fatality Management'), (health_supply_chain, 'Health Care Supply Chain'), (medical_care, 'Medical Care'), (patient_move, 'Patient Movement')]

    # LIFELINE 4: ENERGY
    energy = [(fuel, 'Fuel'), (temp_power, 'Temporary Power'), (power_grid, 'Power')]

    # # LIFELINE 5: COMMUNICATION

    communication = [(comm_infrastructure, 'Infrastructure'), (alerts_warnings_messages, 'Alerts & Warnings'),(dispatch_911, '911 Dispatch'),(responder_commmunications, 'Responder Communications'), (financial_services, 'Financial Services')]

    # # LIFELINE 6: TRANSPORTATION

    transportation = [(highway,'Highway'), (mass_transit, 'Mass Transit'),(railway, 'Railway'), (aviation, 'Aviation'), (maritime, 'Maritime'), (pipeline, 'Pipeline')]

    # LIFELINE 7: HAZARDOUS MATERIAL

    waste = [(facilities, 'Facilities'), (hazardous_incident, 'Incident')]

    tacos = [(tacos_spots, 'Tacos')]

    category_list = [(safety, 'Safety & Security', 1),(fws, 'Food, Water & Shelter', 2),(health, 'Health & Medical', 3), (energy, 'Energy', 4),(communication, 'Communication', 5),(transportation, 'Transportation', 6), (waste, 'Hazardous Material', 7), (tacos,'Tacos', 8)]



    complete_list = []
    for tup in category_list:
        for n in tup[0]:
            for i in n[0]:
                complete_list.append(i)

    def scrape_google(complete_list, api_key):
        names = []
        categories = []
        lat = []
        long = []
        lifeline = []
        for search_term in complete_list:
            query_result = api_key.nearby_search(
                location= city, keyword=search_term,
                radius=40000)

            for place in query_result.places:
                names.append(place.name)
                categories.append(search_term)
                lat.append(place.geo_location['lat'])
                long.append(place.geo_location['lng'])

            print(f'got 20 for search term: {search_term}')
            time.sleep(2)
            def component_builder(category_list):
                def unpack(cell):
                    for tup in category_list:
                        for n in tup[0]:
                            for i in n[0]:
                                if cell == i:
                                    return n[1]
                return df['Category'].map(unpack)

            def lifeline_builder(category_list):
                def unpack(cell):
                    for tup in category_list:
                        for n in tup[0]:
                            for i in n[0]:
                                if cell == i:
                                    return tup[1]
                return df['Category'].map(unpack)


            df = pd.DataFrame(columns=['Business'])
            df['Business'] = names
            df['Category'] = categories
            df['Latitude'] = lat
            df['Longitude'] = long
            df['Lifeline'] = lifeline_builder(category_list)
            df['Component'] = component_builder(category_list)
            df = df.dropna()

        #return df
        return df.to_csv(f'{location_to_save_csv}{city}.csv', index=False)
    return scrape_google(complete_list, api_key)
    print('Done! Go get that csv baby!')
    print(f'Saved to:{location_to_save_csv}{city}.csv')
