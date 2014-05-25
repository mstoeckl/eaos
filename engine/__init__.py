__all__ = ["Engine"]

import os, csv, json, importlib
from .data import Store
from .common import *

class Config():
    defaults = {
        "moo":"COW"
    }

    def __init__(self, path):
        self.config_location = path
        if os.path.exists(path):
            with open(path) as f:
                reader = csv.reader(f)
                for row in reader:
                    if row[0] in Config.defaults:
                        setattr(self, row[0], row[1])
        for k,v in Config.defaults.items():
            if not hasattr(self, k):
                setattr(self, k, v)

    def save(self):
        print("Saving config")
        with open(self.config_location, "w") as f:
            writer = csv.writer(f)
            for k in Config.defaults:
                writer.writerow([k, getattr(self, k)])

def wrap_to_engine(f):
    def g(self, *x, **y):
        return f(*x, **y)
    return g

class Engine():
    """
    Basic principle of operation.
    As soon as new information enters,
    all information dependent on it is updated, and
    the changes are send to the pages

    """

    def __init__(self, year, path, output):
        """
        Output: object with a .(page, key, val) method
        """

        self.path = path
        os.makedirs(self.path, exist_ok=True)
        self.config = Config(path+"/config")
        self.output = output
        self.data = Store(path)
        module = importlib.import_module("engine.years."+str(year))
        self.year = module.Analysis(self.data)

    def page_exists(self, key, tail):
        if key == "/view/robot":
            return self.data.robot_exists(tail)
        if key == "/view/match":
            return self.data.match_exists(tail)
        return False

    def spread(self, pages, key, value):
        for p in pages:
            self.output(p,key,value)
    def cast(self, page, **kvp):
        for k,v in kvp.items():
            self.output(page, k, v)

    csvify = wrap_to_engine(csvify)
    tablify = wrap_to_engine(tablify)
    surround_list = wrap_to_engine(surround_list)

    def csvify(self, it):
        return csvify(it)
    def tablify(self, it):
        return tablify(it)
    def surround_list(self, list, tag):
        return surround_list(list, tag)

    def refresh_robot(self, robot):
        table = [["Match"]+self.year.get_robot_match_header()]
        for match in self.data.get_matches(robot):
            table.append([match] + self.year.get_robot_match_results(robot, match))

        self.output("/view/robot/"+robot, "update_matches", json.dumps(table))

        # note: more fields for net robot summary are necessary

    def refresh_match(self, match):
        fields = {}
        for term in ("Red","Blue"):
            fields[term+"_r1"] = self.data.get_robot(match, term, 1)
            fields[term+"_r2"] = self.data.get_robot(match, term, 2)
            fields[term+"_r3"] = self.data.get_robot(match, term, 3)
            fields[term+"_score_total"] = self.data.get_total_score(match, term)
            fields[term+"Auto"] = self.data.get_score(match, term+"Auto")
            fields[term+"Tele"] = self.data.get_score(match, term+"Tele")
            fields[term+"Foul"] = self.data.get_score(match, term+"Foul")

        self.cast("/view/match/"+match,**fields)

    def receive(self, page, key, val):
        """
        Feed the engine data!
        TODO: how to organize better (dirty-list, etc)
        """
        if page == "/config":
            if key == "longterm":
                self.config.moo = val
                self.output(page,"shortterm"," ".join([self.config.moo]*3))
                self.config.save()
                return
        if page == "/input/schedule":
            if key in ("csv_entry","csv_reset"):
                if key == "csv_entry":
                    table, deleted_matches, deleted_robots = self.data.update_schedule(val)
                else:
                    table, deleted_matches, deleted_robots = self.data.reset_schedule()
                self.output(page,"csv_entry",csvify(table))
                self.output(page,"csv_table",tablify(table))
                self.output("/input/actions","match_list",self.data.matchoptions())
                self.spread(["/input/match","/view/match"], "match_list", json.dumps(self.data.matchlist()))
                self.output("/view/robot", "robot_list", json.dumps(self.data.robotlist()))

                for match in deleted_matches:
                    self.output("/view/match/"+match,"destroy","")
                for robot in deleted_robots:
                    self.output("/view/robot/"+robot,"destroy","")

                # spray!. (note: later, replace with a dirty-list
                # mechanism, and explicit data tracking
                for match in self.data.matchlist():
                    self.refresh_match(match)

                for robot in self.data.robotlist():
                    self.refresh_robot(robot)

                return
        if page == "/input/actions":
            # TODO: robot refresh
            if key == "match_num":
                for i in range(6):
                    self.output(page, "team-{}-{}".format(i, val), self.data.get_actions_team(val, i))
                    self.output(page, "actions-{}-{}".format(i, val), self.data.get_actions_actions(val, i))
                    self.output(page, "scouter-{}-{}".format(i, val), self.data.get_actions_scouter(val, i))
                return
            if key.startswith("actions"):
                spot,match = key.split("-",maxsplit=2)[1:]
                self.data.set_actions_actions(match, int(spot), val.upper())
                robot = self.data.get_actions_team(match, int(spot))
                self.refresh_robot(robot)
                return
            if key.startswith("scouter"):
                spot,match = key.split("-",maxsplit=2)[1:]
                self.data.set_actions_scouter(match, int(spot), val.upper())
                return
        if page == "/input/match":
            if key == "request_scores":
                for match in self.data.matchlist():
                    for key in Store.scores:
                        self.output(page, key + "-" + match, self.data.get_score(match, key))
                return
            elif "-" in key:
                item, match = key.split("-", maxsplit=1)
                try:
                    v = int(val)
                except ValueError:
                    return

                self.data.set_score(match, item, v)
                # update match page!
                self.output("/view/match/"+match, item, v)
                if item.startswith("Red"):
                    term = "Red"
                else:
                    term = "Blue"
                self.output("/view/match/"+match, term+"_score_total", self.data.get_total_score(match, term))

                for i in range(6):
                    self.refresh_robot(self.data.data[match][i]["Team"])

                return


        print("\033[1;31m[Fall]\033[0m Page {}; Key {}; Value {}".format(page,key,val))










