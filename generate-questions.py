#!/usr/bin/env python3

from anthropic import Anthropic
import sqlite3
import sys

def triple_to_prompt(triple):
    return f"""The following is a object-relation-subject triple from wikidata. Transform the triple into a question. Here are some examples: "
1|Tenors | publication date | 1988-01-01T00:00:00 => When was Tenors published? | 1988-01-01
2|Tennōjuku Station | instance of | railway station above ground => What is Tennōjuku Station? | A railway station
3|Tasuj District | number of households | 6458 => How many households are there in Tasuj District? | 6458
4|Tapiwa Zivira | occupation | journalist => What does Tapiwa Zivira's work as? | A Journalist
5|Switch V | form of creative work | studio album => What form of creative work is Switch V? | A studio album
6|Steven Lee Olsen | social media followers | 14055 => How many social media followers does Steven Lee Olsen have? | 14055
7|Steve Zabriskie | given name | Steve => What is Steve Zabriskie's given name? | Steve
8|1984 Stafford by-election | parliamentary term | 49th Parliament of the United Kingdom => In what parliamentary term did the 1984 Stafford by-election occur in? | 49th Parliament
9|Sri Krishna Rai Hridyesh | writing language | Hindi => What language does Sri Krishna Rai Hridyesh write in? | Hindi
10|Sketchy Three EP | number of parts of this work | 6 => How many part does Sketchy Three EP have? | 6"
The triple to transform is: {triple}.
Reply with only the question and answer separated by a pipe"""

def generate_question_claude(triple):
    client = Anthropic()
    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1000,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": triple_to_prompt(triple)
                    }
                ]
            }
        ]
        )
    return message.content[0].text

(startid, stopid) = (sys.argv[1], sys.argv[2])
db_conn = sqlite3.connect("db.db")
db_cur = db_conn.cursor()
db_cur.execute("select id, triple from 'triples' where id >= ? and id < ? and question is null", (startid, stopid))
triples = db_cur.fetchall()
for (i, triple) in triples:
    print(f"[{i}] generating question for '{triple}'")
    question, answer = generate_question_claude(triple).split("|")
    print(f"[{i}] generated question: \"{question}\" with answer: \"{answer}\"")
    db_cur.execute("update 'triples' set question = ?, answer = ?, generator = ? where id = ?", (question, answer, "claude-sonnet-3.5", i))
db_conn.commit()
