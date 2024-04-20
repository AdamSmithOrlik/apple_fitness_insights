import numpy as np
import pandas as pd 

def load_dataframe(root, type):
    return pd.DataFrame([x.attrib for x in root.iter(type)])

def access(call):
    try: 
        return call()
    except:
        return np.nan