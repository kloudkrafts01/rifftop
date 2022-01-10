#!python3

import os
import statistics as st
import openpyxl as opx
import pandas as pd

from build_db import engine

results_excelpath = "top2020_RESULTS.xlsx"

df_entries = pd.read_sql_table('entries',engine)
df_albums = pd.read_sql_table('albums',engine,index_col='id')
df_users = pd.read_sql_table('users',engine,index_col='id')
df_genres = pd.read_sql_table('genres',engine,index_col='id')

def compute_all_stats():

   entries = build_entries()
   entries = format_entries(entries)

   print(entries.head(20))

   album_results = build_album_stats(entries)
   album_results = format_album_results(album_results)
   album_results.to_sql('album_stats', engine, if_exists='replace')

   genre_stats = compute_genre_stats(album_results)

   full_entries = extend_entries(entries, album_results)
   full_entries = compute_entry_stats(full_entries)
   full_entries.to_sql('entry_stats', engine, if_exists='replace')

   user_genres, user_edgyness = compute_user_stats(full_entries)

   # write it all to a big Excel
   writer = pd.ExcelWriter(results_excelpath)
   album_results.to_excel(writer, sheet_name='album_results')
   full_entries.to_excel(writer, sheet_name='full_entries')
   genre_stats.to_excel(writer, sheet_name='genre_stats')
   user_genres.to_excel(writer, sheet_name='user_genres')
   user_edgyness.to_excel(writer, sheet_name='user_edgyness')

   writer.save()


   # album_results.to_excel('top2020_album_results.xlsx')

def build_entries():

   entries = pd.merge(df_entries, df_albums, left_on='album_id', right_on='id')
   entries = pd.merge(entries, df_genres, left_on='genre_id', right_on='id')

   return entries

def format_entries(entries):

   map = {
      'id':'entry_id',
      'user_id':'user_id',
      'album_id':'album_id',
      'name_y':'album',
      'genre_id':'genre_id',
      'name':'genre',
      'position':'position',
      'score':'score'
   }

   drop_cols = (x for x in entries.columns if x not in map.keys())

   entries.drop(drop_cols, axis=1, inplace=True)
   entries.rename(map, axis=1, inplace=True)
   entries.set_index('entry_id', drop=False, inplace=True)

   return entries

def build_album_stats(entries):

   aggfunc = {
      'position': ['mean','min','max'],
      'score': ['count','sum','mean','max','min']
   }

   album_stats = pd.pivot_table(entries, index = ['genre_id','genre','album_id','album'], values = ['score','position'], aggfunc=aggfunc)

   album_ranking = album_stats.rank(method='dense',ascending=False)[('score','sum')]
   album_genre_ranking = album_stats.groupby('genre_id').rank(method='dense',ascending=False)[('score','sum')]

   album_results = pd.merge(album_stats, album_ranking, left_index=True, right_index=True)
   album_results = pd.merge(album_results, album_genre_ranking, left_index=True, right_index=True)

   album_results.reset_index(inplace=True)

   return album_results

def format_album_results(album_results):

   album_results.columns = album_results.columns.map('|'.join).str.strip('|')

   map = {
      'score_y|sum':'rank',
      'album_id':'album_id',
      'album':'album',
      'score|sum':'genre_rank',
      'genre_id':'genre_id',
      'genre':'genre',
      'score_x|count':'nb_votes',
      'score_x|sum':'total_score',
      'score_x|mean':'mean_score',
      'score_x|max':'highest_score',
      'score_x|min':'lowest_score',
      'position|mean':'mean_position',
      'position|min':'highest_position',
      'position|max':'lowest_position'
   }

   album_results = album_results.reindex(columns=map.keys())

   drop_cols = (x for x in album_results.columns if x not in map.keys())
   album_results.drop(drop_cols, axis=1, inplace=True)

   album_results.rename(map, axis=1, inplace=True)

   album_results.set_index('album_id', inplace=True, drop=True)

   album_results.sort_values('rank', inplace=True)

   return album_results

def compute_genre_stats(df):

    genre_stats = pd.pivot_table(df, index=['genre'], values=['nb_votes','total_score'], aggfunc=['sum'])
    genre_stats.sort_values(('sum','nb_votes'), ascending=False, inplace=True)

    genre_stats['weight'] = genre_stats[('sum','total_score')] * 100.0 / genre_stats[('sum','total_score')].sum()

    return genre_stats

def extend_entries(entries, album_results):

    album_keepcols = [
        'album_id',
        'total_score'
    ]
    album_dropcols = (x for x in album_results.columns if x not in album_keepcols)
    album_scores = album_results.drop(album_dropcols, axis=1)

    full_entries = pd.merge(entries, album_scores, on='album_id')

    full_entries = pd.merge(full_entries, df_users, left_on='user_id', right_on='id')

    full_entries.set_index('entry_id', inplace=True)
    cols = [
        'user_id',
        'name',
        'album_id',
        'album',
        'genre_id',
        'genre',
        'top_size',
        'position',
        'score',
        'total_score'
    ]

    full_entries = full_entries.reindex(columns=cols)

    return full_entries

def compute_entry_stats(df):

   df['pop_score'] = df['score'] * df['total_score'] / 1000
   # idea for a future implementation
   # df['pop_score'] = df['score'] * ( df['total_score'] - df['total_score'].quantile(q=0.666) ) / 1000
   df['edgyness'] = df['top_size'] / df['pop_score']

   df.sort_values('entry_id', inplace=True)

   return df

def compute_user_stats(full_entries):
    
   user_genres = pd.pivot_table(full_entries, index=['name'], columns=['genre'], values=['score'], aggfunc=['sum'])

   aggfunc = {
      'pop_score': 'sum',
      'edgyness': 'mean'
   }
   user_edgyness = pd.pivot_table(full_entries, index = ['name'], values=['pop_score','edgyness'], aggfunc=aggfunc)

   user_edgyness.sort_values(('edgyness'), ascending=False, inplace=True)

   return user_genres,user_edgyness

if __name__ == "__main__":

   compute_all_stats()