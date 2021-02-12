#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import re
import pandas as pd
import numpy as np
import sys
import glob
import traceback
import json
import folium
import datetime
from ast import literal_eval

sys.path.append('/lib')
import lib.helper as helper

# %load_ext folium_magic

CURRENT_DIR = os.getcwd()
DATA_DIR = CURRENT_DIR + '/data'
RAW_DATA_DIR = DATA_DIR + '/raw'
ANALYSES_DIR = "data/analyses/"
MAPS_DIR = DATA_DIR + "/maps"
UK_REGIONS_FILE = CURRENT_DIR + '/lib/UK-regions.json'


# In[35]:

#
# # Absolute or relative path to processed instructor and workshop data that we want to analyse/map (extracted from the Carpentries REDASH)
# instructors_file = "data/processed/processed_carpentry_instructors_UK_2020-12-10_redash.csv"
# workshops_file = "data/processed/processed_carpentry_workshops_UK_2020-12-10_redash.csv"


# In[ ]:


# For executing from command line after converting to python script
args = helper.parse_command_line_parameters_redash()
instructors_file = args.processed_instructors_file
workshops_file = args.processed_workshops_file


# In[5]:


instructors_df = pd.read_csv(instructors_file, encoding = "utf-8")
# instructors_df = instructors_df.drop(labels=['first_name', 'last_name'], axis=1)
# load 'taught_workshops_per_year' column as dictionary
instructors_df.loc[~instructors_df['taught_workshops_per_year'].isnull(),['taught_workshops_per_year']] = instructors_df.loc[~instructors_df['taught_workshops_per_year'].isnull(),'taught_workshops_per_year'].apply(lambda x: literal_eval(x))
instructors_df.loc[instructors_df['taught_workshops_per_year'].isnull(),['taught_workshops_per_year']] = instructors_df.loc[instructors_df['taught_workshops_per_year'].isnull(),'taught_workshops_per_year'].apply(lambda x: {})

# Let's change type of some columns and do some conversions

# Convert list of strings into list of dates for 'taught_workshop_dates' and 'earliest_badge_awarded' columns (turn NaN into [])
instructors_df['taught_workshop_dates'] = instructors_df['taught_workshop_dates'].str.split(',')
instructors_df.loc[instructors_df['taught_workshop_dates'].isnull(), ['taught_workshop_dates']] = instructors_df.loc[instructors_df['taught_workshop_dates'].isnull(), 'taught_workshop_dates'].apply(lambda x: [])
instructors_df['taught_workshop_dates'] = instructors_df['taught_workshop_dates'].apply(lambda list_str: [datetime.datetime.strptime(date_str, '%Y-%m-%d').date() for date_str in list_str])

# Convert list of strings into list of dates for ' ' column (turn NaN into [])
instructors_df['taught_workshops'] = instructors_df['taught_workshops'].str.split(',')
instructors_df.loc[instructors_df['taught_workshops'].isnull(), ['taught_workshops']] = instructors_df.loc[instructors_df['taught_workshops'].isnull(), 'taught_workshop_dates'].apply(lambda x: [])

# Convert 'earliest_badge_awarded' column from strings to datetime
instructors_df['earliest_badge_awarded'] = pd.to_datetime(instructors_df['earliest_badge_awarded'], format="%Y-%m-%d").apply(lambda x: x.date())
print(type(instructors_df['earliest_badge_awarded'][0]))


# In[6]:


# Let's inspect our instructors data
instructors_df.head(10)


# In[7]:


# Let's inspect our data a bit more
print("Columns: ")
print(instructors_df.columns)

print("\nData types: ")
print(instructors_df.dtypes)

print("\nExpecting a list for 'taught_workshop_dates' column: ")
print(type(instructors_df['taught_workshop_dates'][0]))

print("\nExpecting dates in the list in 'taught_workshop_dates' column: ")
print(instructors_df['taught_workshop_dates'][0])

print("\nExpecting datetime for 'earliest_badge_awarded' column: ")
print(instructors_df['earliest_badge_awarded'][0])

print("\n'earliest_badge_awarded' column should not have nulls:")
print(instructors_df[instructors_df['earliest_badge_awarded'].isnull()])

print("\nWhich instructors have null for institution?")
print(instructors_df[instructors_df['institution'].isna()].index)

print("\nWhich instructors have null for region?")
print(instructors_df[instructors_df['region'].isna()].index)

print("\nWhich instructors have null for geo-coordinates?")
print(instructors_df[instructors_df['longitude'].isna()].index)


# In[8]:


