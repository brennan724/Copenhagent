#!/usr/bin/env python3

# Python 3.5
# Brennan Kuo
# Brian Mitchell
# Linnea Sahlberg

import requests
import json
from urllib.parse import urlencode
import random
import time
from random import randint


def environment_connect(name):
    params = {'name': name}
    r = requests.get('http://localhost:3000/api/environment/connect?' + urlencode(params))
    print(r.status_code)
    res = json.loads(r.text)
    print(res['agentToken'])
    return res['agentToken']


# Do the stuff here to get the token
# TOKEN = sys.argv[1]
TOKEN = environment_connect('Brian Mitchell' + str(randint(0, 100000)))
TOKEN_HEADER = {'agentToken': TOKEN}
CURRENT_LOC = ''
MAP = {}


def call_api(url):
    s = requests.get(url, headers=TOKEN_HEADER)
    print(url, "\x1B[92m" + str(s.status_code) + "\x1B[0m")
    res = json.loads(s.text)
    # print(json.dumps(res, sort_keys=True, indent=4))
    return res


"""
Environment
"""


def environment_leave():
    call_api('http://localhost:3000/api/environment/leave')


"""
Map
"""


def map_enter():
    global CURRENT_LOC, MAP
    res = call_api('http://localhost:3000/api/map/enter')
    MAP = res
    CURRENT_LOC = res['state']['agents'][TOKEN]['locationId']
    print('Current locationId:', CURRENT_LOC)


def map_bike(location_id):
    global CURRENT_LOC
    call_api('http://localhost:3000/api/map/bike?locationId=' + location_id)
    CURRENT_LOC = location_id
    print('Current locationId:', CURRENT_LOC)


def map_metro(direction):
    global CURRENT_LOC
    call_api('http://localhost:3000/api/map/metro?direction=' + direction)
    CURRENT_LOC = next(iter(MAP['state']['map']['metro'][CURRENT_LOC][direction]))
    print('Current locationId:', CURRENT_LOC)


def map_leave():
    global CURRENT_LOC
    call_api('http://localhost:3000/api/map/leave')
    CURRENT_LOC = ''


def go_to_location(location_id, callback):  # where we are trying to go
    print(CURRENT_LOC)
    cw_cost = 0
    ccw_cost = 0
    metro = MAP['state']['map']['metro']
    new_cw_loc = next(iter(metro[CURRENT_LOC]['cw']))
    new_ccw_loc = next(iter(metro[CURRENT_LOC]['ccw']))
    ccw_cost = ccw_cost + metro[CURRENT_LOC]['ccw'][new_ccw_loc]
    cw_cost = cw_cost + metro[CURRENT_LOC]['cw'][new_cw_loc]
    while location_id != new_cw_loc:
        newer_cw_loc = next(iter(metro[new_cw_loc]['cw']))
        cw_cost = cw_cost + metro[new_cw_loc]['cw'][newer_cw_loc]
        new_cw_loc = newer_cw_loc
    while location_id != new_ccw_loc:
        newer_ccw_loc = next(iter(metro[new_ccw_loc]['ccw']))
        ccw_cost = ccw_cost + metro[new_ccw_loc]['ccw'][newer_ccw_loc]
        new_ccw_loc = newer_ccw_loc
    # print(cw_cost, ccw_cost)
    if cw_cost <= ccw_cost and cw_cost < 15:
        metro_to_location(location_id, 'cw')
        print('Taking the metro cw to {0} costing {1}'.format(location_id, cw_cost))
    elif ccw_cost < cw_cost and ccw_cost < 15:
        metro_to_location(location_id, 'ccw')
        print('Taking the metro ccw to {0} costing {1}'.format(location_id, ccw_cost))
    else:
        map_bike(location_id)
        print('Biking to {0} costing 15'.format(location_id))
    callback()


def metro_to_location(location_id, direction):
    if direction == 'cw':
        while location_id != CURRENT_LOC:
            map_metro('cw')
    elif direction == 'ccw':
        while location_id != CURRENT_LOC:
            map_metro('ccw')
    else:
        print('FUCK YOU TELL ME WHERE YOU WANT TO GO')

"""
Papersoccer
"""


