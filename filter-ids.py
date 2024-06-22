#!/usr/bin/env python3

import json

def contains_id(rel_label):
    l = rel_label.lower()
    for id_word in ["code", "id", "slug"]:
        if id_word in l: return True
    if rel_label in ["FIG gymnast biography number",
                     "coordinate location"]: return True
    return False

def is_wp_label(item_label):
    return len(item_label) != 0 and item_label[0] == "Q"

def entity_is_good(entity):
    return not (contains_id(entity["relLabel"]) or
                is_wp_label(entity["itemLabel"]) or
                is_wp_label(entity["otherLabel"]))

open("datasets/triples-filtered.json", "w").write(json.dumps([entity
                                                              for entity
                                                              in json.loads(open("datasets/wd-extract.json", "r").read())
                                                              if entity_is_good(entity)]))
