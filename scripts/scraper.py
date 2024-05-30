from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

courseCatalog = "https://courses.illinois.edu/cisapp/explorer/schedule/2024/spring.xml"

# Use proxy_requests to scrape

password = os.environ.get("AUTH_PASS")
username = os.environ.get("AUTH_NAME")

def proxy_request(url):
    payload = {
        "source" : "universal",
        "url" : url,
        "geo_location" : "United States"
    }

    response = requests.request(
        "POST" , "https://realtime.oxylabs.io/v1/queries",
        auth = (username , password),
        json = payload
    )

    response_html = response.json()['results'][0]['content']

    return BeautifulSoup(response_html , features= "xml")



# parse data
#soup = proxy_request(courseCatalog)

# Extract the subjectCode for all subjects
#subjects = [subject.attrs['id'] for subject in soup.subjects]


# Send a request to retrieve all courses in that subjectCode
def retrieve_info(subjectCode):
    toReturn = {}
    classesWithinSubject = courseCatalog[:-4] + '/' + subjectCode + '.xml'


    soupClass = proxy_request(classesWithinSubject)
    
    # Get all classes from subject 
    courses = [course.attrs['id'] for course in soupClass.courses]
    print(courses)
    # Request to get first section of course
    for courseNumber in courses:
     
        course = "https://courses.illinois.edu/cisapp/explorer/schedule/2024/spring/" + subjectCode + '/' + courseNumber + '.xml'
        
        # Here I can also get course descriptions
        soupSections = proxy_request(course)
        try:
            description = soupSections.description.string
        except:
            description = ""
        sections = [section.attrs['id'] for section in soupSections.sections]

        sectionsInfo = []

        # Now lets get section information
        for sectionNumber in sections:
            
            sectionLink  = course[:-4] + '/' + sectionNumber + '.xml'

            soupSectionInfo =  proxy_request(sectionLink)

            # Finally get all necessary information 
            try:
                section_number = soupSectionInfo.sectionNumber.string
            except:
                section_number = ""

            try:
                startTime = soupSectionInfo.start.string
            except:
                startTime = ""
            try:
                endTime = soupSectionInfo.end.string
            except:
                endTime = ""
            try:
                daysOfWeek = soupSectionInfo.daysOfTheWeek.string
            except:
                daysOfWeek = ""
            try:
                RoomNumber = soupSectionInfo.roomNumber.string
            except:
                RoomNumber = ""
            try:
                buildingName = soupSectionInfo.buildingName.string
            except:
                 buildingName = ""
            try:
                meetingType = soupSectionInfo.type.string
            except:
                meetingType = ""
            section_dict = {
                "Section Number" : section_number,
                "Start Time" : startTime,
                "End Time" : endTime,
                "Days of Week" : daysOfWeek,
                "Room Number" : RoomNumber,
                "Building Name" : buildingName,
                "Course Description" : description,
                "Meeting Type" : meetingType
            }

            sectionsInfo.append(section_dict)
        print(sectionsInfo)
        toReturn[courseNumber] = sectionsInfo
    return toReturn





#print(f"Information Regarding course : {subjectCode + ' ' +courseNumber}")
#    
#print(f"Section Number : {sectionNumber}")
#print(f"Start Time : {startTime}")
#print(f"End Time : {endTime}")
#print(f"Days Of Week : {daysOfWeek}")
#print(f"Room Number : {RoomNumber}")
#print(f"Building Name : {buildingName}")