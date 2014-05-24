__all__ = ["Engine"]

import os,csv,io,json,random
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
        return d

class Store():
    """
        There are two encoding choices: JSON and CSV.
        CSV has less overhead, JSON is easier to edit by hand.
        CSV is easy. in table editor. We choose CSV.
    """

    scores = "RedAuto, RedTele, RedFoul, BlueAuto, BlueTele, BlueFoul".split(", ")
    match = "Match"
    entries = "T0, A0, S0, T1, A1, S1, T2, A2, S2, T3, A3, S3, T4, A4, S4, T5, A5, S5".split(", ")
    header = [match] + scores + entries

    def __init__(self, path):
        self.path = path + "/data"
        self.load()

    def save(self):
        arr = [Store.header]
        for k in sorted(self.data.keys()):
            arr.append(self.data[k].to_list())
        with open(self.path,"w") as f:
            f.write(csvify(arr))

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

            print(self.index)

        else:
            self.reset()

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


        for key in list(self.data.keys()):
            if key not in overall:
                self.delete_entry(key)
        for key in overall:
            self.mod_entry(key, overall[key])

        # also: pass list of match pages to update/force
        # and list of robots to update?
        # or just do an internal mark-dirty & let the Engine handle it?

        self.save()
        return self.schedule_regen()
    def reset_schedule(self):
        print("NO RESET ALLOWED! BAD FEATURE!")

        return self.schedule_regen()
    def schedule_regen(self):
        st = [Store.sched_header]
        for key in sorted(self.data.keys()):
            match = self.data[key]
            st.append([key] + [match[i]["Team"] for i in range(6)])

        # raw, table
        return csvify(st), tablify(st)

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

    def get_score(self, match, key):
        if match in self.data:
            v = self.data[match].scores()[key]
            if not v:
                return 0
            return int(v)
        else:
            return 0
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
        self.data = Store(path)
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
                self.output("/input/actions","match_list",self.data.matchoptions())
                self.output("/input/match","match_list",json.dumps(self.data.matchlist()))
                return
            if key == "csv_reset":
                sr,st = self.data.reset_schedule()
                self.output(page,"csv_entry",sr)
                self.output(page,"csv_table",st)
                self.output("/input/actions","match_list",self.data.matchoptions())
                self.output("/input/match","match_list",json.dumps(self.data.matchlist()))
                return
        if page == "/input/actions":
            if key == "match_num":
                for i in range(6):
                    self.output(page, "team-{}-{}".format(i, val), self.data.get_actions_team(val, i))
                    self.output(page, "actions-{}-{}".format(i, val), self.data.get_actions_actions(val, i))
                    self.output(page, "scouter-{}-{}".format(i, val), self.data.get_actions_scouter(val, i))
                return
            if key.startswith("actions"):
                spot,match = key.split("-",maxsplit=2)[1:]
                self.data.set_actions_actions(match, int(spot), val.upper())
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
                return


        print("\033[1;31m[Fall]\033[0m Page {}; Key {}; Value {}".format(page,key,val))










