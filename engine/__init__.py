__all__ = ["Engine"]

import os,csv,io
from collections import defaultdict

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

def tablify(array):
    rt = lambda row: "<td>"+"</td><td>".join(map(str,row))+"</td>"
    return "<tr>" +"</tr><tr>".join(map(rt,array))+"</tr>"

def csvify(array):
    sstream = io.StringIO()
    writer = csv.writer(sstream)
    for row in array:
        writer.writerow(row)
    return sstream.getvalue()

def readcsv(string):
    reader = csv.reader(string.split("\n"))
    return [list(map(lambda u:u.strip(),row)) for row in reader if row]

class Data():
    schedule_header = ["Number","R1","R2","R3","B1","B2","B3"]
    actions_header = ["Match", "Spot", "Actions", "Scouter"]

    def __init__(self, path):
        self.schedule_loc = path + "/schedule"
        self.actions_loc = path + "/actions"

        if os.path.exists(self.schedule_loc):
            with open(self.schedule_loc) as f:
                blk = readcsv(f.read())

            self._do_sched(blk, True)
        else:
            self.reset_schedule()

        if os.path.exists(self.actions_loc):
            self.load_actions()
        else:
            self.actions = defaultdict(dict)

    def _do_sched(self, blk, write=True):
        self.schedule_raw = csvify(blk)
        if write:
            with open(self.schedule_loc, "w") as f:
                f.write(self.schedule_raw)
        self.schedule_table = tablify(blk)
        return self.schedule_raw, self.schedule_table
    def update_schedule(self, data):
        return self._do_sched(readcsv(data))
    def reset_schedule(self):
        return self._do_sched([Data.schedule_header])


    def get_actions_team(self, match, spot):
        # schedule dependent lookup
        return 114 * match + spot
    def get_actions_actions(self, match, spot):
        if match in self.actions:
            d = self.actions[match]
            if spot in d:
                return d[spot][0]
        return ""
    def get_actions_scouter(self, match, spot):
        if match in self.actions:
            d = self.actions[match]
            if spot in d:
                return d[spot][1]
        return ""
    def set_actions_actions(self, match, spot, string):
        d = self.actions[match]
        if spot in d:
            initials = d[spot][1]
            if string and initials:
                d[spot] = (string, initials)
            else:
                del d[spot]
        elif string:
            d[spot] = (string,"")
        self.save_actions()
    def set_actions_scouter(self, match, spot, initials):
        d = self.actions[match]
        if spot in d:
            string = d[spot][0]
            if string and initials:
                d[spot] = (string, initials)
            else:
                del d[spot]
        elif initials:
            d[spot] = ("",initials)
        self.save_actions()
    def load_actions(self):
        # read in the csv
        with open(self.actions_loc) as f:
            blk = readcsv(f.read())
        self.actions = defaultdict(dict)
        for row in blk[1:]:
            match,spot,string,initials = row
            self.actions[int(match)][int(spot)] = (string, initials)
    def save_actions(self):
        arr = [Data.actions_header]

        # walk the tree
        for ik,iv in self.actions.items():
            for jk,jv in iv.items():
                arr.append([ik,jk,jv[0],jv[1]])

        with open(self.actions_loc,"w") as f:
            f.write(csvify(arr))




class Engine():
    """
    Basic principle of operation.
    As soon as new information enters,
    all information dependent on it is updated, and
    the changes are send to the pages

    """

    def __init__(self, path, output):
        """
        Output: object with a .(page, key, val) method
        """
        self.path = path
        self.config = Config(path+"/config")
        self.output = output
        self.data = Data(path)
    def receive(self, page, key, val):
        """
        Feed the engine data!
        """
        if page == "/config":
            if key == "longterm":
                self.config.moo = val
                self.output(page,"shortterm"," ".join([self.config.moo]*3))
                self.config.save()
                return
        if page == "/input/schedule":
            if key == "csv_entry":
                sr, st = self.data.update_schedule(val)
                self.output(page,"csv_entry",sr)
                self.output(page,"csv_table",st)
                return
            if key == "csv_reset":
                sr,st = self.data.reset_schedule()
                self.output(page,"csv_entry",sr)
                self.output(page,"csv_table",st)
                return
        if page == "/input/actions":
            if key == "match_num":
                mn = int(val)
                for i in range(6):
                    self.output(page, "team-{}-{}".format(i, mn), self.data.get_actions_team(mn, i))
                    self.output(page, "actions-{}-{}".format(i, mn), self.data.get_actions_actions(mn, i))
                    self.output(page, "scouter-{}-{}".format(i, mn), self.data.get_actions_scouter(mn, i))
                return
            if key.startswith("actions"):
                spot,match = map(int,key.split("-")[1:])
                self.data.set_actions_actions(match, spot, val.upper())
                return

            if key.startswith("scouter"):
                spot,match = map(int,key.split("-")[1:])
                self.data.set_actions_scouter(match, spot, val.upper())
                return

        print("Page {}; Key {}; Value {}".format(page,key,val))










