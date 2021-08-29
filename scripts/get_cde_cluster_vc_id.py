import sys
import json
import os

def get_vc_id(all_vcs, vc_name):
    for vc in all_vcs["vcs"]:
        if vc["vcName"] == vc_name:
            print(vc_name)
            return vc["vcId"]

with open("vcs.json") as json_vcs_file:
    all_vcs = json.load(json_vcs_file)
