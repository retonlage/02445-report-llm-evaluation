#!/usr/bin/env python3
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.power import FTestAnovaPower
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from nltk.tokenize import word_tokenize
import sqlite3
import  matplotlib.pyplot as plt

def load_data_from_sqlite(db_path):
    conn = sqlite3.connect(db_path)
    query = """
    SELECT id, rater, triple, answer,
           oai_answer, anthropic_answer, mistral_answer,
           oai_distance, anthropic_distance, mistral_distance
    FROM triples
    WHERE rater IS NOT NULL
      AND (oai_distance IS NOT NULL OR anthropic_distance IS NOT NULL OR mistral_distance IS NOT NULL)
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def calculate_bleu(reference, candidate):
    smooth = SmoothingFunction()
    reference_tokens = word_tokenize(reference.lower())
    candidate_tokens = word_tokenize(candidate.lower())
    return sentence_bleu([reference_tokens], candidate_tokens, smoothing_function=smooth.method1)

def rank_based_inverse_normal_transform(series):
    n = len(series)
    temp = series.argsort().argsort() # double argsort for ranking
    return stats.norm.ppf((temp + 0.5) / n)

df = load_data_from_sqlite("db.db")
df = df.drop(df[df["triple"].map(lambda triple: triple.split("|")[1].strip()) == "Commons category"].index)

df['oai_bleu'] = df.apply(lambda row: calculate_bleu(row['answer'], row['oai_answer']), axis=1)
df['anthropic_bleu'] = df.apply(lambda row: calculate_bleu(row['answer'], row['anthropic_answer']), axis=1)
df['mistral_bleu'] = df.apply(lambda row: calculate_bleu(row['answer'], row['mistral_answer']), axis=1)

distance_data = pd.melt(df,
                     id_vars=['id', 'rater'],
                     value_vars=['oai_distance', 'anthropic_distance', 'mistral_distance'],
                     var_name='answerer',
                     value_name='distance')
distance_data['answerer'] = distance_data['answerer'].str.replace('_distance', '')

bleu_data = pd.melt(df,
                     id_vars=['id', 'rater'],
                     value_vars=['oai_bleu', 'anthropic_bleu', 'mistral_bleu'],
                     var_name='answerer',
                     value_name='bleu')
bleu_data['answerer'] = bleu_data['answerer'].str.replace('_bleu', '')

distance_data = distance_data.dropna()

distance_data['normalized_distance'] = distance_data.groupby('rater')['distance'].transform(rank_based_inverse_normal_transform)

def draw_dist_boxplot(anova_data):
    # Prepare the data
    data = [anova_data[anova_data["answerer"] == "oai"]["normalized_distance"],
            anova_data[anova_data["answerer"] == "anthropic"]["normalized_distance"],
            anova_data[anova_data["answerer"] == "mistral"]["normalized_distance"]]
    labels = ['OpenAI', 'Anthropic', 'Mistral']
    plt.figure(figsize=(12, 6))
    boxplot = plt.boxplot(data, labels=labels, patch_artist=True)
    colors = ['lightblue', 'lightgreen', 'lightpink']
    for patch, color in zip(boxplot['boxes'], colors):
        patch.set_facecolor(color)
    for i, d in enumerate(data):
        y = d
        x = np.random.normal(i + 1, 0.04, size=len(y))
        plt.scatter(x, y, alpha=0.3, s=5, color='black')
    plt.savefig("box.png")

def draw_boxplot(data, filename, value):
    data = [data[data["answerer"] == "oai"][value],
            data[data["answerer"] == "anthropic"][value],
            data[data["answerer"] == "mistral"][value]]
    labels = ['OpenAI', 'Anthropic', 'Mistral']
    plt.figure(figsize=(12, 6))
    boxplot = plt.boxplot(data, labels=labels, patch_artist=True)
    colors = ['lightblue', 'lightgreen', 'lightpink']
    for patch, color in zip(boxplot['boxes'], colors):
        patch.set_facecolor(color)
    for i, d in enumerate(data):
        y = d
        x = np.random.normal(i + 1, 0.04, size=len(y))
        plt.scatter(x, y, alpha=0.3, s=5, color='black')
    plt.savefig(filename)

draw_boxplot(distance_data, "distance_box.png", "normalized_distance")
draw_boxplot(bleu_data, "bleu_box.png", "bleu")

def plot_bleu_distance_correlation(distance_data, bleu_data):
    merged_data = pd.merge(distance_data, bleu_data, on=['id', 'rater', 'answerer'])
    plt.figure(figsize=(10, 8))
    colors = {'oai': 'blue', 'anthropic': 'green', 'mistral': 'red'}
    for answerer in merged_data['answerer'].unique():
        subset = merged_data[merged_data['answerer'] == answerer]
        plt.scatter(subset['bleu'], -subset['normalized_distance'],
                    c=colors[answerer], label=answerer, alpha=0.5)

    plt.title('BLEU vs Normalized Distance')
    plt.xlabel('BLEU Score')
    plt.ylabel('Normalized Distance')
    plt.legend()

    # Calculate and print R² for each answerer
    for answerer in merged_data['answerer'].unique():
        subset = merged_data[merged_data['answerer'] == answerer]
        r, p = stats.pearsonr(subset['bleu'], -subset['normalized_distance'])
        r2 = r**2
        print(f"{answerer} R²: {r2:.4f}")

    plt.savefig('bleu_distance_correlation.png')
    plt.close()

plot_bleu_distance_correlation(distance_data, bleu_data)

# --- ANOVA -------
model = ols('normalized_distance ~ C(rater) + C(answerer) + C(rater):C(answerer)', data=distance_data).fit()
anova_table = sm.stats.anova_lm(model, typ=2)

print("Two-way ANOVA results:")
print(anova_table)
print(f"GPT     mean: {distance_data[distance_data['answerer'] == 'oai'      ]['normalized_distance'].mean()}")
print(f"Claude  mean: {distance_data[distance_data['answerer'] == 'anthropic']['normalized_distance'].mean()}")
print(f"Mistral mean: {distance_data[distance_data['answerer'] == 'mistral'  ]['normalized_distance'].mean()}")

def calculate_eta_squared(anova_table):
    eta_squared = {}
    ss_total = anova_table['sum_sq'].sum()
    for index, row in anova_table.iterrows():
        if index != 'Residual':
            eta_squared[index] = row['sum_sq'] / ss_total
    return eta_squared

eta_squared = calculate_eta_squared(anova_table)

def cohens_f_squared(eta_squared):
    return eta_squared / (1 - eta_squared)

def estimate_sample_size(effect_size, power=0.8, alpha=0.05, num_groups=3):
    ftester = FTestAnovaPower()
    sample_size = ftester.solve_power(
        effect_size=np.sqrt(cohens_f_squared(effect_size)),
        power=power,
        alpha=alpha,
        k_groups=num_groups
    )
    return int(np.ceil(sample_size))

power = 0.8  # Conventional power level
alpha = 0.05  # Conventional significance level

for effect, eta_sq in eta_squared.items():
    sample_size = estimate_sample_size(eta_sq, power, alpha)
    print(f"Estimated sample size for {effect}: {sample_size} f2: {cohens_f_squared(eta_sq)}")

import scikit_posthocs as sp

print("\nPost-hoc Tukey HSD test for answerer models:")
posthoc = sp.posthoc_tukey(distance_data, val_col='normalized_distance', group_col='answerer')
print(posthoc)

print("\nPost-hoc Tukey HSD test for rater (embedding) models:")
posthoc_rater = sp.posthoc_tukey(distance_data, val_col='normalized_distance', group_col='rater')
print(posthoc_rater)

