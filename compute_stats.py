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
         'score': score,
         'top_size': length
      },

      position += 1

   entry_df = pd.DataFrame(entry_list)
   
   return entry_df

def compute_vote_weight(df):

    df['vote_weight'] = df['nb_votes'] * 100.0 / df['nb_votes'].sum()

    return df

def compute_score_weight(df,group_by=None,level=0):

   if group_by:
      df['score_weight'] = df['total_score'] * 100.0 / df.groupby(by=group_by).sum()['total_score']
   else:
      df['score_weight'] = df['total_score'] * 100.0 / df.groupby(level=level).sum()['total_score']

   return df

def compute_rarity(df):

   df['rarity'] = 1 / ( df['nb_votes'] * df['vote_weight'] )

   return df

def compute_entry_stats(df):

   # df['pop_score'] = df['score'] * df['total_score'] / 1000
   # idea for a future implementation
   df['pop_score'] = df['score'] * ( df['total_score'] - df['total_score'].quantile(q=0.666) ) / 1000
   # df['pop_score'] = df['score'] * ( df['total_score'] - df['total_score'].df['nb_votes'] ) / 1000
   df['edgyness'] = df['top_size'] / df['pop_score']

   return df
