import os,csv,io,json,random
from collections import defaultdict

def readcsv(string):
    reader = csv.reader(string.split("\n"))
    return [list(map(lambda u:u.strip(),row)) for row in reader if row]

class Match():
    def __init__(self, store=None):
        if store is None:
            store = defaultdict(str)
        self.store = store

    def to_list(self):
        return [self.store[k] for k in Store.header]

    def __getitem__(self, i):
        if i < 0 or i > 6:
            raise IndexError
        l = str(i)
        return {"Team":self.store["T"+l],"Actions":self.store["A"+l],"Scouter":self.store["S"+l]}

    def set_slot(self, slot, key, val):
        translate = {"Actions":"A","Team":"T","Scouter":"S"}
        self.store[translate[key]+str(slot)] = val

    def scores(self):
        d = {}
        for s in Store.scores:
            d[s] = self.store[s]
            if not d[s]:
                d[s] = 0
            else:
                d[s] = int(d[s])
        return d

class Store():
    """
        There are two encoding choices: JSON and CSV.
        CSV has less overhead, JSON is easier to edit by hand.
        CSV is easy. in table editor. We choose CSV.
    """

    # TODO: typing
    scores = "RedAuto, RedTele, RedFoul, BlueAuto, BlueTele, BlueFoul".split(", ")
    match = "Match"
    entries = "T0, A0, S0, T1, A1, S1, T2, A2, S2, T3, A3, S3, T4, A4, S4, T5, A5, S5".split(", ")
    header = [match] + scores + entries

    def __init__(self, path):
        self.path = path + "/data"
        self.load()

    def save(self):
        with open(self.path,"w") as f:
            writer = csv.writer(f)
            writer.writerow(Store.header)
            for k in sorted(self.data.keys()):
                writer.writerow(self.data[k].to_list())

    def load(self):
        if os.path.exists(self.path):
            with open(self.path) as f:
                array = readcsv(f.read())[1:]

            self.data = {}
            self.index = defaultdict(set)
            for row in array:
                store = dict(zip(Store.header, row))
                num = store[Store.match]
                match = Match(store)
                self.data[num] = match
                for i in range(6):
                    self.index[match[i]["Team"]].add(num)

            self.regen_index()
        else:
            self.reset()

    def regen_index(self):
        old = self.index
        self.index = defaultdict(set)
        for match, data in self.data.items():
            for i in range(6):
                self.index[data[i]["Team"]].add(match)
        return [robot for robot in old if robot not in self.index]

    def reset(self):
        self.data = {}
        self.index = {}

        self.save()

    sched_header = ["Match","Red1","Red2","Red3","Blue1","Blue2","Blue3"]

    def delete_entry(self, match):
        del self.data[match]

    def mod_entry(self, match, scheddat):
        translate = {"Match":"Match","Red1":"T0","Red2":"T1","Red3":"T2",
                     "Blue1":"T3","Blue2":"T4","Blue3":"T5"}
        if match not in self.data:
            self.data[match] = Match()
        store = self.data[match].store
        for key in translate:
            store[translate[key]] = scheddat[key]

    def update_schedule(self, data):
        blk = readcsv(data)
        if not blk:
            return self.schedule_regen()
        hset = set(blk[0])
        if set(Store.sched_header) != hset:
            return self.schedule_regen()
        if any(len(r) < len(blk[0]) for r in blk[1:]):
            return self.schedule_regen()
        dicts = [dict(zip(blk[0], blk[i])) for i in range(1,len(blk))]
        overall = {}
        for d in dicts:
            overall[d["Match"]] = d

        deleted = []
        for key in list(self.data.keys()):
            if key not in overall:
                self.delete_entry(key)
                deleted.append(key)
        for key in overall:
            self.mod_entry(key, overall[key])

        # also: pass list of match pages to update/force
        # and list of robots to update?
        # or just do an internal mark-dirty & let the Engine handle it?

        deleted_robots = self.regen_index()
        self.save()
        return self.schedule_regen(), deleted, deleted_robots
    def reset_schedule(self):
        print("NO RESET ALLOWED! BAD FEATURE!")

        self.regen_index()
        return self.schedule_regen(), [], []
    def schedule_regen(self):
        st = [Store.sched_header]
        for key in sorted(self.data.keys()):
            match = self.data[key]
            st.append([key] + [match[i]["Team"] for i in range(6)])

        # raw, table
        return st

    def get_actions(self,match,spot, key,default):
        if match in self.data:
            return self.data[match][spot][key]
        else:
            return default
    def set_actions(self,match,spot,key,val):
        if match in self.data:
            self.data[match].set_slot(spot, key, val)
            self.save()
        else:
            print("Invalid match: |{}|".format(match))


    def get_actions_team(self, match, spot):
        return self.get_actions(match,spot,"Team","????")
    def get_actions_actions(self, match, spot):
        return self.get_actions(match,spot,"Actions","")
    def get_actions_scouter(self, match, spot):
        return self.get_actions(match,spot,"Scouter","")

    def set_actions_actions(self, match, spot, string):
        self.set_actions(match,spot,"Actions",string)

    def set_actions_scouter(self, match, spot, initials):
        self.set_actions(match,spot,"Scouter",initials)

    def matchoptions(self):
        items = sorted(self.data.keys())

        s = "".join("<option>{}</option>".format(i) for i in items)

        return s
    def matchlist(self):
        return sorted(self.data.keys())
    def robotlist(self):
        return sorted(self.index.keys())

    def get_score(self, match, key):
        if match in self.data:
            v = self.data[match].scores()[key]
            if not v:
                return 0
            return int(v)
        else:
            return 0
    def get_total_score(self, match, term):
        if match not in self.data:
            return 0

        keys = ("Tele","Auto","Foul")
        scores = self.data[match].scores()
        s = 0
        for k in keys:
            j = scores[term+k]
            if j:
                s += int(j)
        return s
    def get_red_tele_score(self, match):
        return self.get_score(match, "RedTele")
    def get_red_auto_score(self, match):
        return self.get_score(match, "RedAuto")
    def get_red_foul_score(self, match):
        return self.get_score(match, "RedFoul")
    def get_blue_tele_score(self, match):
        return self.get_score(match, "BlueTele")
    def get_blue_auto_score(self, match):
        return self.get_score(match, "BlueAuto")
    def get_blue_foul_score(self, match):
        return self.get_score(match, "BlueFoul")
    def set_score(self, match, item, val):
        if match in self.data:
            self.data[match].store[item] = val
        self.save()
    def get_robot(self, match, term, i):
        if match not in self.data:
            return "????"

        if term == "Red":
            index = (i-1)
        elif term == "Blue":
            index = (i-1) + 3
        else:
            return "?term?"

        return self.data[match][index]["Team"]

    def get_robot_spot(self, robot, match):
        d = self.data[match]
        for i in range(6):
            if d[i]["Team"] == robot:
                return i
        raise KeyError
    def get_alliance_score(self, match, spot):
        scores = self.data[match].scores()

        keys = ("Tele","Auto","Foul")
        if spot < 3:
            group = "Red"
        else:
            group = "Blue"
        translate = dict(zip((group + k for k in keys) ,keys))
        v = {}
        for key in translate:
            v[translate[key]] = scores[key]
        return v







    def match_exists(self, match):
        return match in self.data
    def robot_exists(self, robot):
        return robot in self.index
    def get_matches(self, robot):
        return sorted(self.index[robot])
