#!/usr/bin/env python3
from openai import OpenAI
import mistralai
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from sklearn.metrics.pairwise import euclidean_distances
import os
import re
import sqlite3

def mistral_rate_answers(correct_answer, model_answers):
    api_key = os.environ["MISTRAL_API_KEY"]
    client = MistralClient(api_key=api_key)
    embeddings_batch_response = client.embeddings(
        model="mistral-embed",
        input = [correct_answer] + model_answers,
    )
    correct_embedding = embeddings_batch_response.data[0].embedding
    answer_embeddings = [data.embedding for data in embeddings_batch_response.data[1:]]
    return [euclidean_distances([correct_embedding], [answer_embedding])[0][0] for answer_embedding in answer_embeddings]

def gpt_get_single_embedding(potential_answer):
    client = OpenAI()
    response = client.embeddings.create(
        input=potential_answer,
        model="text-embedding-3-large"
    )
    return response.data[0].embedding

def gpt_rate_answers(correct_answer, model_answers):
    correct_embedding = gpt_get_single_embedding(correct_answer)
    answer_embeddings = [gpt_get_single_embedding(answer) for answer in model_answers]
    return [euclidean_distances([correct_embedding], [answer_embedding])[0][0] for answer_embedding in answer_embeddings]

def clean_answer(answer):
    cleaned = re.sub(r'[.!?,;:]+$', '', answer)
    cleaned = cleaned.strip()
    return cleaned

db_conn = sqlite3.connect("db.db")
db_cur = db_conn.cursor()
db_res = db_cur.execute("select id, rater, answer, oai_answer, anthropic_answer, mistral_answer from triples where (rater is not null and mistral_distance is null)")

for (i, rater, correct_answer, oai_answer, anthropic_answer, mistral_answer) in db_res.fetchall():
    (correct_answer, oai_answer, anthropic_answer, mistral_answer) = (clean_answer(answer) for answer in (correct_answer, oai_answer, anthropic_answer, mistral_answer))
    print(f"{i} getting embedding distances, correct answer: {correct_answer}, oai_answer: {oai_answer}, anthropic_answer: {anthropic_answer}, mistral_answer: {mistral_answer},")
    rater_func = mistral_rate_answers if rater == "mistral" else gpt_rate_answers
    distances = rater_func(clean_answer(correct_answer), [oai_answer, anthropic_answer, mistral_answer])
    print(f"{i} oai_distance: {distances[0]}, anthropic_distance: {distances[1]}, mistral_distance: {distances[2]}")
    db_cur.execute("update triples set oai_distance = ?, anthropic_distance = ?, mistral_distance = ? where id = ?", distances + [i])
    db_conn.commit()
