import googlemaps
from pprint import pprint
from pymongo import MongoClient
import sys
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

API_KEY = os.environ.get("GOOGLE_API")
password = os.environ.get("MONGODB_PWD")



CONNECTION_STRING = f"mongodb+srv://courseserv:{password}@uiuc-schedule.qhi3i2e.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(CONNECTION_STRING)




# Define our client

gmaps = googlemaps.Client(key = API_KEY)

# Define our search
#location_name = "Digital Computer Laboratory UIUC"

#esponse = gmaps.places(query = location_name#
#pprint(response['results'][0]['geometry']['location']['lat'])
#print(response['results'][0]['geometry']['l#ocation']['lng'])



database_names = client.list_database_names()
exclude = ['coursesDB' , 'test' , 'admin' , 'local']

cache = {}


for name in database_names:
    if name in exclude:
        continue
    source_db = client[name]
    # Iterate over all collections in the source database
    for collection_name in source_db.list_collection_names():
        # Get the collection from the source database
        source_collection = source_db[collection_name]
        
        
        for document in source_collection.find():

            building_name = document.get("Building Name") + " UIUC"
            response = gmaps.places(query = building_name)

            if building_name in cache:
                source_collection.update_one({'_id': document['_id']}, {'$set': cache[building_name]})
            else:
                response = gmaps.places(query = building_name)
                cache[building_name] = {"lat" : response['results'][0]['geometry']['location']['lat'],
                                        "lng" : response['results'][0]['geometry']['location']['lng']
                                        }
                source_collection.update_one({'_id': document['_id']}, {'$set': cache[building_name]})
            
            





