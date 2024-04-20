import numpy as np
import pandas as pd 

# loads a dataframe from an xml file
def load_dataframe(type):
    return pd.DataFrame([x.attrib for x in root.iter(type)])