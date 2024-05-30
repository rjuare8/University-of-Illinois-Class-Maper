<h1 align="center">University of Illinois Class Mapper</h1>


# Introduction
Creating a course schedule can be difficult and tedious, especially when trying to avoid time conflicts and unreasonable travel distances between classes. The UIUC Class Mapper is an interactive application that analyzes the distance and time between courses at U of I to help students build optimal schedules.

### Key Features:
- **Interactive map**
- **View travel time between classes**
- **Save class locations on map**
- **Save created schedules**

For more details, view the full project proposal [here](https://docs.google.com/document/d/1HQzlKNUJCsnrAYw-erv83Lm2DPr2Lv68ydDF7qgXZSQ/edit?usp=sharing).

# Technical Architecture
![technical architecture (1)](https://github.com/CS222-UIUC-FA23/group-project-team23/assets/112020441/efafa2da-6722-4e31-ad39-821518e9488f)



# Contributors
- **Alejandro Chavez:** Worked on acquiring/handling course data and web scraping
- **Rudy Juarez:** Worked on the back-end scheduling/map implementation

# Installation Instructions
## 1. Set up environment
Run the following:

First create a virtual environment temp folder, then activate it.

```
virtualenv venv

# Windows
venv\Scripts\activate
# Or Linux
source venv/bin/activate

```
Clone the git repo, then install the requirements with pip

```bash

git clone (PASTE THE "Clone with HTTPS" link here)
cd ./uiuc_class_mapper (The directory that you cloned the repo into)
```
## 2. Install required packages
To install packages, run the following:
```
pip install -r requirements.txt
```
  
## 3. Run application
```
python app.py
```