# How many instructors are there in total?
instructors_df.index.size


# In[9]:


# Get the date of the last taught workshop
instructors_workshops_df = pd.DataFrame(instructors_df[['taught_workshops', 'taught_workshop_dates', 'taught_workshops_per_year', 'earliest_badge_awarded']])
instructors_workshops_df['last_taught_workshop_date'] = instructors_workshops_df['taught_workshop_dates'].apply(lambda x: max(x) if (x != []) else None)
instructors_workshops_df.head(10)


# In[12]:


# Extract column for each year containing number of workshops taught that year by instructor 
years = ['2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020']
for year in years: 
    instructors_workshops_df[year] = instructors_workshops_df['taught_workshops_per_year'].apply(lambda x: x.get(int(year), 0))
instructors_workshops_df


# In[13]:


# Average number of workshop taught across all active years
instructors_workshops_df['avarage_taught_workshops_per_year'] = instructors_workshops_df[years].replace(0, np.NaN).mean(axis=1)
# instructors_workshops_df['avarage_taught_workshops_per_year'] = instructors_workshops_df['avarage_taught_workshops_per_year'].replace(np.NaN, 0)
instructors_workshops_df


# In[14]:


# print(instructors_workshops_df.dtypes)
# print(instructors_workshops_df['taught_workshop_dates'][0])
# print(type(instructors_workshops_df['last_taught_workshop_date'][0]))
# print(instructors_workshops_df.index)
# instructors_workshops_df


# In[15]:


# How many instructors taught 0 times?
len(instructors_workshops_df[instructors_workshops_df['last_taught_workshop_date'].isnull()].index)


# In[16]:


# Let's define active and inactive instructors
# Active = taught in the past 2 years. Inactive = everyone else.
def is_active(taught_workshop_dates):
    if taught_workshop_dates == [] or (datetime.date.today() - max(taught_workshop_dates)).days > 712:
        return False
    else:
        return True
    
instructors_workshops_df['is_active'] = instructors_workshops_df['taught_workshop_dates'].apply(lambda x: is_active(x))
instructors_workshops_df


# In[77]:


# How many active and inactive instructors?
active = instructors_workshops_df[instructors_workshops_df['is_active'] == True]
inactive = instructors_workshops_df[instructors_workshops_df['is_active'] != True]
print("Number of active instructors: " + str(len(active.index)))
print("Number of inactive instructors: " + str(len(inactive.index)))
active_vs_inactive = instructors_workshops_df['is_active'].value_counts()
print(active_vs_inactive)
active_vs_inactive.index = ['inactive', 'active']
active_vs_inactive.rename('number_of_instructors', inplace = True)
plot = active_vs_inactive.plot(kind='bar')
# plot.set_xticklabels(['inactive', 'active'])


# In[19]:


# Average number of workshops taught per year (for all instructors)
average_workshops_per_year_all = instructors_workshops_df[years].replace(0, np.NaN).mean(axis=0)
print(average_workshops_per_year_all)
average_workshops_per_year_all.plot(kind='bar')


# In[20]:


# Average number of workshops taught across all active years (for all instructors)
average_workshops_per_year_all.mean()


# In[21]:


# Average number of workshops taught per year (for active instructors only)
average_workshops_per_year_active = active[years].replace(0, np.NaN).mean(axis=0)
average_workshops_per_year_active.plot(kind='bar')


# In[22]:


# Average number of workshops taught across all active years (for active instructors only)
average_workshops_per_year_active.mean()


# In[23]:


# Average number of workshops taught per year (for inactive instructors only)
average_workshops_per_year_inactive = inactive[years].replace(0, np.NaN).mean(axis=0)
average_workshops_per_year_inactive = average_workshops_per_year_inactive.replace(np.nan, 0)
average_workshops_per_year_inactive.plot(kind='bar')


# In[24]:


# Average number of workshops taught across all active years (for inactive instructors only)
average_workshops_per_year_inactive.mean()


# In[25]:


# How long have instructors that are inactive now been active for? 
# In other words, how long do they teach before they become inactive?
def activity_days_for_inactive(date_list):
    return (max(date_list) - min(date_list)).days

print("Number of inactive instructors: " + str(len(inactive.index)))
time_before_inactivity = inactive[inactive['taught_workshop_dates'].apply(lambda x: len(x)) > 0]# exclude instructors that taught 0 workshops
print("Number of inactive instructors that taught at least 1 workshop: " + str(len(time_before_inactivity.index)))
time_before_inactivity = time_before_inactivity['taught_workshop_dates'].apply(lambda x: activity_days_for_inactive(x))
time_before_inactivity = time_before_inactivity.replace(0, np.NaN)
print("\nAverage period of teaching activity (for currently inactive instructors that taught at least 1 workshop): " + str(time_before_inactivity.mean()) + " days.")


