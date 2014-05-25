import random

from ..common import surround_list

class Analysis():
    conversion = {
        'A':("AHH", "Auto: Hot High Score"),
        'B':("AHC", "Auto: Cold High Score"),
        'C':("AHX", "Auto: High Goal Miss"),
        'D':("ALH", "Auto: Hot Low Score"),
        'E':("ALC", "Auto: Cold Low Score"),
        'F':("ALX", "Auto: Low Goal Miss"),
        'G':("AGB", "Auto: Goalie Blocked Ball"),
        'H':("TX",  "Truss Fail"),
        'I':("THP", "Truss Human Player"),
        'J':("TF",  "Truss to Field"),
        'K':("CX",  "Catch attempt failed"),
        'L':("CC",  "Ball caught"),
        'M':("HX",  "High goal failed"),
        'N':("HS",  "High goal scored"),
        'O':("LX",  "Low goal failed"),
        'P':("LS",  "Low goal scored"),
        'Q':("GP",  "Pickup from ground"),
        'R':("GD",  "Drop to ground"),
        'S':("DP",  "Robot-to-Robot direct pass"),
        'T':("PHP", "Passed to Human Player"),
        'U':("RHP", "Received from Human Player"),
        'V':("DEF", "Played Defense"),
        'W':("DRB", "Dead robot"),
        'X':("DBL", "Dead ball"),
        'Y':("ARB", "Robot alive!"),
        'Z':("DAM", "Damaged Robot")
         }


    def __init__(self, data):
        self.data = data
    def get_robot_match_header(self):
        header = ["Auto Contribution","Tele Contributions"]
        return header
    def get_robot_match_results(self, robot, match):
        spot = self.data.get_robot_spot(robot, match)
        alliance_scores = self.data.get_alliance_score(match, spot)
        actions = self.data.data[match][spot]["Actions"]


        values = [round(alliance_scores["Auto"]/3,1),round(alliance_scores["Tele"]/3,1)]
        return values





