import requests
from bs4 import BeautifulSoup


xml = requests.get("https://courses.illinois.edu/cisapp/explorer/schedule/2024/spring/ABE/128/75643.xml")

soup = BeautifulSoup(xml.content , features="xml")


print(soup.type.string)