def papersoccer_enter():
    res = call_api('http://localhost:3000/api/papersoccer/enter')
    return res['state']['papersoccer']


def papersoccer_leave():
    res = call_api('http://localhost:3000/api/papersoccer/leave')
    return res


def papersoccer_play(direction):
    res = call_api('http://localhost:3000/api/papersoccer/lane?direction=' + direction)
    return res


"""
Navigation
"""


def navigation_enter():
    res = call_api('http://localhost:3000/api/navigation/enter')
    return res['state']['navigation']


def navigation_leave():
    res = call_api('http://localhost:3000/api/navigation/leave')
    return res


def navigation_lane(direction):
    res = call_api('http://localhost:3000/api/navigation/lane?direction=' + direction)
    return res


def navigation_play():
    nav = navigation_enter()
    board = Navigation(nav, TOKEN)
    board.pretty_print()
    while board.iterate():
        board.which_direction(int(board.current_location['row']), int(board.current_location['column']))
    print(board.final_list())
    print(board.final_count())
    move_list = board.final_list()
    length = len(move_list)
    time.sleep(1)
    for i in range(length - 1):
        print(i)
        navigation_lane(move_list[i])
        time.sleep(1)
        print('Leaving Navigation!')
    navigation_leave()


class Navigation:
    move_list = []
    weight_count = 0
    board = []
    current_location = {}
    initial_return = {}
    token = ''
    keep_going = True

    def __init__(self, nav, token):
        self.initial_return = nav
        self.token = token
        self.board = [[0]*nav[token]['config']['size']['columns'] for i in range(nav[token]['config']['size']['rows'])]
        for i in nav[token]['graph']['vertices']:
            self.board[nav[token]['graph']['vertices'][i]['row']][nav[token]['graph']['vertices'][i]['column']] \
                = nav[token]['graph']['vertices'][i]['weight']
        self.current_location = nav[token]['config']['initial']

    def iterate(self):
        return self.keep_going

    def final_list(self):
        return self.move_list

    def final_count(self):
        return self.weight_count

    def set_current_location(self, string):
        string = string[1:-1]
        string = string.split(',')
        self.current_location['row'] = string[0]
        self.current_location['column'] = string[1]

    def pretty_print(self):
        print('Current location:', self.current_location)
        for i in self.board:
            print(i)

    def weight(self, row, col):
        return self.board[row][col]

    def left(self, row, col):
        try:
            edge = self.initial_return[self.token]['graph']['edges']['[' + str(row) + ',' + str(col) + ']']
            left = edge['left']
        except Exception as e:
            print(e)
            return '-10000'
        return left

    def right(self, row, col):
        try:
            edge = self.initial_return[self.token]['graph']['edges']['[' + str(row) + ',' + str(col) + ']']
            right = edge['right']
        except Exception as e:
            print(e)
            return '-10000'
        return right

    def stay(self, row, col):
        try:
            edge = self.initial_return[self.token]['graph']['edges']['[' + str(row) + ',' + str(col) + ']']
            stay = edge['stay']
        except Exception as e:
            print(e)
            return '-10000'
        return stay

    def which_direction(self, row, col):
        chosen_direction = ''
        left = self.left(row, col)
        right = self.right(row, col)
        stay = self.stay(row, col)
        if left > right and left > stay:
            self.move_list.append('left')
            chosen_direction = left
        elif right > left and right > stay:
            self.move_list.append('right')
            chosen_direction = right
        else:
            self.move_list.append('stay')
            chosen_direction = stay
        if stay == '-10000' and left == '-10000' and right == '-10000':
            map_leave()
            self.keep_going = False
        else:
            for i in self.initial_return[self.token]['graph']['vertices']:
                if i == chosen_direction:
                    self.weight_count = self.weight_count + self.initial_return[self.token]['graph']['vertices'][i]['weight']
            self.set_current_location(chosen_direction)


def go_to_nav_location(callback):
    locations = ['bryggen', 'noerrebrogade', 'langelinie', 'dis']
    go_to_location(random.choice(locations), callback)


def main():
    map_enter()
    go_to_nav_location(navigation_play)
    # map_leave()

main()
