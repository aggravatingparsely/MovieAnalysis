#!/usr/bin/env python
# coding: utf-8



#Importing libraries
import pandas as pd
import matplotlib as plt
import sys
import datetime 


if len(sys.argv) < 2:
    print('No dataset found. Usage: python MovieAnalysis.py <dataset file>')
    exit()
else:
    dataset = sys.argv[1]

#setting up current year
current_year = datetime.date.today().year

#importing data
movies = pd.read_excel(dataset)
oscars = pd.read_excel('oscars.xlsx')
gold_globe = pd.read_excel('golden_globes.xlsx')
sag = pd.read_excel('sag.xlsx')
cpi_index = pd.read_excel('cpi index.xlsx').set_index('Year')



# Constants

# Award constants - arbitrary values given to a movie if they've won a certain award
BEST_MOVIE = 5  
BEST_DIR = 4
BEST_SCREENPLAY = 4
BEST_ACTOR = 3
BEST_ACTRESS = 3
BEST_SUP_ACTOR = 2
BEST_SUP_ACTRESS = 2


# Mapping between column name indicating if an award has been won and the award constant it has been assigned
# for example - if a movie wins "best actress" oscar award, it will be indicated in that year for the best_actress_mov_id column
# and its oscar value will be increased by BEST_ACTRESS

# Mapping for important Oscar awards
OSCAR_CRITERIA = [['best_pic_mov_id', BEST_MOVIE], ['best_dir_mov_id', BEST_DIR], 
                  ['best_actor_mov_id', BEST_ACTOR], ['best_actress_mov_id', BEST_ACTRESS],
                  ['best_sup_actor_mov_id', BEST_SUP_ACTOR], ['best_sup_actress_mov_id', BEST_SUP_ACTRESS]]

# Mapping for important Golden Globe awards
GOLDEN_GLOBE_CRITERIA = [['best_pic_dr_mov_id', BEST_MOVIE], ['best_pic_mc_mov_id', BEST_MOVIE],
                         ['best_dir_mov_id', BEST_DIR], ['best_screenplay_mov_id', BEST_SCREENPLAY],
                         ['best_actor_dr_mov_id', BEST_ACTOR], ['best_actor_mc_mov_id', BEST_ACTOR],
                         ['best_actress_dr_mov_id', BEST_ACTRESS], ['best_actress_mc_mov_id', BEST_ACTRESS]]

# Mapping for important Screen actor guild (SAG) awards
SAG_CRITERIA = [['best_pic_mov_id', BEST_MOVIE], ['best_actor_mov_id', BEST_ACTOR],
                    ['best_actress_mov_id', BEST_ACTRESS], ['best_support_male_mov_id', BEST_SUP_ACTOR],
                    ['best_support_female_mov_id', BEST_SUP_ACTRESS]]

# Variable to track max adjusted gross for all movies
max_adjusted_gross = 0 

# Variable to track max popularity for all movies
max_pop = 0

# When calculating for best actor/actress how many in each of the categories, popularity, profit, and awards do we consider?
MOVIES_PER_CATEGORY = 10

# Routine to add the arbitrary value determined by the criteria above to the appropriate award value
#  award_field_name - column name of the award value being updated i.e. 'oscar_value'
#  ident - identification for movie recieving the award
#  value - amount award_value is increased by i.e. BEST_ACTOR
#  max_points - maximum points available per year
#
#  sets cell to normalized award value, in particular, a movie that wins all awards in a particular year 
#would return a value of 1.0
def update_single_award_value(award_field_name, ident, value, max_points):
    
    # do nothing if ident is not a number (NaN)
    if not pd.isna(ident):
        movies.loc[movies['id'] == ident, award_field_name] += (value / max_points)

# Routine to determine if element is a list of movie ids or a single movie id
#  award_field_name - column name of the award value being updated i.e. 'oscar_value'
#  row - row in the movies dataframe corresponding to current movie
#  field_name - the column containing the movie that won the award i.e. 'best_actor_mov_id'
#  value - amount award_value is increased by i.e. BEST_ACTOR
def update_award_values(award_field_name, row, field_name, value):
    best_id = row[field_name]
    max_points = row['max_value_possible']
 
    # if cell is a string, then it is a list of movies, separate each value by the comma, process each movie individually
    if type(best_id) == str:
        list_best_id = best_id.replace(' ', '').split(',')
        
        for best_id in list_best_id:
            update_single_award_value(award_field_name, best_id, value, max_points)
            
    # if cell has no number, do nothing
    elif pd.isna(best_id):
        pass
    
    # if cell has single value, then it refers to single movie, call update_single_award_value
    else:
        update_single_award_value(award_field_name, int(best_id), value, max_points)
        

