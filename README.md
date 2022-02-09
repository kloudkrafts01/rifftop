# rifftop

This is a simple DIY project, made to compute a Musical top out of Community votes on facebook communities.

I am running with a couple of friends a FB group where we share and discuss music - mainly Metal and Rock. We wanted to have a "Albums of the Year" list that was representative of our Community, and that could be less linear and top-down than AOTY lists provided by certified curators like "mainstream" Metal media (Metal Hammer, Rock'n'Folk etc etc). Nothing wrong with these authoritative lists, we just wanted to have fun with more interesting statistics, and take it as a pretext to highlight interesting albums that would not get the stage from larger Media :)

The principle is simple and I have no claims over the elegance or efficiency of this code.

It defines a simple python wrapper around pandas, to encode pandas functions on YAML config files. The pandasWrapper takes up a dictionary, translated from YAML files, that defines a pipeline of Excel datasets and a linear sequence of typical tabular operations (joins, pivots, ranks, sorts...)

For more specific operations, pandasWrapper can load functions from a python file (in this case compute_stats.py), that can be applied to either a dataframe rows or an entire dataframe.

All config and specimen data provided should allow to run all the stats defined.
  - inputs.xlsx is a cleaned up version of the results of a simple Google Form that community members filled out (names have been changed to respect privacy)
  - albums_list_final.xlsx is the list of all albums voted by our members, with name cleaning, and descriptions of musical genre and country of origin. This data has been curated by the admin team
  - genres_list.xlsx is the defined list of genres we considered to classify entries. It's by far not perfect, don't @ me :)
  
main usage : ./main.py [pipeline_name]
with [pipeline_name] = the filename of any YAML file you will find in the "data" folder.

The recommended order od operations would be :
  - process_entries
  [Manual curation of the albums_list, that ultimately results in albums_list_final.xlsx. So you can skip this first one]
  - process_albums
  - album_stats
  - user_stats
 
