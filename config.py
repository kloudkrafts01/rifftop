import os,sys,re
import yaml,json


# Python path config
CONF_FOLDER = os.path.abspath('conf')
DATA_FOLDER = os.path.abspath('data')

sys.path.insert(0,CONF_FOLDER)
sys.path.insert(0,DATA_FOLDER)


def load_conf(name,type="yaml",folder=CONF_FOLDER,subfolder=None):
    """Simply Loads a YAML file and passes the result as a dict"""

    conf_dict = {}

    if subfolder:
        folder = os.path.join(folder,subfolder)
    
    if type=="json":
        json_ext = re.compile('(\.yml)$')
        if re.search(json_ext, name) is None:
            name = '{}.json'.format(name)
        
        conf_path = os.path.join(folder,name)

        with open(conf_path,'r') as conf:
            conf_dict = json.loads(conf)

    elif type=="yaml":
        # Add the .yml extension to the conf name if not already present
        yml_ext = re.compile('(\.yml|\.yaml)$')
        if re.search(yml_ext, name) is None:
            name = '{}.yml'.format(name)

        conf_path = os.path.join(folder,name)

        with open(conf_path,'r') as conf:
            conf_dict = yaml.full_load(conf)
    
    else:
        ValueError("common.config :: Invalid value provided for Config Type ! Valid options are 'json' or 'yaml'.")

    return conf_dict
