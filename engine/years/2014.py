import random


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

    def match_attributes(self, robot, match, match_data):
        """
        Returns a list of [key, value] pairs.
        """
        i = match_data["teams"].index(robot)
        if i < 3:
            alliance_scores = match_data["score"][0]
        else:
            alliance_scores = match_data["score"][1]

        log = [Analysis.conversion[letter][1]
               for letter in match_data["actions"][i]]
        contr_tele = alliance_scores[0] / 3
        contr_auto = alliance_scores[1] / 3
        contr_foul = alliance_scores[2] / 3

        return [("Auto contribution", float(contr_auto)),
                ("Tele contribution", float(contr_tele)),
                ("Foul incidence", float(contr_foul)),
                ("Match log", list(log))]
