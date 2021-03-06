

class ZVVTimeTable:
    def __init__(self):
        self.base_url = 'http://online.fahrplan.zvv.ch//bin/stboard.exe/dn?L=vs_widgets&{}&maxJourneys=1&start=no&requestType=0'

    def get_next_connection(self, station, direction):
        '''
            Direction has to be a line end station.
        '''

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


class ConnectionTracker:
    '''
        Can check multiple directions, stores next connection as a off-line updated countdown.
    '''

    def __init__(self, api, station, targets):
        self.api = api
        self.station = station
        self.targets = targets

        # Set up countdown container
        self.countdown = False
        self.current_msg = False

    def check_all(self):
        '''
            Finds the next connection using the provided api.
        '''

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
        '''
            Does not initiate api call, uses off-line countdown instead.
        '''

        if self.countdown:
            return '{} in {} minutes'.format(self.line, self.countdown.get_value())
        else:
            return 'No Data Yet...'

if __name__=='__main__':
    station = 'Zuerich, Hauptbahnhof'
    targets = ['Zuerich, Muehlacker', 'Zuerich, Neuaffoltern']

    # ZVV Time Table example:

    # api = ZVVTimeTable()
    # next_connection = ConnectionTracker(api, station, targets)

    # You can check connections in irregular intervals (according to bus frequency...)
    # next_connection.check_all()
    # .get_next() uses off-line countdown & does not initiate api calls.
    # print next_connection.get_next()

