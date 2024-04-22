import numpy as np
import pandas as pd 


def access(call):
    try: 
        return call()
    except:
        return np.nan

def hours_to_string(value):
    if value < 1:
        return str(int(value * 60)) + 'minutes'
    else:
        hours = int(value)
        minutes = (value - hours) * 60
        if hours == 1:
            hour_string = 'hour'
        else:
            hour_string = 'hours'
        return str(int(hours)) + ' ' + hour_string + ' and ' + str(np.round(minutes)) + ' minutes'