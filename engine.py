import json
import urllib
from urllib import urlencode
import time

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
        '''
        minutes_passed = int(round((time.time() - self.started)/60))
        val = self.start_val - minutes_passed
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
        std_params = {'L': 'vs_widgets', 'maxJourneys': str(num_journeys), 'start': 'yes',
            'requestType': '0', 'input': station}
        std_params.update(params)
        self.station = station

        self.url = 'http://online.fahrplan.zvv.ch//bin/stboard.exe/dn?' + urlencode(std_params)

        self.board = []
        self.update_board()

    def update_board(self):
        # Get the data, fix it
        timetableData = urllib.urlopen(self.url)
        try:
            timetableDataString = timetableData.read().decode(encoding='UTF-8')
        except UnicodeDecodeError:
            print 'Did not receive expected json data from api. (DecodeError)'
            return

        timetableDataStringTrunc = timetableDataString[14:]

        # Load all the journeys as the new board
        data = json.loads(timetableDataStringTrunc)
        del self.board
        self.board = []

        try:
            for j in data['journey']:
                self.board.append(Journey(j))
        except KeyError:
            print 'Did not receive expected json data from api.'
            return

    def get_board(self):
        title = 'Connections from ' + self.station + ':'
        return '\n'.join([title] + [str(j) for j in self.board])

    def remove_passed_journeys(self):
        threshold = 0
        ind = [i for i,j in enumerate(self.board) if j.get_value() < threshold]
        [self.board.pop(i) for i in reversed(ind)]

    def get_next_journey(self, targets):
        self.remove_passed_journeys()

        # Get all possible connections
        for j in self.board:
            if j.target in targets:
                return j

if __name__=='__main__':
    station = 'Zuerich, Kunsthaus'
    fritz = ['Zuerich, Albisrieden', 'Schlieren, Zentrum']
    hans = ['Zuerich, Klusplatz']

    board = ZVVStationBoard(station, 20)

    print 'Fritz:', board.get_next_journey(fritz)
    print 'Hans:', board.get_next_journey(hans)

    '''
    i = 0
    while True:
        i += 1
        # Update board every 120 seconds
        if not i%12:
            board.update_board()

        # Print next connections every 10 seconds
        print '\nFritz:', board.get_next_journey(fritz)
        print 'Hans:', board.get_next_journey(hans)
        time.sleep(10)
    '''


