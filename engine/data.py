import os
import csv
import io
import json
import random
from collections import defaultdict
from . node import Node
from . common import *
from copy import copy, deepcopy

# injected
push = None
schedule_node = None
year = None
save_data = None

# global links

matches = {}
# takes: "match":(ActionNode, ScoreNode, SynthNode)

robots = {}
# takes: "robot":(RoboNode)


# helpers

def get_match_list():
    return sorted(matches.keys())
def get_robot_list():
    return sorted(robots.keys())

def spread(pages, key, value):
    for p in pages:
        push(p, key, value)
def cast(page, **kvp):
    for k, v in kvp.items():
        push(page, k, v)
def constNode(v):
    n = Node(lambda x: v, lambda x:v)
    n.data = v
    return n

# ROOT NODES

def actions_redo(input):
    return input
def actions_onchange(action_data):
    pass

def score_redo(input):
    return forceints(input)
def score_onchange(action_data):
    pass

def schedule_redo(input):
    dct = {}
    for row in input:
        dct[row[0]] = row[1:]
    return dct

def schedule_to_array(dct):
    d = dct
    x = [Store.sched_header]
    for match,teams in sorted(d.items()):
        x.append([match] + teams)
    return x

def schedule_onchange(schedule_data):
    index = defaultdict(set)

    # delete old matches
    for match in list(matches.keys()):
        if match not in schedule_data:
            for u in matches[match]:
                u.unlink()
            del matches[match]
            push("/view/match/"+match, "destroy", "")

    # add new matches, index robots
    for match, teams in schedule_data.items():
        if match not in matches:
            mk_match(match, {})
        for t in teams:
            index[t].add(match)

    # delete old robots
    for t in list(robots.keys()):
        if t not in index:
            robots[t].unlink()
            del robots[t]
            push("/view/robot/"+t, "destroy", "")

    # add new robots
    for t,mx in index.items():
        if t in robots:
            robots[t].unlink()
        robonode = Node(robot_redo, robot_onchange, [constNode(t)]+[matches[match][2] for match in mx])
        robots[t] = robonode

    #push raw

    arr = schedule_to_array(schedule_data)
    push("/input/schedule", "csv_entry", csvify(arr))
    push("/input/schedule", "csv_table", tablify(arr))


    spread(("/input/match", "/view/match", "/input/actions"),
           "match_list", json.dumps(get_match_list()))

    push("/view/robot", "robot_list", json.dumps(get_robot_list()))


# EXTENDED NODES

def robot_redo(robot, *match_data):
    # here, calculate the relevant statistics
    return (robot, dict(zip(map(lambda x: x["num"], match_data), match_data)))
def robot_onchange(robot_data):
    robot = robot_data[0]
    # push to page
    table = [["Match"] + year.get_robot_match_header()]
    for match in sorted(robot_data[1].keys()):
        table.append(
            [match] + year.get_robot_match_results(robot_data[1], robot, match))

    push("/view/robot/" + robot, "update_matches", json.dumps(table))

    table = [["Statistic"] + year.get_robot_stats_header()]
    data = year.get_robot_stats_results(robot_data[1], robot)
    for param,key in (("min","Min"),("avg","Avg"),("max","Max")):
        table.append([key] + data[param])
    push("/view/robot/"+robot, "update_stats", json.dumps(table))

def match_redo(num, schedule, act, score):
    teams = schedule[num]
    result = {"num":num, "score":score, "data":[ [teams[i],act[i][0],act[i][1]] for i in range(6)]}
    return result

def match_onchange(match_data):
    scores = match_data["score"]
    teams = match_data["data"]
    fields = {}
    for i in range(6):
        fields["robot-"+str(i)] = teams[i][0]
        fields["score-"+str(i)] = scores[i]
    fields["Red_score_total"] = scores[0]+scores[1]+scores[2]
    fields["Blue_score_total"] = scores[3]+scores[4]+scores[5]

    cast("/view/match/" + match_data["num"], **fields)

# control / interface

