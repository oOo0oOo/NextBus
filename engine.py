import json
import urllib
from urllib import urlencode
import time
from math import ceil


class MinuteCountdown:
    '''
        A simple, lazy countdown in minutes.
    '''
    def __init__(self, minutes):
        self.start_val = minutes
        self.started = time.time()

    def get_value(self):
        '''
            Calculate current value from time passed.
            If run out countdown will stay at 0 indefinitely.
        '''
        minutes_passed = int(ceil((time.time() - self.started)/60))
        val = self.start_val - minutes_passed
        if val<0: val=0
        return val


class Journey(MinuteCountdown):
    def __init__(self, params):
        self.params = params

        # Line name and target
        self.line = params['pr'].replace(' ', '')

        # pprint a bit
        t = repr(params['st'])[2:-1]
        t = t.replace('\\xfc', 'ue')
        t = t.replace('\\xf6', 'oe')
        t = t.replace('\\xe4', 'ae')
        self.target = t

        MinuteCountdown.__init__(self, int(self.params['countdown_val']))

    def __str__(self):
        p = self.params
        pl = 's'
        if self.get_value() == 1:
            pl = ''

        return '{} to {} in {} minute{}'.format(self.line, self.target, self.get_value(), pl)


class ZVVStationBoard:
    def __init__(self, station, num_journeys = 15, params = {}):
        std_params = {'L': 'vs_widgets', 'maxJourneys': str(num_journeys), 'start': 'no',
            'requestType': '0', 'input': station}
        std_params.update(params)
        self.station = station

        self.url = 'http://online.fahrplan.zvv.ch//bin/stboard.exe/dn?' + urlencode(std_params)
        self.board = []
        self.update_board()

    def update_board(self):
        # Get the data, fix it
        timetableData = urllib.urlopen(self.url)
        timetableDataString = timetableData.read().decode(encoding='UTF-8')
        timetableDataStringTrunc = timetableDataString[14:]

        # Load all the journeys as the new board
        data = json.loads(timetableDataStringTrunc)
        del self.board
        self.board = []
        for j in data['journey']:
            self.board.append(Journey(j))

    def get_board(self):
        title = 'Connections from ' + self.station + ':'
        return '\n'.join([title] + [str(j) for j in self.board])

    def get_next_connection(self, targets):
        cons = []
        for jo in self.board:
            pass


if __name__=='__main__':
    station = 'Zuerich, berninaplatz'
    targets = ['Zuerich, Muehlacker', 'Zuerich, Neuaffoltern']

    board = ZVVStationBoard(station, 10)
    print board.get_board()
