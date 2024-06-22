from openai import OpenAI
from anthropic import Anthropic
import mistralai
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import os
import sys
import json
import csv
import string
import requests
from bs4 import BeautifulSoup
import sqlite3
import re

def load_csv(filename):
    with open(filename, "r") as f:
        reader = csv.reader(f)
        return list(reader)

def search_internet(query):
    res = requests.get("http://127.0.0.1:8080/search",
                       params={"q": query, "format": "json"},)
    if res.status_code != 200:
        return "Search error"
    return [{key: val for key, val in result.items() if key in ["url", "title", "content"]} for result in res.json()["results"]]

def extract_final_answer(full_response):
    match = re.search(r'[(.+?)]', full_response, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return "No final answer found"

    # --------- OPENAI
def openai_raw_prompt(question):
    return f"{question} Answer as succinctly as possible, preferably with a single word."

def openai_get_answer(question):
    client = OpenAI(api_key = os.environ.get("OAI_KEY"))
    return client.chat.completions.create(
            messages = [{"role": "user", "content": openai_raw_prompt(question)}],
            model="gpt-4o").choices[0].message.content

def openai_cot_prompt(question):
    return f"{question} Let's think through this step-by-step, but enclose your final answer in square brackets ([  ]) at the end of your response. Answer as succinctly as possible, preferably with a single word."

def openai_get_cot_answer(question):
    client = OpenAI(api_key = os.environ.get("OAI_KEY"))
    response = client.chat.completions.create(
            messages = [{"role": "user", "content": openai_cot_prompt(question)}],
            model="gpt-4o").choices[0].message.content

    return extract_final_answer(response)

 # CLAUDE

def claude_raw_prompt(question):
    return f"{question} Answer as succinctly as possible, preferably with a single word."

def claude_get_answer(question):
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
                        "text": claude_raw_prompt(question)
                        }
                    ]
                }
            ]
        )
    answer = message.content[0].text
    return answer

def claude_cot_prompt(question):
    return f"{question} Let's think through this step-by-step, but enclose your final answer in square brackets ([  ]) at the end of your response. Answer as succinctly as possible, preferably with a single word."

def claude_get_cot_answer(question):
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
                        "text": claude_cot_prompt(question)
                        }
                    ]
                }
            ]
        )
    answer = message.content[0].text
    return extract_final_answer(answer)

def claude_browse_prompt(question, history):
    return f"{question} You can use the search_tool function to look up information online if needed."

def claude_get_browse_answer(question):
    client = Anthropic()
    history = ""
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
                        "text": claude_browse_prompt(question)
                        }
                    ]
                }
        ],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "search_tool",
                    "description": "Search the internet for current information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ])
    answer = message.content[0].text
    attempted_extraction = extract_final_answer(answer)
    return

 # MISTRAL ------

def mistral_raw_prompt(question):
    return f"{question} Be brief. Answer with a single word only"

def mistral_get_answer(question):
    api_key = os.environ["MISTRAL_API_KEY"]
    model = "mistral-large-latest"
    client = MistralClient(api_key=api_key)
    messages = [
        ChatMessage(role="user", content=mistral_raw_prompt(question))
    ]
    chat_response = client.chat(
        model=model,
        messages=messages,
    )
    return chat_response.choices[0].message.content

def mistral_cot_prompt(question):
    return f"{question} Let's think through this step-by-step, but enclose your final answer in square brackets ([  ]) at the end of your response. Be brief. Answer with a single word only"

def mistral_get_cot_answer(question):
    api_key = os.environ["MISTRAL_API_KEY"]
    model = "mistral-large-latest"
    client = MistralClient(api_key=api_key)
    messages = [
        ChatMessage(role="user", content=mistral_cot_prompt(question))]


# -----------

def get_claude_raw_answers(k):
    db_conn = sqlite3.connect("db.db")
    db_cur = db_conn.cursor()
    db_res = db_cur.execute("select id, question from triples where question is not null and anthropic_answer is null and id < ?", (k,))
    for (i, question) in db_res.fetchall():
        print(f"{i} answering '{question}' with claude")
        answer = claude_get_answer(question)
        db_cur.execute("update triples set anthropic_answer = ? where id = ?", (answer, i))
        db_conn.commit()
        print(f"{i} got answer '{answer}' with claude")

def get_claude_cot_answers():
    db_conn = sqlite3.connect("db.db")
    db_cur = db_conn.cursor()
    db_res = db_cur.execute("select id, question from triples where question is not null and claude_cot_answer is null")
    for (i, question) in db_res.fetchall():
        print(f"{i} answering '{question}' with gpt")
        answer = claude_get_cot_answer(question)
        # db_cur.execute("update triples set claude_cot_answer = ? where id = ?", (answer, i))
        # db_conn.commit()
        print(f"{i} got answer '{answer}' with gpt")

def get_openai_raw_answers(k):
    db_conn = sqlite3.connect("db.db")
    db_cur = db_conn.cursor()
    db_res = db_cur.execute("select id, question from triples where question is not null and oai_answer is null and id < ?", (k,))
    for (i, question) in db_res.fetchall():
        print(f"{i} answering '{question}' with gpt")
        answer = openai_get_answer(question)
        db_cur.execute("update triples set oai_answer = ? where id = ?", (answer, i))
        db_conn.commit()
        print(f"{i} got answer '{answer}' with gpt")

def get_openai_cot_answers():
    db_conn = sqlite3.connect("db.db")
    db_cur = db_conn.cursor()
    db_res = db_cur.execute("select id, question from triples where question is not null and oai_cot_answer is null")
    for (i, question) in db_res.fetchall():
        print(f"{i} answering '{question}' with gpt")
        answer = openai_get_cot_answer(question)
        # db_cur.execute("update triples set oai_cot_answer = ? where id = ?", (answer, i))
        # db_conn.commit()
        print(f"{i} got answer '{answer}' with gpt")

def get_mistral_raw_answers(k):
    db_conn = sqlite3.connect("db.db")
    db_cur = db_conn.cursor()
    db_res = db_cur.execute("select id, question from triples where question is not null and mistral_answer is null and id < ?", (k,))
    for (i, question) in db_res.fetchall():
        print(f"{i} answering '{question}' with mistral")
        answer = mistral_get_answer(question)
        db_cur.execute("update triples set mistral_answer = ? where id = ?", (answer, i))
        db_conn.commit()
        print(f"{i} got answer '{answer}' with mistral")

def get_mistral_cot_answers():
    db_conn = sqlite3.connect("db.db")
    db_cur = db_conn.cursor()
    db_res = db_cur.execute("select id, question from triples where question is not null and mistral_cot_answer is null")
    for (i, question) in db_res.fetchall():
        print(f"{i} answering '{question}' with mistral")
        answer = mistral_get_cot_answer(question)
        # db_cur.execute("update triples set mistral_cot_answer = ? where id = ?", (answer, i))
        # db_conn.commit()
        print(f"{i} got answer '{answer}' with mistral")

k = sys.argv[1]
print(k)
model = sys.argv[2]

if model == "mistral":
    get_mistral_raw_answers(k)
elif model == "openai":
    get_openai_raw_answers(k)
elif model == "claude":
    get_claude_raw_answers(k)