# Routine to update the data field award_field_name in the award_dataframe based on the award_criteria
#  award_field_name - is the name of the field to contain the normalized summation of awards movie has recieved
#  award_dataframe - dataframe containing info on the awards
#  award_criteria - is a list of tuples where the first entry is the particular award, second entry is the value of the award
#
# This routine iterates through a particular award dataframe i.e. oscars for each row looks to see which movies 
#  recieved awards for that year, and gives them credit for that award based on the criteria set above [OSCAR_CRITERIA]
def add_award_data(award_field_name, award_dataframe, award_criteria):
    
    # adding a new sorting column to movies df where all values are 0 so points corresponding to each award won can be added
    movies[award_field_name] = 0.0

    # for each an award is given... 
    for index, row in award_dataframe.iterrows():
        
        # for each award in that year... 
        for criteria in award_criteria: 
            
            # update the award field in the movie df for a particular movie attribute with a specified value
            update_award_values(award_field_name, row, criteria[0], criteria[1])  

            
# Routine takes gross of each movie and updates it according to inflation of current year
#  release_year - year movie was released
#  gross - how much profit movie made
#
#  returns - movie profit adjusted for inflation
def adjust_for_inflation(release_year, gross):
    current_year_cpi = cpi_index.loc[current_year]['CPI']
    og_cpi = cpi_index.loc[release_year]['CPI']
    cpi_ratio = current_year_cpi / og_cpi
    adjusted_gross = cpi_ratio * gross

    return adjusted_gross



# Extracting release year from release_date column
movies['release_year'] = movies['release_date'].dt.year



# 
# Cell for computing gross for movies in df
#
# When cell is finished, the movies df will have a new column, 'adjusted_gross', which is gross for each movie,
# adjusted for inlation
#

# Adding gross profit as a column. Gross profit is difference between revenue and budget expense
# NOTE: for many cases in dataframe, especially older movies, revenue and/or budget is not known
# also, budgets are usually estimated by reputable sources
movies['gross'] = movies['revenue'] - movies['budget']

# Adding column for adjusted gross
movies['adjusted_gross'] = 0

# Only consider movies with a positive gross
movies_gross = movies[movies['gross'] > 0]

# Iterate through all movies in movies df which have a gross greater than 0, and calculate an adjusted gross for that movie
for index, row in movies_gross.iterrows(): 
    adjusted_gross = movies.loc[movies['id'] == row['id'], 'adjusted_gross'] =         adjust_for_inflation(row['release_year'], row['gross'])

    # Track the max_adjusted_gross for normalization later
    if adjusted_gross > max_adjusted_gross:
        max_adjusted_gross = adjusted_gross

# Group the adjusted gross based on release year, and print as reference material
print(movies.set_index(['id', 'title']).groupby(['release_year'])['adjusted_gross'].nlargest(3).reset_index())



# 
# Cell for computing the popularity for all movies in df
#
# When cell is finished, the movies df will have a new column, 'normalized_by_year_pop', which is a partial normalization
# of each movie's popularity score. It is calculated as the movie's popularity divided by the average popularity by year of its
# release. This means that older movies, which tend to have lower popularity because they are not 'current', have a useful 
# popularity value to compare with movies from more recent times
#

# New df listing the average popularity for every movie released within each year
# information in this df will be used to partially normalize each movie's popularity score 
avg_pop_by_year = movies.groupby(['release_year'])['popularity'].mean().to_frame()

# Adding column for popularity normalized by year
movies['normalized_by_year_pop'] = 0.0

# Creating a new dataframe with relevant info (id, title, popularity, release year, normalized_by_year_pop)
movies_pop = movies[['id', 'title', 'popularity', 'release_year', 'normalized_by_year_pop']]

# Iterate through all movies in movies df, and calculate the partial normalization for each movie by taking the quotient
# of the popularity score and the average popularity score for the corresponding release year
for index, row in movies_pop.iterrows(): 
    popularity = movies.loc[movies_pop['id'] == row['id'], 'normalized_by_year_pop'] =         row['popularity'] / avg_pop_by_year.loc[row['release_year']]['popularity']

    # Track the maximum popularity for full normalization later
    if popularity > max_pop:
        max_pop = popularity

# Group the normalized_by_year_pop based on release year, and print as reference material
print(movies.set_index(['id', 'title']).groupby(['release_year'])['normalized_by_year_pop'].nlargest(3).reset_index())



# Finding the most critically acclaimed movies per year, considering Oscars, Golden Globes, Screen Actors Guild

