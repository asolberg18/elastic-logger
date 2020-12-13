import uuid
import random
from datetime import datetime

# The LogEvent class encapsulates the CitiBike
# ride entity.


class LogEvent:

    # class variable to track the number of entities
    # that have been logged
    logged = 0

    # The citibike rideshare event schema
    schema = {
        "mappings": {
            "properties": {
                "tripduration": {"type": "integer"},
                "starttime": {"type": "date"},
                "stoptime": {"type": "date"},
                "start_station_id": {"type": "integer"},
                "start_station_name": {"type": "keyword"},
                "start_location": {"type": "geo_point"},
                "end_station_id": {"type": "integer"},
                "end_station_name": {"type": "keyword"},
                "end_location": {"type": "geo_point"},
                "bikeid": {"type": "integer"},
                "usertype": {"type": "keyword"},
                "birth_year": {"type": "integer"},
                "gender": {"type": "integer"}
            }
        }
    }

    # Constructor taking all entity values
    # see the factory methods below for friendlier construction
    def __init__(self, tripduration, starttime, stoptime, start_station_id, start_station_name, start_location,
                 end_station_id, end_station_name, end_location, bikeid, usertype, birth_year, gender):
        self.tripduration = tripduration
        self.starttime = starttime
        self.stoptime = stoptime
        self.start_station_id = start_station_id if start_station_id != 'NULL' else 0
        self.start_station_name = start_station_name
        self.start_location = start_location if start_location['lat'] != 'NULL' else {
            'lat': 0.0, 'lon': 0.0}
        self.end_station_id = end_station_id if end_station_id != 'NULL' else 0
        self.end_station_name = end_station_name
        self.end_location = end_location if end_location['lat'] != 'NULL' else {
            'lat': 0.0, 'lon': 0.0}
        self.bikeid = bikeid
        self.usertype = usertype
        self.birth_year = birth_year if birth_year != 'NULL' and birth_year != "\\N" else 0
        self.gender = gender if gender != 'NULL' else 0

    # Send the instance data to the specified logger
    async def log(self, logger, silent=True):
        await logger(self.__dict__, silent=silent)
        LogEvent.logged += 1

    # Static class factory method to create citybike
    # event records from
    # the data received from a Kafka message
    @staticmethod
    def from_kafka(event):
        # The citibike data has some inconsistencies in the field names
        # some have spaces between words and some have
        # capital first letters
        # here I'm normalizing the attribute keys to lower case, no spaces
        # I have found that there are no discrepancies across the full
        # data set with this approach
        e = {}
        for key, value in event.items():
            key = "".join(key.lower().split(" "))
            e[key] = value
        event = e

        try:
            # Construct a log event from the normalized Kafka record
            # There are some experessions here to deal with Nulls and
            # other invalid data attributes
            return LogEvent(
                tripduration=event['tripduration'],
                starttime="T".join(event['starttime'].split(' ')),
                stoptime="T".join(event['stoptime'].split(' ')),
                start_station_id=event['startstationid'],
                start_station_name=event['startstationname'],
                start_location={
                    'lat': event['startstationlatitude'], 'lon': event['startstationlongitude']},
                end_station_id=event['endstationid'],
                end_station_name=event['endstationname'],
                end_location={
                    'lat': event['endstationlatitude'], 'lon': event['endstationlongitude']},
                bikeid=event['bikeid'],
                usertype=event['usertype'],
                birth_year=event['birthyear'],
                gender=event['gender'])
        except KeyError as error:
            # I was getting some KeyError and Attribute Error
            # exceptions, but those have been cleaned up
            # if I get them again, I can see what data caused
            # the error and update the code to deal with the
            # bad data
            print(error)
            print(event)
        except AttributeError as error:
            print(error)
            print(event)
