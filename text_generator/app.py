import os
import json
import random
import re
from collections import defaultdict, Counter
from flask import Flask, render_template, request, jsonify
from groq import Groq

app = Flask(__name__)

# ── Groq client ──────────────────────────────────────────────────────────────
client = Groq(api_key="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")

# ── Paths ─────────────────────────────────────────────────────────────────────
CUSTOM_DICT_PATH = os.path.join("data", "custom_dict.json")
CORPUS_PATH      = os.path.join("data", "corpus.txt")

# ── Load / save custom dictionary ─────────────────────────────────────────────
def load_custom_dict():
    if os.path.exists(CUSTOM_DICT_PATH):
        with open(CUSTOM_DICT_PATH) as f:
            return json.load(f)
    return {"words": [], "phrases": []}

def save_custom_dict(d):
    with open(CUSTOM_DICT_PATH, "w") as f:
        json.dump(d, f, indent=2)

# ── Default corpus ─────────────────────────────────────────────────────────────
DEFAULT_CORPUS = """
The quick brown fox jumps over the lazy dog.
I love programming and building intelligent systems.
Machine learning is a fascinating field of study.
Natural language processing helps computers understand human language.
Python is a versatile language used in many domains.
Artificial intelligence is transforming technology and society.
Deep learning models require large amounts of training data.
The weather today is beautiful and sunny outside.
I would like to go to the restaurant for dinner tonight.
Thank you for your help and support with the project.
How are you doing today? I hope everything is going well.
The quick fox runs through the dark forest.
Let me know if you have any questions or concerns.
This is a great opportunity to learn something new.
I am working on a very interesting project right now.
The application is running smoothly on the server.
Data science combines statistics mathematics and computer science.
The model was trained on a large dataset of text.
We need to improve the accuracy of our predictions.
Good morning! How can I help you today?
"""

def load_corpus():
    if os.path.exists(CORPUS_PATH):
        with open(CORPUS_PATH) as f:
            return f.read()
    return DEFAULT_CORPUS

# ── N-gram model ───────────────────────────────────────────────────────────────
class NGramModel:
    def __init__(self, n=3):
        self.n = n
        self.ngrams: dict[tuple, Counter] = defaultdict(Counter)
        self.bigrams: dict[tuple, Counter] = defaultdict(Counter)
        self.unigrams: Counter = Counter()

    def tokenize(self, text: str) -> list[str]:
        return re.findall(r"\b[a-zA-Z']+\b", text.lower())

    def train(self, text: str):
        tokens = self.tokenize(text)
        self.unigrams.update(tokens)
        for i in range(len(tokens) - 1):
            self.bigrams[(tokens[i],)][tokens[i + 1]] += 1
        for i in range(len(tokens) - self.n + 1):
            ctx = tuple(tokens[i:i + self.n - 1])
            nxt = tokens[i + self.n - 1]
            self.ngrams[ctx][nxt] += 1

    def predict(self, context: list[str], top_k: int = 5) -> list[tuple[str, float]]:
        context = [w.lower() for w in context]
        # Try n-gram first
        if len(context) >= self.n - 1:
            ctx = tuple(context[-(self.n - 1):])
            if ctx in self.ngrams:
                return self._top(self.ngrams[ctx], top_k)
        # Fall back to bigram
        if context:
            ctx1 = (context[-1],)
            if ctx1 in self.bigrams:
                return self._top(self.bigrams[ctx1], top_k)
        # Fall back to unigram
        return self._top(self.unigrams, top_k)

    @staticmethod
    def _top(counter: Counter, k: int) -> list[tuple[str, float]]:
        total = sum(counter.values())
        return [(w, round(c / total, 3)) for w, c in counter.most_common(k)]

# ── Markov Chain model ─────────────────────────────────────────────────────────
class MarkovChain:
    def __init__(self):
        self.chain: dict[str, list[str]] = defaultdict(list)

    def train(self, text: str):
        tokens = re.findall(r"\b[a-zA-Z']+\b", text.lower())
        for i in range(len(tokens) - 1):
            self.chain[tokens[i]].append(tokens[i + 1])

    def predict(self, word: str, top_k: int = 5) -> list[tuple[str, float]]:
        word = word.lower()
        if word not in self.chain:
            return []
        freq = Counter(self.chain[word])
        total = sum(freq.values())
        return [(w, round(c / total, 3)) for w, c in freq.most_common(top_k)]

# ── Build models ───────────────────────────────────────────────────────────────
corpus       = load_corpus()
ngram_model  = NGramModel(n=3)
markov_model = MarkovChain()
ngram_model.train(corpus)
markov_model.train(corpus)

def retrain():
    global corpus, ngram_model, markov_model
    corpus = load_corpus()
    custom = load_custom_dict()
    extra  = " ".join(custom["words"] + custom["phrases"])
    full   = corpus + " " + extra
    ngram_model  = NGramModel(n=3)
    markov_model = MarkovChain()
    ngram_model.train(full)
    markov_model.train(full)

# ── Merge & deduplicate predictions ───────────────────────────────────────────
def merge_predictions(ngram_preds, markov_preds, top_k=5):
    scores: dict[str, float] = {}
    for w, s in ngram_preds:
        scores[w] = scores.get(w, 0) + s * 0.6
    for w, s in markov_preds:
        scores[w] = scores.get(w, 0) + s * 0.4
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [(w, round(s, 3)) for w, s in ranked[:top_k]]

