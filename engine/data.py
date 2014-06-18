import os
import csv
import json
from collections import defaultdict
from copy import deepcopy

from . node import link
from . common import *

year = None
push = None
save_path = None

# helpers


def spread(pages, key, value):
    for p in pages:
        push(p, key, value)


def cast(page, **kvp):
    for k, v in kvp.items():
        push(page, k, v)

# ROOT NODES


@link(default=[])
def raw_schedule(vector, this):
    return this


@link(dim=1, default=[['', ''] for i in range(6)])
def raw_actions(vector, this):
    return this


@link(dim=1, default=[0, 0, 0, 0, 0, 0])
def raw_score(vector, this):
    return this

# INNERWARE


def mkindex(schedule):
    index = defaultdict(set)
    for match, robots in schedule.items():
        for robot in robots:
            index[robot].add(match)
    return index


@link(default=({}, defaultdict(set)), dependencies={raw_schedule: link.only})
def schedule(vector, this, raw_schedule=0):
    """ As side effect, terminates pages, adds/unlinks match/page nodes """

    new = dict(map(lambda u: (u[0], u[1:]), raw_schedule))
    new_idx = mkindex(new)
    old, old_idx = this

    for team in old_idx.keys() - new_idx.keys():
        robot_page(team).delete()
        robot(team).delete()
        push("/view/robot/" + team, "destroy", "")

    for team in new_idx.keys() - old_idx.keys():
        r = robot(team)
        for mtc in new_idx[team]:
            r.add(match, (mtc,))
        robot_page(team)

    for team in new_idx.keys() & old_idx.keys():
        r = robot(team)
        for mtc in new_idx[team] - old_idx[team]:
            r.add(match, (mtc,))
        for mtc in old_idx[team] - new_idx[team]:
            r.remove(match, (mtc,))

    for mtc in old.keys() - new.keys():
        match_page(mtc).delete()
        match(mtc).delete()
        raw_actions(mtc).delete()
        raw_score(mtc).delete()
        push("/view/match/" + match, "destroy", "")

    for mtc in new.keys() - old.keys():
        raw_actions(mtc)
        raw_score(mtc)
        match(mtc)
        match_page(mtc)

    return new, new_idx

    print("schedule received {}...{}".format(
        raw_schedule[:1], raw_schedule[-1:]))
    return not this


@link(dim=1, dependencies={
      schedule: link.only, raw_actions: link.match, raw_score: link.match})
def match(vector, this, schedule=0, raw_actions=0, raw_score=0):
    this = {"score": [raw_score[:3], raw_score[3:]],
            "teams": schedule[0][vector[0]],
            "actions": [x[0] for x in raw_actions],
            "scouters": [x[1] for x in raw_actions]}

    return this


@link(dim=1, dependencies={match: link.vary})
def robot(vector, this, match=0):
    return match

# OUTERWARE


@link(dim=1, dependencies={match: link.match})
def match_page(vector, this, match=0):
    """ Match page """

    scores = flatten(match["score"])
    teams = match["teams"]
    fields = {}
    for i in range(6):
        fields["robot-" + str(i)] = teams[i]
        fields["score-" + str(i)] = scores[i]
    fields["Red_score_total"] = scores[0] + scores[1] + scores[2]
    fields["Blue_score_total"] = scores[3] + scores[4] + scores[5]

    cast("/view/match/" + vector[0], **fields)
    return this


@link(dim=1, dependencies={robot: link.match})
def robot_page(vector, this, robot=0):
    """ Robot page, & analysis """
    rbt = vector[0]
    match_table = [["Match"] + year.get_robot_match_header()]
    for mtc in sorted(robot.keys()):
        match_table.append(
            [mtc[0]] + year.get_robot_match_results(robot, rbt, mtc[0]))

    push("/view/robot/" + rbt, "update_matches", json.dumps(match_table))

    stats_table = [["Statistic"] + year.get_robot_stats_header()]
    data = year.get_robot_stats_results(robot, rbt)
    for param, key in (("min", "Min"), ("avg", "Avg"), ("max", "Max")):
        stats_table.append([key] + data[param])
    push("/view/robot/" + rbt, "update_stats", json.dumps(stats_table))
    return match_table, stats_table


def schedule_to_array(dct):
    d = dct
    x = [Store.sched_header]
    for match, teams in sorted(d.items()):
        x.append([match] + teams)
    return x


def push_schedule_page(matches):
    arr = schedule_to_array(matches)
    # TODO: just push it in JSON format, have page deserialize. One control
    # point!
    push("/input/schedule", "csv_entry", csvify(arr))
    push("/input/schedule", "csv_table", tablify(arr))


