import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
import sqlite3
import re
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from nltk.tokenize import word_tokenize

def clean_answer(answer):
    if not isinstance(answer, str):
        return ""
    cleaned = answer.strip()
    cleaned = re.sub(r'[.!?,;:]+$', '', cleaned)
    return cleaned

def load_data_from_sqlite(db_path):
    conn = sqlite3.connect(db_path)
    query = """
    SELECT id, answer,
           oai_answer, anthropic_answer, mistral_answer
    FROM triples
    WHERE answer IS NOT NULL
      AND oai_answer IS NOT NULL
      AND anthropic_answer IS NOT NULL
      AND mistral_answer IS NOT NULL
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

df = load_data_from_sqlite("db.db")

for col in ['answer', 'oai_answer', 'anthropic_answer', 'mistral_answer']:
    df[col] = df[col].apply(clean_answer)

anova_data = pd.melt(df,
                     id_vars=['id'],
                     value_vars=['oai_bleu', 'anthropic_bleu', 'mistral_bleu'],
                     var_name='answerer',
                     value_name='bleu_score')
anova_data['answerer'] = anova_data['answerer'].str.replace('_bleu', '')

model = ols('bleu_score ~ C(answerer)', data=anova_data).fit()
anova_table = sm.stats.anova_lm(model, typ=2)
print("One-way ANOVA results:")
print(anova_table)

def calculate_eta_squared(anova_table):
    eta_squared = {}
    ss_total = anova_table['sum_sq'].sum()
    for index, row in anova_table.iterrows():
        if index != 'Residual':
            eta_squared[index] = row['sum_sq'] / ss_total
    return eta_squared

eta_squared = calculate_eta_squared(anova_table)
print("\nEta-squared value:")
print(f"C(answerer): {eta_squared['C(answerer)']:.6f}")

from statsmodels.stats.multicomp import pairwise_tukeyhsd

print("\nPost-hoc Tukey HSD test for answerer models:")
tukey_answerer = pairwise_tukeyhsd(anova_data['bleu_score'], anova_data['answerer'])
print(tukey_answerer)
