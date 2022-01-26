#!python
import sys

from config import load_conf
from pandasWrapper import PandasWrapper

if __name__ == "__main__":

    pipeline = sys.argv[1]

    transforms_def = load_conf(pipeline)
    target_filename = transforms_def['TargetFile']
    pdw = PandasWrapper(target_filename=target_filename)

    pdw.apply_transforms(transforms_def)