@link(dependencies={schedule: link.only})
def schedule_page(vector, this, schedule=0):
    """ Index pages; """
    matches, robots = schedule
    push_schedule_page(matches)

    spread(("/input/match", "/view/match", "/input/actions"),
           "match_list", json.dumps(sorted(matches.keys())))

    push("/view/robot", "robot_list", json.dumps(sorted(robots.keys())))
    return this

# AUXILIARY


@link(dependencies={match: link.all})
def save(vector, this, match=0):
    table = [Store.header]
    for k in sorted(match.keys()):
        d = match[k]

        group = [k[0]] + flatten(d["score"]) + flatten(
            [[d["teams"][i], d["actions"][i], d["scouters"][i]] for i in range(6)])
        table.append(group)

    text = csvify(table)
    with open(save_path, "w") as f:
        f.write(text)
    return this

# control / interface


def load():
    rsc = raw_schedule()
    sc = schedule()
    schedule_page()

    if os.path.exists(save_path):
        with open(save_path) as f:
            array = readcsv(f.read())[1:]

        rscd = []
        for row in array:
            store = dict(zip(Store.header, row))
            num = store[Store.match]

            teams = [num] + \
                dictrip(store, ["T0", "T1", "T2", "T3", "T4", "T5"])
            rscd.append(teams)

            act_struct = [["A0", "S0"], ["A1", "S1"], ["A2", "S2"], [
                "A3", "S3"], ["A4", "S4"], ["A5", "S5"]]
            score_struct = [
                "RedAuto", "RedTele", "RedFoul", "BlueAuto", "BlueTele", "BlueFoul"]

            raw_actions(num).modify(dictrip(store, act_struct))
            raw_score(num).modify(forceints(dictrip(store, score_struct)))
            match(num)

        rsc.modify(rscd)

    link.clean()
    save()


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
        global save_path
        year = year_funcs
        push = push_data
        save_path = path + "/data"
        load()

    sched_header = ["Match", "Red1", "Red2", "Red3", "Blue1", "Blue2", "Blue3"]

    def get_schedule(self):
        return schedule_to_array(schedule().state[0])

    def update_schedule(self, text_csv):
        blk = readcsv(text_csv)
        if not blk:
            push_schedule_page(schedule().state[0])
            return
        trim = len(Store.sched_header)
        if blk[0] != Store.sched_header:
            push_schedule_page(schedule().state[0])
            return

        res = [u[:trim] for u in blk[1:]]
        if res != blk[1:] and res == raw_schedule().state:
            push_schedule_page(schedule().state[0])
            return

        raw_schedule().modify(res)
        link.clean()

    def reset_schedule(self):
        print("No reset allowed")
        push("/input/schedule", "message", "Yo!")

    def get_match_list(self):
        return sorted(schedule().state[0].keys())

    def get_robot_list(self):
        return sorted(schedule().state[1].keys())

    no_match = " "

    def get_scouter(self, mtc, spot):
        if mtc != Store.no_match:
            return match(mtc).state["scouters"][spot]
        return ""

    def get_actions(self, mtc, spot):
        if mtc != Store.no_match:
            return match(mtc).state["actions"][spot]
        return ""

    def get_team(self, mtc, spot):
        if mtc != Store.no_match:
            return schedule().state[0][mtc][spot]
        return "????"

    def set_actions(self, mtc, spot, val):
        if mtc == Store.no_match:
            return
        e = raw_actions(mtc)
        e.state[spot][0] = val
        e.modify()
        link.clean()

    def set_scouter(self, mtc, spot, val):
        if mtc == Store.no_match:
            return
        e = raw_actions(mtc)
        e.state[spot][1] = val
        e.modify()
        link.clean()

    def get_scores(self, mtc):
        return raw_score(mtc).state

    def set_score(self, mtc, item, val):
        e = raw_score(mtc)
        e.state[item] = val
        e.modify()
        link.clean()

    def robot_exists(self, rbt):
        return (rbt,) in link.list(robot)

    def match_exists(self, mtc):
        return (mtc,) in link.list(match)

    def get_matches(self, rbt):
        return [x[0] for x in sorted(robot(rbt).state.keys())]

    def get_robot_match_header(self):
        return year.get_robot_match_header()

    def get_robot_match_results(self, rbt, mtc):
        return year.get_robot_match_results(
            robot(rbt).state, rbt, mtc)

    def get_robot_stats_header(self):
        return year.get_robot_stats_header()

    def get_robot_stats_results(self, rbt):
        return year.get_robot_stats_results(robot(rbt).state, rbt)
