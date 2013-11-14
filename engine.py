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
        params = {'input': 'Zuerich, Regensbergbruecke', 'dirInput': 'Zuerich, Schwammendingerplatz'}

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
            line = False

        # Calculate how much time there is left until departure (in seconds)
        departure = parse(con['from']['departure']).replace(tzinfo=None)
        time_left = departure - datetime.now().replace(tzinfo=None)
        time_left = int(time_left.total_seconds())

        # Check if a prognosed time was sent (has not happened so far)
        prognosed = con['from']['prognosis']['departure']
        if prognosed:
            print 'Prognosed departure', prognosed

        # Return a nice message
        seconds = time_left % 60
        minutes = abs((time_left - seconds) / 60)

        if not line:
            line = ''

        if time_left > 0:
            msg = '{} in {} min {} s'.format(line, minutes, seconds)
        else:
            msg = '{}: Run it\'s LATE!'.format(line)

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
    '''Can check connections to different targets'''

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
    station = 'Zuerich, Regensbergbruecke'
    targets = ['Zuerich, Unteraffoltern', 'Zuerich, Muehlacker']

    api = ZVVTimeTable()
    next_connection = ConnectionTracker(api, station, targets)

    while True:
        next_connection.check_all()
        print next_connection.get_next()
        time.sleep(20)
