import os
import pandas as pd
import numpy as np
from importlib import import_module

from config import DATA_FOLDER


class PandasWrapper():

    def __init__(self,target_filename='pandas_output.xlsx'):

        self.source_type = ['csv','excel']
        self.target_type = ['excel']
        self.dataframes = {}
        self.to_save = {}
        self.target_file = os.path.join(DATA_FOLDER,target_filename)
        self.xlswriter = pd.ExcelWriter(self.target_file)

    def load_xls_tables(self,file_list,folder=DATA_FOLDER):
        
        for filename in file_list:
            filepath = os.path.join(folder,filename)
            tablename, extname = os.path.splitext(filename)
            print("Pandas loading file: {}".format(filepath))
            self.dataframes[tablename] = pd.read_excel(filepath)

    def save(self,df,sheetname):
        
        if df.empty:
            print("PandasSQL: Dataframe {} to be saved is Empty. Not saving.".format(sheetname))
            return
        df.to_excel(self.xlswriter,sheet_name=sheetname,index=True,index_label=df.index.name)

    def passthrough(self,origin_df):
        return origin_df

    def apply_transforms(self,transforms):

        table_list = transforms['Tables']
        kwargs = {}

        if 'Folder' in transforms.keys():
            kwargs['folder'] = transforms['Folder']
        
        self.load_xls_tables(table_list,**kwargs)

        df = None

        for step in transforms['Steps']:
            
            step_name = step['Step']

            # try:
            print("{} - Executing Step".format(step_name))
            operation = step['type']
            params = (step['params'] if 'params' in step.keys() else {})
            output_name = step['output']

            # replace the dataframe names by the actual dataframes in the params
            input_name = step['input']
            params['origin_df'] = self.dataframes[input_name]
            
            if 'right_input' in step.keys():
                right_name = step['right_input']
                params['right_df'] = self.dataframes[right_name]
            
            print("STEP PARAMS: {}".format(params))
            # retrieve the right function to apply and pass the parameters as dict
            function = getattr(self,operation)
            df = function(**params) 

            print(df.head(10))

            # store the output in the buffer_dfs for further chaining
            self.dataframes[output_name] = df

            if 'save' in step.keys() and (step['save']):
                print("Saving dataframe {}".format(output_name))
                self.save(df, output_name)

            # except Exception as e:
            #     errmsg = "{} error: {}".format(step_name, e)
            #     print(errmsg)
            #     continue
        
        self.xlswriter.save()

        return self.dataframes

    def reduce_df_axis(self,origin_df):

        df = origin_df.iloc[0]
        for i in range(1,origin_df.shape[0]):
            df = pd.concat([df,origin_df.iloc[i]])

        return df

    def series_from_set(self,origin_df,import_from=None, import_value=None):

        module = import_module(name=import_from)
        imported_set = getattr(module,import_value)

        datalist = list(imported_set)
        series = pd.Series(datalist)

        return series

    def apply_func_on_df(self,origin_df,func_name=None,import_from='.',**fargs):

        module = import_module(name=import_from)
        func = getattr(module,func_name)
        df = func(origin_df,**fargs)

        return df

    def apply_func_on_axis(self,origin_df,func_name=None,axis=1,import_from='.'):

        module = import_module(name=import_from)
        func = getattr(module,func_name)
        df = origin_df.apply(func,axis=axis)

        return df

    def merge_fields(self,origin_df,how='inner',left_key='Id',left_index=False,left_fields=None,right_df=None,right_key=None,right_index=False,right_fields=None,prefix=None):

        map = {}
        base_df = origin_df
        extend_df = right_df

        # if we only want to keep a subset of fields from the left dataframe
        if left_fields:

            left_fields += left_key,
            drop_cols = (x for x in origin_df.columns if x not in left_fields)
            base_df = origin_df.drop(drop_cols, axis=1)

        # if we only want to keep a subset of fields from the right dataframe, and rename those fields before merging
        if right_fields:

            if prefix:
                for field_name in right_fields:
                    map[field_name] = '{}_{}'.format(prefix,field_name)

            right_fields += right_key,
            drop_cols = (x for x in right_df.columns if x not in right_fields)
            extend_df = right_df.drop(drop_cols, axis=1)
            extend_df = extend_df.rename(map, axis=1)

        # build a dict with the join parameters for pandas
        joinparams = {
            'how': how
        }
        if (left_index or (left_key == base_df.index.name)):
            joinparams['left_index'] = True
        else:
            joinparams['left_on'] = left_key
        
        if (right_index or (right_key == extend_df.index.name)):
            joinparams['right_index'] = True
        elif right_key is None:
            # if no right key is provided, join on the same key as left
            joinparams['right_on'] = left_key
        else:
            joinparams['right_on'] = right_key

        # and here we go
        df = pd.merge(base_df, extend_df, **joinparams)

        return df

    def group_compute(self,origin_df,group_by,map=None,unstack=None,slug_index=False,fillna=True):
        
        values = list(set(map.keys()))
        df = pd.pivot_table(origin_df,index=group_by, values=values, aggfunc=map)

        if unstack:
            df = df.unstack(unstack)

        if slug_index:
            # flatten the df index, to avoid ugly column names if saved to the database
            df.columns = df.columns.map('_'.join).str.strip('_')

        if fillna:
            df = df.fillna(0.0)

        return df

    def reindex(self,origin_df,**params):

        df = origin_df.reindex(**params)

        return df

    def rename_columns(self,origin_df,separator="|",column_map={},dropcolumns=False,flatten_columns=False):

        df = origin_df

        if flatten_columns:
            df.columns = df.columns.map(separator.join).str.strip(separator)
            df = df.reindex(columns=column_map.keys())

        if dropcolumns:
            drop_cols = (x for x in df.columns if x not in column_map.keys())
            df.drop(drop_cols, axis=1, inplace=True)
        
        df.rename(column_map, axis=1, inplace=True)

        return df

    def sort_values(self,origin_df,sort_by,**params):

        df = origin_df.sort_values(sort_by,**params)
        return df

    def group_rank(self,origin_df,rank_by,name=None,group_by=None,method='dense',ascending=False):

        if group_by:
            series = origin_df.groupby(group_by).rank(method=method,ascending=ascending)[rank_by]
        else:
            series = origin_df.rank(method=method,ascending=ascending)[rank_by]

        if name is None:
            name = rank_by

        df = pd.DataFrame({name: series})

        return df

    def deduplicate(self,origin_df,by=None):

        df = origin_df.drop_duplicates(subset=by,keep='first')

        return df

    def add_datetimes(self,origin_df,datecol,dayfirst=True):

        df = origin_df
        df.loc[:,'datetime'] = pd.to_datetime(df.loc[:,datecol], dayfirst=dayfirst)
        df['date_'] = df.loc[:,'datetime'].dt.date
        df.loc[:,'year'] = df.loc[:,'datetime'].dt.year
        df.loc[:,'month'] = df.loc[:,'datetime'].dt.month
        df.loc[:,'day'] = df.loc[:,'datetime'].dt.day

        return df

    def filter(self,origin_df,filter_map):

        fdef = filter_map.pop(0)
        
        if fdef['right_type'] == 'str':
            query_str = "({} {} '{}')"
        else:
            query_str = "({} {} {})"
            
        query_str = query_str.format(fdef['left'], fdef['op'], fdef['right'])

        for fdef in filter_map:
            if fdef['right_type'] == 'str':
                query_step = " and ({} {} '{}')"
            else:
                query_step = " and ({} {} {})"

            query_str = query_str + query_step.format(fdef['left'], fdef['op'], fdef['right'])
        
        df = origin_df.query(query_str)

        return df

    def hash_columns(self,origin_df,columns):

        hashcol = np.zeros(origin_df.shape[0])

        for col in columns:
            hashcol += df[col].apply(lambda x: hash(x))

        df = origin_df
        df['hash'] = hashcol
        return df

    def concat(self,origin_df,df_list=[]):

        dataframes = [origin_df]

        for df_name in df_list:
            dataframes += self.dataframes[df_name],

        return pd.concat(dataframes)