# Update movies df to show value of the oscar awards a particular movie got
add_award_data('oscar_value', oscars, OSCAR_CRITERIA)

# Update movies df to show value of the golden globe awards a particular movie got
add_award_data('golden_globe_value', gold_globe, GOLDEN_GLOBE_CRITERIA)

# Update movies df to show value of the SAG awards a particular movie got
add_award_data('sag_value', sag, SAG_CRITERIA)



# Compute an end-all-be-all value that indicates the 'greatness' of a movie based on popularity, gross, and award success
#  this value is calculated by adding normalized gross, popularity, and award values

movies['normalized_gross'] = movies['adjusted_gross'] / max_adjusted_gross
movies['normalized_pop'] = movies['normalized_by_year_pop'] / max_pop
movies['normalized_award'] = (movies['oscar_value'] + movies['golden_globe_value'] + movies['sag_value']) / 3

movies['final_movie_value'] = (movies['normalized_gross'] + movies['normalized_pop'] + movies['normalized_award']) / 3


# Sort the end-all-be-all value in descending order and print as reference material
print(movies.sort_values(by = ['final_movie_value'], ascending = False).head(10))

# Makes movies dataframe into excel sheet, commented out to save time while running
# movies.to_excel("movies_data.xlsx", sheet_name="movies", index=False) 



# Finding best actor/actress

# actors df - name, totals for profitability, awards, popularity, number of movies made, end-all-be-all
# for each category, picking top MOVIES_PER_CATEGORY movies (between n-3n movies)

top_n_adjusted_gross = movies.sort_values(by = ['adjusted_gross'], ascending = False).head(MOVIES_PER_CATEGORY)
top_n_awards_won = movies.sort_values(by = ['normalized_award'], ascending = False).head(MOVIES_PER_CATEGORY)
top_n_popular = movies.sort_values(by = ['normalized_pop'], ascending = False).head(MOVIES_PER_CATEGORY)

top_n_adjusted_gross_ids = top_n_adjusted_gross['id'].values.tolist()
top_n_awards_won_ids = top_n_awards_won['id'].values.tolist()
top_n_popular_ids = top_n_popular['id'].values.tolist()

top_n_ids = list(set(top_n_adjusted_gross_ids + top_n_awards_won_ids + top_n_popular_ids))

# List to contain all actors/actresses who've appeared in the top n movies
top_n_movie_cast = []

# Iterate through the top ids and extract credits for each movie
for i in top_n_ids:
    credits = list(movies[(movies['id'] == i)]['credits'])[0]
    
    credit_list = credits.split('-') 
    
    top_n_movie_cast += credit_list
    
# Unique list of actors/actresses who've appear in the top n movies
top_n_movie_cast = list(set(top_n_movie_cast))


# Create empty dataframe to put all information needed
actors = pd.DataFrame(columns = ['name', 'gross_earned', 'normalized_gross_earned', 'awards_won', 
                                 'avg_movie_popularity', 'movie_popularity', 'number_of_movies', 'final_value'])


for a in top_n_movie_cast:
    
    row = pd.Series([a, 0, 0, 0, 0, 0, 0, 0], index=actors.columns)
    actors = pd.concat([actors, pd.DataFrame([row])]).sort_values(by = ['name'])

# Iterate through all movies, update actors df for every movie the actor has been in
for index, row in movies.iterrows():
    # Go through every actor in this movie's credits, if it matches one of top n actors, add to their entry
    credits = row['credits'].split('-')
    
    for actor_in_movie in credits:
        if actor_in_movie in top_n_movie_cast: 
            # Since actor is of interest, add information to actors df
            actors.loc[actors['name'] == actor_in_movie, 'gross_earned'] += row['adjusted_gross']
            actors.loc[actors['name'] == actor_in_movie, 'normalized_gross_earned'] += row['normalized_gross']
            actors.loc[actors['name'] == actor_in_movie, 'awards_won'] += row['normalized_award']
            actors.loc[actors['name'] == actor_in_movie, 'movie_popularity'] += row['normalized_pop']
            actors.loc[actors['name'] == actor_in_movie, 'number_of_movies'] += 1




# With all information of the actors, run through actors df and find summation of normalized_gross_earned, awards_won,
#  and movie popularity

actors['final_value'] = actors['normalized_gross_earned'] + actors['awards_won'] + actors['movie_popularity'] 
actors['avg_movie_popularity'] = actors['movie_popularity'] / actors['number_of_movies']

print(actors.sort_values(by = ['final_value'], ascending = False).head(50))

# Make actors dataframe into excel sheet, commented out to save time while running
# actors.to_excel("actors_df.xlsx", sheet_name="actors", index=False) 
