import json
import urllib
from dateutil.parser import parse
from datetime import datetime
import time
from math import ceil

###
# The interfaces for the ZVV and SBB API
###


class ZVVTimeTable:
    def __init__(self):
        self.base_url = 'http://online.fahrplan.zvv.ch//bin/stboard.exe/dn?L=vs_widgets&{}&additionalTime=0&maxJourneys=1&start=yes&requestType=0'

    def get_next_connection(self, station, direction):
        '''direction has to be an end station.'''

        # Fix up url
        params = {'input': station, 'dirInput': direction}
        url = self.base_url.format(urllib.urlencode(params))

        # Get data and modify
        timetableData = urllib.urlopen(url)
        timetableDataString = timetableData.read().decode(encoding='UTF-8')
        timetableDataStringTrunc = timetableDataString[14:]

        data = json.loads(timetableDataStringTrunc)
        journey = data[u'journey'][0]

        return journey[u'pr'], int(journey[u'countdown_val'])


class SBBTimeTable:
    def __init__(self):
        self.base_url = 'http://transport.opendata.ch/v1/'

    def _get_remote_data(self, url, params = {}):
        request_url = self.base_url + url + '?' + urllib.urlencode(params)
        return json.load(urllib.urlopen(request_url))

    def get_next_connection(self, origin, target):
        # Get the data
        connections = self._get_remote_data('connections', {'from': origin, 'to': target})
        # Select the first (next) connection
        con = connections['connections'][0]

        # Find the (bus) line name
        if con['sections'][0]['journey']:
            line = con['sections'][0]['journey']['name'].rstrip()
        else:
            line = ''

        # Calculate how much time there is left until departure (in seconds)
        departure = parse(con['from']['departure']).replace(tzinfo=None)
        time_left = departure - datetime.now().replace(tzinfo=None)
        time_left = int(time_left.total_seconds())

        # Return a nice message
        minutes = int(round(abs(time_left)/ 60))
        return line, minutes


class MinuteCountdown:
    '''A simple countdown lazy minute countdown'''
    def __init__(self, minutes):
        self.start_val = minutes
        self.started = time.time()

    def get_value(self):
        minutes_passed = int(ceil((time.time() - self.started)/60))
        val = self.start_val - minutes_passed
        if val<0: val=0
        return val


class ConnectionTracker:
    '''Can check multiple directions, stores next connection as a off-line updated countdown.'''

    def __init__(self, api, station, targets):
        self.api = api
        self.station = station
        self.targets = targets

        # Set up countdown container
        self.countdown = False
        self.current_msg = False

    def check_all(self):
        # iterate over connections, find minimal time
        min_con = (False, 1000)
        for t in self.targets:
            con = self.api.get_next_connection(self.station, t)
            if con[1] < min_con[1]:
                min_con = con

        # Set up the Countdown
        self.countdown = MinuteCountdown(min_con[1])
        self.line = min_con[0]

    def get_next(self):
        if self.countdown:
            return '{} in {} minutes'.format(self.line, self.countdown.get_value())
        else:
            return 'No Data Yet...'


if __name__=='__main__':
    station = 'Zuerich, ETH Hoenggerberg'
    targets = ['Zuerich, Bucheggplatz', 'Zuerich, Triemlispital', 'Zuerich, Oerlikon Nord']

    api = ZVVTimeTable()
    next_connection = ConnectionTracker(api, station, targets)
    next_connection.check_all()
    print 'Evacuate Hoenggerberg!\nNext connection:', next_connection.get_next()
