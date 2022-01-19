#!python3
import pandas as pd

GLOBAL_ENTRIES_SET = set()

def process_entry_row(row):

   row_filled = row.notna()
   row_strip = row[row_filled == True]
   length = row_strip.shape[0] - 1
   # print(length)

   global GLOBAL_ALBUMS_SET
   position = 1
   username = row_strip[0]

   entry_list = []

   for entry in row_strip[1:length+1]:

      entry_slug = entry.lower().strip(" ")
      GLOBAL_ENTRIES_SET.add(entry_slug)
      score = 25*(length - position)/(length - 1) + 5

      entry_list += {
         'username': username,
         'entry': entry_slug,
         'position': position,
         'score': score
      },

      position += 1

   entry_df = pd.DataFrame(entry_list)
   
   return entry_df

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