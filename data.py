import numpy as np
import pandas as pd
import datetime as dt
from tools import *
import os 

import xml.etree.ElementTree as ET

class Data:
    def __init__(self, filename):
        self.filename = filename
        self._tree = ET.parse(filename)
        self._root = self._tree.getroot()
        self._data_types = set([x.tag for x in self._root.iter()])
        self.workout_df = pd.DataFrame([x.attrib for x in self._root.iter('Workout')])
        self.stats_df = pd.DataFrame([x.attrib for x in self._root.iter('WorkoutStatistics')])
        self.activity_df = pd.DataFrame([x.attrib for x in self._root.iter('ActivitySummary')])
        self.me_df = pd.DataFrame([x.attrib for x in self._root.iter('Me')])


    # GETTERS
    def age(self):
        try:
            birthdate_str = self.me_df.HKCharacteristicTypeIdentifierDateOfBirth.values[0]
            # convert to datetime object 
            birthdate = dt.datetime.strptime(birthdate_str, "%Y-%m-%d")
            # calculate current age with todays date
            age = dt.datetime.now().year - birthdate.year
            # check if birthday has happened this year
            if dt.datetime.now().month < birthdate.month or (dt.datetime.now().month == birthdate.month and dt.datetime.now().day < birthdate.day):
                age -= 1
            # check if its their birthday today 
            if dt.datetime.now().month == birthdate.month and dt.datetime.now().day == birthdate.day:
                birthday_flag = True
            else: 
                birthday_flag = False
        except:
            return np.nan, np.nan
        return age, birthday_flag
    
    def get_usage(self):
        dates = pd.to_datetime(self.activity_df.dateComponents.values)
        # get the first day the watch was used 
        first_use = dates.min().date()
        # get the number of days the watch has been used
        dates_used = len(dates.unique())
        # total days since the watch was first used
        total_days = (dt.datetime.now().date() - first_use).days
        # number of days a workout has been tracked 
        days_workout_tracked = len(pd.to_datetime(self.workout_df.creationDate).dt.date.unique())
        # total hours tracking activity
        total_hours = np.round(self.activity_df.appleExerciseTime.astype(float).sum() / 60)
        # number of workouts tracked
        total_num_workouts = len(self.workout_df)
        # most active month 
        most_active_month = dates.month.value_counts().idxmax()

        return {'first_use': first_use, 'dates_used': dates_used, 'total_days': total_days, 'days_workout_tracked': days_workout_tracked, 'total_hours': total_hours, 'total_num_workouts': total_num_workouts}

    def get_workout_dataframe(self):
        # merge workout statistics into the workout dataframe
        df = self.workout_df.copy()
        stats = self.stats_df.copy()

        # convert dates to datetime object 
        for col in ['creationDate', 'startDate', 'endDate']:
            df[col] = pd.to_datetime(df[col])

        for col in ["startDate", "endDate"]:
            stats[col] = pd.to_datetime(stats[col])

        # drop the unnecessary columns
        df.drop(columns=['sourceName', 'sourceVersion', 'device'], inplace=True)

        # change name of all the type elements to remove HKQuantityTypeIdentifier
        df['Type'] = df['workoutActivityType'].str.replace('HKWorkoutActivityType', '')

        # change name of all the type elements to remove HKQuantityTypeIdentifier
        stats['type'] = stats['type'].str.replace('HKQuantityTypeIdentifier', '')

        # names of stats to merge with dataframe
        statistics_columns = ["activeCalories", "basalCalories", "distance", "avgHeartRate", "minHeartRate", "maxHeartRate", "avgRunSpeed", "minRunSpeed", "maxRunSpeed"]
        statistics = []

        for i in range(len(df)):
            workout = df.iloc[i]
            start = workout.startDate

            # get the statistics for the workout
            recordedStats = stats[stats.startDate == start]

            # Create np.nans if no data is available for a workout 
            if len(recordedStats) == 0:
                workout_stats =  [np.nan] * len(statistics_columns)

            else:
                activeCalories = access(lambda: recordedStats.loc[recordedStats["type"] == "ActiveEnergyBurned"]["sum"].values[0])
                basalCalories = access(lambda: recordedStats.loc[recordedStats["type"] == "BasalEnergyBurned"]["sum"].values[0])
                distance = access(lambda: recordedStats.loc[recordedStats["type"] == "DistanceWalkingRunning"]["sum"].values[0])
                avgHeartRate = access(lambda: recordedStats.loc[recordedStats["type"] == "HeartRate"]["average"].values[0])
                minHeartRate = access(lambda: recordedStats.loc[recordedStats["type"] == "HeartRate"]["minimum"].values[0])
                maxHeartRate = access(lambda: recordedStats.loc[recordedStats["type"] == "HeartRate"]["maximum"].values[0])
                avgSpeed = access(lambda: recordedStats.loc[recordedStats["type"] == "RunningSpeed"]["average"].values[0])
                minSpeed = access(lambda: recordedStats.loc[recordedStats["type"] == "RunningSpeed"]["minimum"].values[0])
                maxSpeed = access(lambda: recordedStats.loc[recordedStats["type"] == "RunningSpeed"]["maximum"].values[0])
        
                workout_stats = [activeCalories, basalCalories, distance, avgHeartRate, minHeartRate, maxHeartRate, avgSpeed, minSpeed, maxSpeed]

            statistics.append(workout_stats)
        
        statistics = np.array(statistics)

        # add the statistics to the dataframe
        for i, col in enumerate(statistics_columns):
            df[col] = statistics[:,i]
        
        # change all numerical columns to float
        for col in ["duration", "activeCalories", "basalCalories", "distance", "avgHeartRate", "minHeartRate", "maxHeartRate", "avgRunSpeed", "minRunSpeed", "maxRunSpeed"]:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # add total calories to the dataframe
        df["totalCalories"] = df["activeCalories"] + df["basalCalories"]

        return df 

    def get_activity_dataframe(self):
        activity = self.activity_df.copy()
        # change data column to datetime object 
        activity["dateComponents"] = pd.to_datetime(activity["dateComponents"])
        # convert numeric columns to floats 
        for col in ["activeEnergyBurned", "activeEnergyBurnedGoal", "appleExerciseTime", "appleMoveTime", "appleMoveTimeGoal", "appleExerciseTimeGoal", "appleStandHours", "appleStandHoursGoal"]:
            activity[col] = pd.to_numeric(activity[col], errors='coerce')

        return activity
