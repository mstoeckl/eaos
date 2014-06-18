__all__ = ["Engine"]

import os
import csv
import json
import importlib
from .data import Store
from .common import *


class Config():
    defaults = {
        "moo": "COW"
    }

    def __init__(self, path):
        self.config_location = path
        if os.path.exists(path):
            with open(path) as f:
                reader = csv.reader(f)
                for row in reader:
                    if row[0] in Config.defaults:
                        setattr(self, row[0], row[1])
        for k, v in Config.defaults.items():
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
        self.config = Config(path + "/config")
        self.output = output

        def push(*x):
            return self.output(*x)
        module = importlib.import_module("engine.years." + str(year))
        self.year = module.Analysis()
        self.data = Store(path, self.year, push)

    def page_exists(self, key, tail):
        if key == "/view/robot":
            return self.data.robot_exists(tail)
        if key == "/view/match":
            return self.data.match_exists(tail)
        return False

    csvify = wrap_to_engine(csvify)
    tablify = wrap_to_engine(tablify)
    surround_list = wrap_to_engine(surround_list)

    def receive(self, page, key, val):
        """
        Feed the engine data!
        """
        if page == "/config":
            if key == "longterm":
                self.config.moo = val
                self.output(page, "shortterm", " ".join([self.config.moo] * 3))
                self.config.save()
                return
        if page == "/input/schedule":
            if key in ("csv_entry", "csv_reset"):
                if key == "csv_entry":
                    self.data.update_schedule(val)
                else:
                    self.data.reset_schedule()

                return
        if page == "/input/actions":
            if key == "match_num":
                for i in range(6):
                    self.output(
                        page, "team-{}-{}".format(i, val), self.data.get_team(val, i))
                    self.output(
                        page, "actions-{}-{}".format(i, val), self.data.get_actions(val, i))
                    self.output(
                        page, "scouter-{}-{}".format(i, val), self.data.get_scouter(val, i))
                return

            if key.startswith("actions"):
                spot, match = key.split("-", maxsplit=2)[1:]
                self.data.set_actions(match, int(spot), val.upper())
                return
            if key.startswith("scouter"):
                spot, match = key.split("-", maxsplit=2)[1:]
                self.data.set_scouter(match, int(spot), val.upper())
                return
        if page == "/input/match":
            if key == "request_scores":
                for match in self.data.get_match_list():
                    scores = self.data.get_scores(match)
                    for i in range(6):
                        self.output(
                            page, str(i) + "-" + match, scores[i])
                return
            elif "-" in key:
                item, match = key.split("-", maxsplit=1)
                try:
                    v = int(val)
                except ValueError:
                    return

                self.data.set_score(match, int(item), v)
                return

        print(
            "\033[1;31m[Fall]\033[0m Page {}; Key {}; Value {}".format(page, key, val))
