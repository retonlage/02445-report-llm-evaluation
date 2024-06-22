#!/usr/bin/env python3

import sqlite3
import json
import random

with open("datasets/triples-filtered.json", "r") as f:
    items = json.loads(f.read())

triples = [(f"{item['itemLabel']} | {item['relLabel']} | {item['otherLabel']}",) for item in items]
random.shuffle(triples)

db_conn = sqlite3.connect("db.db")
db_cur = db_conn.cursor()
db_cur.executemany("insert into 'triples' (triple) values (?)", triples)
db_conn.commit()
