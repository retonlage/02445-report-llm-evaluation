#!/usr/bin/env python3

import csv
import sqlite3

def preprocess_han(parsed):
    res = []
    for row in parsed:
        res.append((row[15], row[1], row[15].split("|")[2]))
    return res

def load_csv(filename):
    with open(filename, "r") as f:
        reader = csv.reader(f)
        l = list(reader)[1:]
        return l

def save(data):
    db_conn = sqlite3.connect("examples.db")
    db_cursor = db_conn.cursor()
    db_cursor.executemany("insert into finetuning_examples (triple, question, answer) values (?, ?, ?)", data)
    db_conn.commit()

save(preprocess_han(load_csv("datasets/test.csv")))