# In[27]:


# How long have instructors that are active now been active for? 
# In other words, what is the current period of activity for active instuctors up to now
def activity_days_for_active(date_list):
    return (datetime.date.today() - min(date_list)).days
    
period_of_activity = active['taught_workshop_dates'].apply(lambda x: activity_days_for_active(x))
print("Number of active instructors: " + str(len(period_of_activity.index)))
period_of_activity = period_of_activity.replace(0, np.NaN)
print("\nAverage period of teaching activity up till now (for currently active instructors): " + str(period_of_activity.mean()) + " days.")


# In[28]:


# How long have all instructors been active for on average? 
# In other words, what is the period of teaching activity for all instuctors
period_of_activity_all = instructors_workshops_df[instructors_workshops_df['taught_workshop_dates'].apply(lambda x: len(x) > 0)]# exclude instructors that taught 0 workshops
print("Number of active and inactive instructors (that taught at least 1 workshop): " + str(len(period_of_activity_all.index)))
period_of_activity_all = period_of_activity_all.apply(lambda x: activity_days_for_active(x['taught_workshop_dates']) if x['is_active'] else activity_days_for_inactive(x['taught_workshop_dates']), axis = 1)
period_of_activity_all = period_of_activity_all.replace(0, np.NaN)
print("\nAverage period of teaching activity (for all instructors that taught at least 1 workshop): " + str(period_of_activity_all.mean()) + " days.")
# period_of_activity_all


# In[29]:


# How long from becoming an instructor to teaching for the first time on average?
def time_before_first_workshop(date, dates_list):
    if dates_list != []:
        days = min(dates_list) - date
        if days.days > 0: # disregard those instructors who were teaching before officially qualifying as instructors
            return days.days
    return np.NaN
    
instructors_workshops_df['days_to_first_workshop'] = instructors_workshops_df.apply(lambda x: time_before_first_workshop(x['earliest_badge_awarded'], x['taught_workshop_dates']), axis=1)
print("\nAverage period between becoming an instructor and teaching for the first time: " + str(instructors_workshops_df['days_to_first_workshop'].mean()) + " days.")


# In[30]:


# How many new instructors are there for each year?
instructors_per_year = instructors_df['year_earliest_badge_awarded'].value_counts()
instructors_per_year.sort_index(ascending = True, inplace=True)
instructors_per_year.index.name = 'year'
instructors_per_year = instructors_per_year.to_frame('number_of_instructors')
print(instructors_per_year)
instructors_per_year.plot(kind='bar', legend=True, title ="Instructors per year")


# In[60]:


# Let's look how many workshops are these instructors teaching per year?
workshops_df = pd.read_csv(workshops_file, encoding = "utf-8")

workshops_per_year = workshops_df['year'].value_counts()
workshops_per_year.sort_index(ascending = True, inplace=True)
workshops_per_year.index.name = 'year'
workshops_per_year.index = workshops_per_year.index.astype('int64') 
print(workshops_per_year.index)
# drop data for year 2021
workshops_per_year.drop(labels=[2021], inplace = True)
workshops_per_year = workshops_per_year.to_frame('number_of_workshops')
print(workshops_per_year)
workshops_per_year.plot(kind='bar', legend=True, title ="Workshops per year")


# In[61]:


# Total number of workshops
total_workshops = workshops_df.index.size
print("Total number of workshops: " + str(total_workshops))


# In[103]:


# Approximate number of people taught over years
learners_per_year = workshops_per_year * 20
learners_per_year.rename(columns = {'number_of_workshops' : 'number_of_learners'}, inplace = True)
print(learners_per_year)
learners_per_year.plot(kind='bar', legend=True, title ="Approx. learners per year")


# In[63]:


# Approximate total number of learners @ 20 attendees per workshop
total_learners = 20 * total_workshops
print("Approximate number of people taught: " + str(total_learners))


# In[110]:


# Save all analyses into an Excel spreadsheet
if not os.path.exists(ANALYSES_DIR):
    os.makedirs(ANALYSES_DIR)

outcome_113_excel_file = ANALYSES_DIR + 'outcome_1-1-3_' + datetime.date.today().strftime("%Y-%m-%d") + '.xlsx'

excel_writer = pd.ExcelWriter(outcome_113_excel_file, engine='xlsxwriter')

