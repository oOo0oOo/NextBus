#http://transport.opendata.ch/v1/stationboard?station=
#station: Aarau
import json
import urllib
from dateutil.parser import parse
from datetime import datetime


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

        return msg, time_left


if __name__=='__main__':
    station = 'Zuerich, Regensbergbruecke'
    target = 'Zuerich, ETH Hoenggerberg'

    sbb = SBBTimeTable()
    msg, seconds_left = sbb.get_next_connection(station, target)
    print msg
