# Layer 2 Fuzzy Matching Frameworks — Technical Explainer

This document provides a detailed breakdown of the three alternative algorithms implemented for **Layer 2 Fuzzy matching** in the CV Manager Normalization Pipeline.

---

## 1. Edit Distance Engine (RapidFuzz / Levenshtein)
**Implementation File:** `poc/normalizer_rapidfuzz.py`

### How It Works
This engine uses **Levenshtein Distance**, which measures the minimum number of single-character edits (insertions, deletions, or substitutions) required to change one word into another. 
Instead of a simple ratio, it utilizes `fuzz.token_set_ratio` which:
1. Normalizes the strings.
2. Tokenizes them into individual words.
3. Separates common words (intersection) and calculates similarity based on overlapping tokens, ignoring differences in word order and duplicate words.

### Technical Assessment
*   **Best Used For**: Catching typing mistakes (e.g., `"Btehc"` instead of `"BTech"`) and handling simple word reorderings (e.g., `"Science Bachelor of"`).
*   **Pros**: Highly optimized in C; extremely fast runtime (~1–3ms per query); doesn't require machine learning libraries.
*   **Cons**: Completely blind to semantics (e.g., it has no idea that `"B.S."` means `"Bachelor of Science"`).

---

## 2. Character N-Gram TF-IDF Cosine Similarity Engine
**Implementation File:** `poc/normalizer_tfidf.py`

### How It Works
This engine converts strings into sparse mathematical vectors using **Term Frequency-Inverse Document Frequency (TF-IDF)** on **Character N-Grams** (sub-words ranging from 3 to 5 characters):
1. **N-Grams**: A word like `"BTech"` is broken down into `["BTe", "Tec", "ech", "BTec", "Tech"]`.
2. **TF-IDF**: Assigns statistical weights to these sub-words (rare sub-words get higher importance weights).
3. **Cosine Similarity**: Measures the angular cosine distance between the input string's vector and the reference choices vector.

### Technical Assessment
*   **Best Used For**: Highly scalable searches across large dictionary lists where speed is the primary metric.
*   **Pros**: Sub-millisecond matching latency; excellent typo tolerance because spelling errors only change a fraction of the sub-word n-grams.
*   **Cons**: Tuning the threshold (`0.0` to `1.0`) is highly sensitive; fails on conceptual synonyms with completely different spelling layouts.

---

## 3. Semantic Vector Embeddings Engine (Sentence-Transformers)
**Implementation File:** `poc/normalizer_embeddings.py`

### How It Works
This engine employs the **`all-MiniLM-L6-v2`** Sentence-Transformer model (a lightweight BERT-based neural network model):
1. **Dense Vector Space**: Passes the input text through the neural network to produce a dense 384-dimensional floating-point vector representing its *semantic meaning*.
2. **Dot Product Match**: Calculates the dot product of the input vector against a pre-computed index of canonical degree alias vectors.

### Technical Assessment
*   **Best Used For**: Resolving conceptual abbreviations, synonyms, or industry-specific naming variations (e.g., mapping `"B.S."`, `"B.Sc."`, and `"Bachelor of Science"` to the same target).
*   **Pros**: Resolves relationships purely based on linguistic meaning rather than character sequence.
*   **Cons**: Slower execution speed (~50–100ms per string on CPU); high system footprint (requires PyTorch, Hugging Face, and downloading a ~90MB weights model).

---

## Strategic Comparison

| Feature | RapidFuzz (Levenshtein) | TF-IDF (Char N-Gram) | Sentence-Transformers (Embeddings) |
|---|---|---|---|
| **Mechanism** | String token overlaps | Sub-string vector overlaps | Neural network semantic vectors |
| **Speed** | Fast (~1-5ms) | Extremely Fast (<1ms) | Slow (~50-100ms) |
| **Synonym Matching** | Poor | Poor | Excellent |
| **Typo Resilience** | High | High | Moderate |
| **Infrastructure** | Light (Pure C extension) | Light (scikit-learn) | Heavy (PyTorch + SentenceTransformers) |