outcome_sheet = 'Outcome 1.1.3'

# Instructors per year
sheet_row = 1
instructors_per_year.to_excel(excel_writer, sheet_name=outcome_sheet, startrow=sheet_row - 1, startcol=0, index=True)

workbook = excel_writer.book
worksheet = excel_writer.sheets[outcome_sheet]

chart = workbook.add_chart({'type': 'column'})
chart.add_series({
        'categories': [outcome_sheet, sheet_row, 0, len(instructors_per_year.index), 0],
        'values': [outcome_sheet, sheet_row, 1, len(instructors_per_year.index), 1],
        'gap': 2,
    })
chart.set_y_axis({'major_gridlines': {'visible': False}})
chart.set_legend({'position': 'none'})
chart.set_x_axis({'name': 'Year'})
chart.set_y_axis({'name': 'Number of instructors', 'major_gridlines': {'visible': False}})
chart.set_title({'name': 'Number of instructors per year'})
worksheet.insert_chart('K' + str(sheet_row), chart)
worksheet.write(sheet_row + len(instructors_per_year.index), 0, "Total: ")
worksheet.write(sheet_row + len(instructors_per_year.index), 1,  instructors_per_year['number_of_instructors'].sum())

# Active vs inactive instructors
sheet_row = 21
active_vs_inactive.to_excel(excel_writer, sheet_name=outcome_sheet, startrow=sheet_row-1, startcol=0, index=True)
chart = workbook.add_chart({'type': 'column'})
chart.add_series({
        'categories': [outcome_sheet, sheet_row, 0, sheet_row - 1 + len(active_vs_inactive.index), 0],
        'values': [outcome_sheet, sheet_row, 1, sheet_row - 1 + len(active_vs_inactive.index), 1],
        'gap': 2,
    })
chart.set_y_axis({'major_gridlines': {'visible': False}})
chart.set_legend({'position': 'none'})
chart.set_x_axis({'name': 'Activity type'})
chart.set_y_axis({'name': 'Number of instructors', 'major_gridlines': {'visible': False}})
chart.set_title({'name': 'Active vs inactive instructors'})
worksheet.insert_chart('K' + str(sheet_row), chart)

# Workshops per year
sheet_row = 41
workshops_per_year.to_excel(excel_writer, sheet_name=outcome_sheet, startrow=sheet_row-1, startcol=0, index=True)
chart = workbook.add_chart({'type': 'column'})
chart.add_series({
        'categories': [outcome_sheet, sheet_row, 0, sheet_row - 1 + len(workshops_per_year.index), 0],
        'values': [outcome_sheet, sheet_row, 1, sheet_row - 1 + len(workshops_per_year.index), 1],
        'gap': 2,
    })
chart.set_y_axis({'major_gridlines': {'visible': False}})
chart.set_legend({'position': 'none'})
chart.set_x_axis({'name': 'Year'})
chart.set_y_axis({'name': 'Number of workshops', 'major_gridlines': {'visible': False}})
chart.set_title({'name': 'Workshops per year'})
worksheet.insert_chart('K' + str(sheet_row), chart)
worksheet.write(sheet_row + len(workshops_per_year.index), 0, "Total: ")
worksheet.write(sheet_row + len(workshops_per_year.index), 1,  workshops_per_year['number_of_workshops'].sum())

# Learners per year
sheet_row = 61
learners_per_year.to_excel(excel_writer, sheet_name=outcome_sheet, startrow=sheet_row-1, startcol=0, index=True)
chart = workbook.add_chart({'type': 'column'})
chart.add_series({
        'categories': [outcome_sheet, sheet_row, 0, sheet_row - 1 + len(learners_per_year.index), 0],
        'values': [outcome_sheet, sheet_row, 1, sheet_row - 1 + len(learners_per_year.index), 1],
        'gap': 2,
    })
chart.set_y_axis({'major_gridlines': {'visible': False}})
chart.set_legend({'position': 'none'})
chart.set_x_axis({'name': 'Year'})
chart.set_y_axis({'name': 'Number of learners', 'major_gridlines': {'visible': False}})
chart.set_title({'name': 'Approximate number of learners per year'})
worksheet.insert_chart('K' + str(sheet_row), chart)
worksheet.write(sheet_row + len(learners_per_year.index), 0, "Total: ")
worksheet.write(sheet_row + len(learners_per_year.index), 1,  learners_per_year['number_of_learners'].sum())

excel_writer.save()
print("Saved instructors analyses in " + outcome_113_excel_file)


# In[ ]:




