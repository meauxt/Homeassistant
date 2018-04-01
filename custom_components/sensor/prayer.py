
import logging
from datetime import datetime, timedelta
import collections

from homeassistant.const import  (CONF_NAME, TEMP_CELSIUS, CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE)
from homeassistant.core import callback
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_point_in_utc_time
import re

_LOGGER = logging.getLogger(__name__)


TIME_DIGIT_PATTERN = re.compile(r'\d{1,2}')
TIME_PATTERN = re.compile(r'\d{1,2}:\d{1,2}')
STATE_ATTR_FAJR_TIME = None
STATE_ATTR_DHUHR_TIME = None
STATE_ATTR_ASR_TIME = None
STATE_ATTR_MAGHRIB_TIME = None
STATE_ATTR_ISHA_TIME = None

STATE_ATTR_FAJR = "fajr"
STATE_ATTR_DHUHR = 'dhuhr'
STATE_ATTR_ASR = "asr"
STATE_ATTR_MAGHRIB = "maghrib"
STATE_ATTR_ISHA = "isha"



def setup_platform(hass, config, add_devices, discovery_info=None):

    latitude = config[CONF_LATITUDE]
    longitude = config[CONF_LONGITUDE]
    prayer = Prayer(hass, latitude, longitude)
    add_devices([prayer])
    prayer.point_in_time_listener(datetime.now())


class Prayer(Entity):
    """Representation of the Daily Prayer Time."""

    def __init__(self, hass, latitude, longitude):
        """Initialize the Prayer."""
        
        self.hass = hass
        self._state = None
        # self.fajr_time = None
        # self.dhuhr_time = None
        # self.asr_time = None
        # self.maghrib_time = None
        # self.isha_time = None
        self.next_pray = None

        self.longitude = longitude
        self.latitude = latitude

        # self.state_attributes = {
        #     STATE_ATTR_FAJR : None,
        #     STATE_ATTR_DHUHR : None,
        #     STATE_ATTR_ASR : None,
        #     STATE_ATTR_MAGHRIB : None,
        #     STATE_ATTR_ISHA : None
        # }
        # self.date_attributes = {
        #     STATE_ATTR_FAJR_TIME : None,
        #     STATE_ATTR_DHUHR_TIME : None,
        #     STATE_ATTR_ASR_TIME : None,
        #     STATE_ATTR_MAGHRIB_TIME : None,
        #     STATE_ATTR_ISHA_TIME : None
        # }
        self.date_attributes = {}
        self.my_attributes = self.fetch_prayer_time()
        # self.set_state_attribute(prayers)
        self.set_date_attributes(self.my_attributes)

        self.next_update = None
        self.point_in_time_listener(datetime.now())
        # MOVE TO SETUP :
      


    @property
    def name(self):
        """Return the name."""
        return "Prayer"
    

    @property
    def state(self):
        """Return the time of the next Pray."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attr = [('next pray',self.next_pray_name),
        ('---------',"---------"),
        (STATE_ATTR_FAJR, self.my_attributes[STATE_ATTR_FAJR]),
        (STATE_ATTR_DHUHR, self.my_attributes[STATE_ATTR_DHUHR]),
        (STATE_ATTR_ASR, self.my_attributes[STATE_ATTR_ASR]),
        (STATE_ATTR_MAGHRIB, self.my_attributes[STATE_ATTR_MAGHRIB]),
        (STATE_ATTR_ISHA, self.my_attributes[STATE_ATTR_ISHA])
        ]
        collections.OrderedDict(attr)
        return attr
    
    def update_state(self):
        """Return the name of the next pray"""

        left_prayers = [(x,y) for x, y in self.date_attributes.items() if y > datetime.now()]


        if len(left_prayers) is 0:
            self.my_attributes = self.fetch_prayer_time(0)
            self.set_date_attributes(self.my_attributes)
            left_prayers.append(('fajr',self.my_attributes['fajr']))

        next_pray = min(left_prayers, key = lambda t: t[1])

        self.next_pray_name = next_pray[0]
        self.next_update = next_pray[1]
        self._state = self.my_attributes[next_pray[0]]

    @callback
    def point_in_time_listener(self, now):
        """Run when the state of the sun has changed."""
        # IF Isha then assign the 
        # Schedule next update at next_change+1 second so sun state has changed
        self.update_state()
        self.date_attributes[self.next_pray_name]
        # _LOGGER.error(self.date_attributes[self.next_pray_name].microsecond)

        async_track_point_in_utc_time(
            self.hass, self.point_in_time_listener,
             self.date_attributes[self.next_pray_name])


    @staticmethod  
    def generate_date(time):
        """Genertate Date object from """
        groups = TIME_DIGIT_PATTERN.findall(time)
        return  datetime.now().replace(hour = int(groups[0]), minute= int(groups[1]))

     
    def fetch_prayer_time(self,day_from_tomorrow = -1):
        import json
        from datetime import datetime
        import requests
        import json
        import os
        # os.environ['NO_PROXY'] = 'aladhan.com'
        res = requests.get(url="http://api.aladhan.com/"
                           "v1/calendar?latitude="+str(self.latitude)+"&longitude="+
                           str(self.longitude)+"&method=2&month="+str(datetime.now().month)
                           +"&year="+str(datetime.now().year))
        # binary = res.content.decode('utf-8')
        output = json.loads(res.content.decode('utf-8'))
        prayers = output['data'][int(datetime.now().day) + day_from_tomorrow]['timings']
        
        return dict((k.lower(), TIME_PATTERN.findall(v)[0]) for k, v in prayers.items())

    # def set_state_attribute(self, prayers):
    #     """Genertate Date object from """
    #     for pray in self.state_attributes:
    #         self.state_attributes[pray] = TIME_PATTERN.findall(prayers[pray])

    def set_date_attributes(self, prayers):
        """Genertate Date object from """
        for pray in self.my_attributes:
            self.date_attributes[pray] = self.generate_date(prayers[pray])