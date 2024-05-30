from dotenv import load_dotenv, find_dotenv
import os
from pymongo import MongoClient
from scripts.scraper import retrieve_info , proxy_request
import requests
from bs4 import BeautifulSoup


load_dotenv(find_dotenv())

password = os.environ.get("MONGODB_PWD")



CONNECTION_STRING = f"mongodb+srv://courseserv:{password}@uiuc-schedule.qhi3i2e.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(CONNECTION_STRING)


aas_DB = client['ACES']


course_collection = aas_DB.courses

course_for_AAS = retrieve_info('ACES')
print("here")

for key , value in course_for_AAS.items():
    
    new_collection = aas_DB[key]

    for section_info in value:
        new_document = {
            "Section Number" : section_info["Section Number"],
            "Start Time" : section_info["Start Time"],
            "End Time" : section_info["End Time"],
            "Days of Week" : section_info["Days of Week"],
            "Room Number" : section_info["Room Number"],
            "Building Name" : section_info["Building Name"],
            "Course Description" : section_info["Course Description"],
            "Meeting Type" : section_info["Meeting Type"]
        }
        new_collection.insert_one(new_document)

#soup = proxy_request("https://courses.illinois.edu/cisapp/explorer/schedule/2024/spring/AAS/200.xml")

#print(soup.description.string)


'''
source_db = client['AAS']
target_db = client['CS']

# Iterate over all collections in the source database
for collection_name in source_db.list_collection_names():
    # Get the collection from the source database
    source_collection = source_db[collection_name]

    # Create the same collection in the target database
    # (It will be created automatically when you insert the first document)
    target_collection = target_db[collection_name]

    # Copy all documents from the source collection to the target collection
    for document in source_collection.find():
        target_collection.insert_one(document)
'''

