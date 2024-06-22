#import "@preview/slydst:0.1.1": *

#show: slides.with(
  title: "Evaluating LLM performance on question-answering based on Wikidata triples",
  authors: ("Aksel Mads Madsen"),
)

== Introduction

- Questions answering
- Dataset contamination
- Answer rating difficulties
    - Quantify answer quality

== Wikidata & question generation

- Large graph database
- Diverse Subjects
- Example of triple: `(Public Parks (Ireland) Act 1869 | legislated by | Parliament of the United Kingdom)`
- Filtering
- Question generating: 10-shot claude

== Evaluation & Embeddings

- Language Models
    - GPT4-o
    - Claude 3 Sonnet
    - Mistral Large
- Embeddings
    - Semantic Similarity
    - Distances
- Bias potential
    -  Multiple Embedding suppliers
- Rank Normalization

== Analysis & Results

- Means of normalized distance
    - #(table(
    columns: (auto, auto),
    [GPT], $-0.101$,
    [Claude], $0.004$,
    [Mistral], $0.105$,
))
- ANOVA Results
    - #(table(
        columns: (auto, auto, auto),
        table.header(
            [Term], [P-value], [Effect size ($F^2$)]
        ),
    [Model],                      [$6.6 dot 10^(-5)$], [$7 dot 10^(-3)$],
    [Model-Rater Interaction], [$0.44$],            [$5 dot 10^(-4)$],
    ))

== Results box-plot (In standard deviations)

#image("box.png")

== Pos-hoc analysis
- Pos-hoc matrix
    - Tukey Post-Hoc test (in p-values): #table(
        columns: (auto, auto, auto, auto),
        [], [GPT4-o], [Claude 3 Sonnet], [Mistral Large],
        [GPT4-o], $1$, $0.095$, $0.001$,
        [Claude 3 Sonnet], [], $1$, $0.05$,
        [Mistral Large], [], [], $1$
    )

// == Correlation with BLEU
//
// #image("bleu_distance_correlation.png", height: 80%)
// - $R^2 = 0.4$

// == Conclusion & Discussion
//
// - Differences in model performance
//     - Small effect sizes
// - No significant differences interaction with embedding model
// - Comparison with BLEU
// - No significant differences
//     - Mistral-Claude
//     - Claude-GPT

== Limitations

- Small Effect size
- Poor dataset
- Embeddings distance difficult to interpret
    - Distance between embeddings between topic vary
