#!/usr/bin/env python3

import sqlite3
import re

with open("300.txt", "r") as in_file:
    res = []
    for line in in_file.readlines():
        found = re.match(r'^\[(\d+)\] generated question: "(.*)" with answer: "(.*)"$', line)
        if found:
            g = found.groups()
            res.append((g[1], g[2], g[0]))
            print(f"question: {found.groups()[1]}")
            print(f"answer: {found.groups()[2]}")
            print(f"id: {found.groups()[0]}")
    db_conn = sqlite3.connect("db.db")
    db_cur = db_conn.cursor()
    db_cur.executemany("update triples set question = ?, answer = ? where id = ?", res)
    db_conn.commit()