# ── Groq AI prediction ─────────────────────────────────────────────────────────
def groq_predict(text: str) -> list[str]:
    if not os.environ.get("GROQ_API_KEY"):
        return []
    try:
        prompt = (
            f'Given the partial sentence: "{text}"\n'
            "Suggest the 5 most likely next words that would naturally follow. "
            "Return ONLY a JSON array of strings, no explanation. Example: [\"word1\",\"word2\",\"word3\",\"word4\",\"word5\"]"
        )
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.3,
        )
        raw = response.choices[0].message.content.strip()
        # Extract JSON array
        match = re.search(r'\[.*?\]', raw, re.DOTALL)
        if match:
            words = json.loads(match.group())
            return [str(w).lower() for w in words if isinstance(w, str)][:5]
    except Exception as e:
        print(f"Groq error: {e}")
    return []

# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    data    = request.get_json()
    text    = data.get("text", "").strip()
    mode    = data.get("mode", "hybrid")   # local | groq | hybrid

    if not text:
        return jsonify({"predictions": [], "source": "none"})

    tokens = re.findall(r"\b[a-zA-Z']+\b", text.lower())

    ngram_preds  = ngram_model.predict(tokens, top_k=5)
    markov_preds = markov_model.predict(tokens[-1], top_k=5) if tokens else []
    local_preds  = merge_predictions(ngram_preds, markov_preds, top_k=5)

    if mode == "local":
        return jsonify({"predictions": local_preds, "source": "local"})

    groq_words = groq_predict(text)

    if mode == "groq":
        groq_preds = [(w, 1.0) for w in groq_words]
        return jsonify({"predictions": groq_preds, "source": "groq"})

    # Hybrid: merge groq + local
    groq_scored = [(w, 0.9 - i * 0.05) for i, w in enumerate(groq_words)]
    merged = merge_predictions(local_preds, groq_scored, top_k=6)
    return jsonify({"predictions": merged, "source": "hybrid"})

@app.route("/generate", methods=["POST"])
def generate():
    """Generate a full sentence continuation using Groq."""
    data   = request.get_json()
    text   = data.get("text", "").strip()
    length = int(data.get("length", 10))

    if not text:
        return jsonify({"continuation": ""})

    if os.environ.get("GROQ_API_KEY"):
        try:
            prompt = (
                f'Continue this sentence naturally: "{text}"\n'
                f"Add approximately {length} more words. Return ONLY the continuation words, no quotes."
            )
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=60,
                temperature=0.7,
            )
            cont = response.choices[0].message.content.strip().strip('"').strip("'")
            return jsonify({"continuation": cont, "source": "groq"})
        except Exception as e:
            print(f"Groq generate error: {e}")

    # Fallback: Markov chain walk
    tokens = re.findall(r"\b[a-zA-Z']+\b", text.lower())
    if not tokens:
        return jsonify({"continuation": ""})
    word = tokens[-1]
    result = []
    for _ in range(length):
        nexts = markov_model.chain.get(word, [])
        if not nexts:
            break
        word = random.choice(nexts)
        result.append(word)
    return jsonify({"continuation": " ".join(result), "source": "local"})

@app.route("/custom_dict", methods=["GET"])
def get_custom_dict():
    return jsonify(load_custom_dict())

@app.route("/custom_dict", methods=["POST"])
def update_custom_dict():
    data  = request.get_json()
    word  = data.get("word", "").strip()
    ptype = data.get("type", "word")   # "word" or "phrase"
    if not word:
        return jsonify({"success": False, "error": "Empty input"})
    d = load_custom_dict()
    key = "phrases" if ptype == "phrase" else "words"
    if word.lower() not in [x.lower() for x in d[key]]:
        d[key].append(word)
        save_custom_dict(d)
        retrain()
    return jsonify({"success": True, "dict": d})

@app.route("/custom_dict/delete", methods=["POST"])
def delete_custom_entry():
    data  = request.get_json()
    word  = data.get("word", "").strip()
    ptype = data.get("type", "word")
    d = load_custom_dict()
    key = "phrases" if ptype == "phrase" else "words"
    d[key] = [x for x in d[key] if x.lower() != word.lower()]
    save_custom_dict(d)
    retrain()
    return jsonify({"success": True, "dict": d})

@app.route("/train", methods=["POST"])
def train_on_text():
    """Add new text to the corpus and retrain."""
    data = request.get_json()
    new_text = data.get("text", "").strip()
    if not new_text:
        return jsonify({"success": False})
    with open(CORPUS_PATH, "a") as f:
        f.write("\n" + new_text)
    retrain()
    return jsonify({"success": True})

@app.route("/stats")
def stats():
    return jsonify({
        "unigram_vocab":  len(ngram_model.unigrams),
        "bigram_contexts": len(ngram_model.bigrams),
        "ngram_contexts":  len(ngram_model.ngrams),
        "markov_states":   len(markov_model.chain),
        "custom_words":    len(load_custom_dict()["words"]),
        "custom_phrases":  len(load_custom_dict()["phrases"]),
    })

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    app.run(debug=True, port=5000)
