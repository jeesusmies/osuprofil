import requests
import json

OSU_URL = 'https://osu.ppy.sh/api/get_user'

class Owrap:
    def __init__(self):
        pass
    
    def _return_dict(self, parse_json):
        if parse_json == 0:
            print("aaa")
            return
        result = {"pp_rank": int(parse_json[0]),
                  "pp_raw": float(parse_json[1]),
                  "level": float(parse_json[2]),
                  "accuracy": round(float(parse_json[3]), 2),
                  "playcount": int(parse_json[4]),
                  "ranked_score": int(parse_json[5]),
                  "total_score": int(parse_json[6]),
                  "count300": int(parse_json[7]),
                  "count100": int(parse_json[8]),
                  "count50": int(parse_json[9])}
        
        return result
        
    def _parse_json(self, r):
        # lol variable names because i am stupid
        result = []
        #json_thing = r.json()
        data = r
        try:
            result.extend((data["pp_rank"],
                        data["pp_raw"],
                        data["level"],
                        data["accuracy"],
                        data["playcount"],
                        data["ranked_score"],
                        data["total_score"],
                        data["count300"],
                        data["count100"],
                        data["count50"]))
        except:
            return 0 # means not found or something is broken
        
        return result
        
    def osu(self, r):
        return self._return_dict(self._parse_json(r))
        
