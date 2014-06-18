import random

from ..common import surround_list

def transpose(array):
    x = [[] for e in array[0]]
    for i in range(len(array)):
        for j in range(len(array[i])):
            x[j].append(array[i][j])
    return x

def mean(li):
    return sum(li) / len(li)

def r1(x):
    return round(x,1)



class Analysis():
    conversion = {
        'A': ("AHH", "Auto: Hot High Score"),
        'B': ("AHC", "Auto: Cold High Score"),
        'C': ("AHX", "Auto: High Goal Miss"),
        'D': ("ALH", "Auto: Hot Low Score"),
        'E': ("ALC", "Auto: Cold Low Score"),
        'F': ("ALX", "Auto: Low Goal Miss"),
        'G': ("AGB", "Auto: Goalie Blocked Ball"),
        'H': ("TX",  "Truss Fail"),
        'I': ("THP", "Truss Human Player"),
        'J': ("TF",  "Truss to Field"),
        'K': ("CX",  "Catch attempt failed"),
        'L': ("CC",  "Ball caught"),
        'M': ("HX",  "High goal failed"),
        'N': ("HS",  "High goal scored"),
        'O': ("LX",  "Low goal failed"),
        'P': ("LS",  "Low goal scored"),
        'Q': ("GP",  "Pickup from ground"),
        'R': ("GD",  "Drop to ground"),
        'S': ("DP",  "Robot-to-Robot direct pass"),
        'T': ("PHP", "Passed to Human Player"),
        'U': ("RHP", "Received from Human Player"),
        'V': ("DEF", "Played Defense"),
        'W': ("DRB", "Dead robot"),
        'X': ("DBL", "Dead ball"),
        'Y': ("ARB", "Robot alive!"),
        'Z': ("DAM", "Damaged Robot")
    }

    def get_robot_match_header(self):
        header = ["Auto Contribution", "Tele Contributions","Match log"]
        return header

    def get_robot_match_results(self, robot_data, robot, match):
        match_data = robot_data[(match,)]
        i = match_data["teams"].index(robot)
        if i < 3:
            alliance_scores = match_data["score"][0]
        else:
            alliance_scores = match_data["score"][1]

        log=[]
        for letter in match_data["actions"][i]:
            log.append(Analysis.conversion[letter][1])

        values = [round(alliance_scores[1] / 3, 1),
                round(alliance_scores[0] / 3, 1), surround_list(log, "div")]
        return values

    def get_robot_stats_header(self):
        return ["Auto Contribution", "Tele Contributions"]
    def get_robot_stats_results(self, data, robot):
        arr = [self.get_robot_match_results(data, robot, match[0]) for match in data]
        t = transpose(arr)

        return {"min":[r1(min(t[0])),r1(min(t[1]))], "max":[r1(max(t[0])),r1(max(t[1]))], "avg":[r1(mean(t[0])),r1(mean(t[1]))]}
