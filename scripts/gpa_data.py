from pymongo import MongoClient
from dotenv import load_dotenv, find_dotenv
import os
import pandas as pd


load_dotenv(find_dotenv())

password = os.environ.get("MONGODB_PWD")



CONNECTION_STRING = f"mongodb+srv://courseserv:{password}@uiuc-schedule.qhi3i2e.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(CONNECTION_STRING)

df = pd.read_csv('uiuc-gpa-dataset.csv')

database_names = client.list_database_names()
exclude = ['coursesDB' , 'test' , 'admin' , 'local']


matched_row = df[(df['Subject'] == 'AAS') & (df['Number'] == 100)].iloc[0]







for name in database_names:
    if name in exclude:
        continue
    source_db = client[name]
    # Iterate over all collections in the source database
    for collection_name in source_db.list_collection_names():
        # Get the collection from the source database
        source_collection = source_db[collection_name]
        matched_row = df[(df['Subject'] == name) & (df['Number'] == int(collection_name))]
        print(matched_row)
        a_plus = matched_row['A+'] * 4
        a = matched_row['A'] * 4
        a_minus = matched_row['A-'] * 3.67
        b_plus = matched_row['B+'] * 3.33
        b = matched_row['B'] * 3
        b_minus = matched_row['B-'] * 2.67
        c_plus = matched_row['C+'] * 2.33
        c = matched_row['C'] * 2
        c_minus = matched_row['C-'] * 1.67
        d_plus = matched_row['D+'] * 1.33
        d = matched_row['D']
        d_minus = matched_row['D-'] * 0.67
        
        total_students = 0
        total_students += matched_row['A+']
        total_students += matched_row['A']
        total_students += matched_row['A-']
        total_students += matched_row['B+']
        total_students += matched_row['B']
        total_students += matched_row['B-']
        total_students += matched_row['C+']
        total_students += matched_row['C']
        total_students += matched_row['C-']
        total_students += matched_row['D+']
        total_students += matched_row['D']
        total_students += matched_row['D-']
        total_students += matched_row['F']
        
        average_gpa = (a_plus + a + a_minus + b_plus + 
                        b + b_minus + c_plus + c + c_minus
                        + d_plus + d + d_minus
                       ) / total_students

        print(total_students)
        for document in source_collection.find():
            gpa = {"Average GPA" : str(int(average_gpa))}

            source_collection.update_one({'_id': document['_id']}, {'$set': gpa})