def mk_match(num, store):
    actnode = Node(actions_redo, actions_onchange)
    scorenode = Node(score_redo, score_onchange)
    synthnode = Node(match_redo, match_onchange, [constNode(num), schedule_node, actnode, scorenode])

    actnode.data = dictrip(store, [["A0","S0"],["A1","S1"],["A2","S2"],["A3","S3"],["A4","S4"],["A5","S5"]])
    scorenode.data = forceints(dictrip(store, ["RedAuto","RedTele","RedFoul","BlueAuto","BlueTele","BlueFoul"]))

    matches[num] = (actnode, scorenode, synthnode)

class Store():
    scores = "RedAuto, RedTele, RedFoul, BlueAuto, BlueTele, BlueFoul".split(
        ", ")
    match = "Match"
    entries = "T0, A0, S0, T1, A1, S1, T2, A2, S2, T3, A3, S3, T4, A4, S4, T5, A5, S5".split(
        ", ")
    header = [match] + scores + entries

    # view on everything, trigger input
    def __init__(self, path, year_funcs, push_data):
        global push
        global year
        global save_data
        year = year_funcs
        push = push_data
        save_data = lambda: self.save()
        self.path = path + "/data"
        self.load()
    def save(self):
        # write all the data bound in the matches
        table = [Store.header]
        for k in sorted(matches.keys()):
            d = matches[k][2].data
            group = [k] + d["score"] + flatten(d["data"])
            table.append(group)

        with open(self.path, "w") as f:
            writer = csv.writer(f)
            for r in table:
                writer.writerow(r)

    def load(self):
        global schedule_node
        schedule_node = Node(schedule_redo, schedule_onchange)
        schedule_data = []

        if os.path.exists(self.path):
            with open(self.path) as f:
                array = readcsv(f.read())[1:]

            for row in array:
                store = dict(zip(Store.header, row))
                num = store[Store.match]
                mk_match(num, store)
                teams = [num] + dictrip(store, ["T0","T1","T2","T3","T4","T5"])
                schedule_data.append(teams)

        # side effect: forms, creates all the robots
        schedule_node.update(schedule_data)

    sched_header = ["Match", "Red1", "Red2", "Red3", "Blue1", "Blue2", "Blue3"]

    def get_schedule(self):
        return schedule_to_array(schedule_node.data)

    def update_schedule(self, text_csv):
        blk = readcsv(text_csv)
        if not blk:
            print("empty")
            return
        trim = len(Store.sched_header)
        if blk[0] != Store.sched_header:
            print("invalid data")
            return

        res = [u[:trim] for u in blk[1:]]

        schedule_node.update(res)
        save_data()

    def reset_schedule(self):
        print("No reset allowed")
        push("/input/schedule","message","Yo!")

    def get_match_list(self):
        return get_match_list()
    def get_robot_list(self):
        return get_robot_list()

    def get_scouter(self, match, spot):
        if match not in matches:
            return ""
        return matches[match][0].data[spot][1]
    def get_actions(self, match, spot):
        if match not in matches:
            return ""
        return matches[match][0].data[spot][0]
    def get_team(self, match, spot):
        if match not in schedule_node.data:
            return ""
        return schedule_node.data[match][spot]
    def set_actions(self, match, spot, val):
        if match not in matches:
            return
        sector = deepcopy(matches[match][0].data)
        sector[spot][0] = val
        matches[match][0].update(sector)
        save_data()
    def set_scouter(self, match, spot, val):
        if match not in matches:
            return
        sector = deepcopy(matches[match][0].data)
        sector[spot][1] = val
        matches[match][0].update(sector)
        save_data()

    def get_scores(self, match):
        if match not in matches:
            return [0,0,0,0,0,0]
        return matches[match][1].data
    def set_score(self, match, item, val):
        sector = deepcopy(matches[match][1].data)
        sector[item] = val
        matches[match][1].update(sector)
        save_data()

    def robot_exists(self, robot):
        return robot in robots
    def match_exists(self, match):
        return match in matches

    def get_matches(self, robot):
        return sorted(robots[robot].data[1].keys())

    def get_robot_match_header(self):
        return year.get_robot_match_header()
    def get_robot_match_results(self, robot, match):
        return year.get_robot_match_results(robots[robot].data[1],robot, match)
    def get_robot_stats_header(self):
        return year.get_robot_stats_header()
    def get_robot_stats_results(self, robot):
        return year.get_robot_stats_results(robots[robot].data[1], robot)
