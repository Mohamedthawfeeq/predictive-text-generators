# NEXTEXT — Predictive Text Generator

A full-featured Predictive Text Generator powered by **N-gram models**, **Markov Chains**, and **Groq's LLaMA3 LLM**. Built with Python (Flask) and a sleek dark terminal UI.

---

## Features

| Feature | Details |
|---|---|
| **Word Prediction** | Real-time next-word suggestions as you type |
| **Context Awareness** | 3-gram model uses previous 2 words for context |
| **Markov Chain** | Probabilistic word transitions for local predictions |
| **Groq AI Mode** | LLaMA3-8b via Groq API for intelligent suggestions |
| **Hybrid Mode** | Blends local models (60%) + Groq AI (40%) |
| **Generate Continuation** | Auto-completes full sentence continuations |
| **Custom Dictionary** | Add your own words and phrases; model retrains instantly |
| **Train on Your Text** | Paste any text to teach the model your writing style |
| **Probability Chart** | Visual bar chart of prediction confidence scores |
| **Tab to Accept** | Press Tab to instantly insert top prediction |

---

## Project Structure

```
predictive_text_generator/
├── app.py                  # Flask backend (N-gram, Markov, Groq API)
├── requirements.txt
├── .env.example
├── data/
│   ├── corpus.txt          # Auto-created; grows as you train
│   └── custom_dict.json    # Auto-created; stores your custom words
├── templates/
│   └── index.html          # Main UI template
└── static/
    ├── css/style.css       # Dark terminal aesthetic
    └── js/app.js           # Frontend logic
```

---

## Setup Instructions

### Step 1 — Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- A free Groq API key from [console.groq.com](https://console.groq.com)

---

### Step 2 — Get Your Groq API Key

1. Visit [https://console.groq.com](https://console.groq.com)
2. Sign up / log in
3. Go to **API Keys** → **Create API Key**
4. Copy the key (starts with `gsk_...`)

---

### Step 3 — Install & Run

**Windows:**
```bat
cd predictive_text_generator
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
set GROQ_API_KEY=gsk_your_key_here
python app.py
```

**Mac / Linux:**
```bash
cd predictive_text_generator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export GROQ_API_KEY=gsk_your_key_here
python app.py
```

Then open your browser at: **http://localhost:5000**

---

### Step 4 — (Optional) Use a .env file

Instead of setting the env var every time, create a `.env` file:

```
GROQ_API_KEY=gsk_your_key_here
```

Then install `python-dotenv` and add this to the top of `app.py`:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## How to Use

### Prediction Modes

| Mode | Description |
|---|---|
| **HYBRID** | Best of both worlds — local models + Groq AI merged |
| **LOCAL** | N-gram + Markov only — works offline |
| **GROQ AI** | Groq LLaMA3 only — most intelligent, requires API key |

### Keyboard Shortcuts

| Key | Action |
|---|---|
| `Tab` | Accept top prediction instantly |
| `Enter` (in dict input) | Add word to dictionary |

### Generate Continuation

Click **GENERATE CONTINUATION** to have the AI complete your sentence. Accept it with the **ACCEPT →** button to append it to your text.

### Custom Dictionary

1. Type a word or phrase in the right panel
2. Select **Word** or **Phrase** radio button
3. Click **+ ADD TO DICTIONARY**
4. The model retrains automatically — your word will now be suggested!

### Train on Your Text

Paste any text (emails, notes, essays, chat logs) into the **TRAIN MODEL** box and click **TRAIN ON THIS TEXT**. The system learns your vocabulary and style immediately.

---

## How the Models Work

### N-gram Model (3-gram)
- Builds a frequency table: given words A and B, what word C most often follows?
- Stored as `{(A, B): Counter({C: count, D: count, ...})}`
- Falls back to bigrams, then unigrams if no n-gram match found

### Markov Chain
- Simpler: given word A, what words most often follow?
- Used for sentence generation (random walk through the chain)

### Hybrid Scoring
- Local (N-gram + Markov) predictions are scored 0–1
- Groq AI predictions are ranked and scored 0.9 → 0.7
- Scores are merged with weights: **local × 0.6 + groq × 0.4**
- Top-5 unique results are shown

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/predict` | Get word predictions for input text |
| POST | `/generate` | Generate sentence continuation |
| GET | `/custom_dict` | Fetch custom dictionary |
| POST | `/custom_dict` | Add word/phrase |
| POST | `/custom_dict/delete` | Remove word/phrase |
| POST | `/train` | Add text to corpus and retrain |
| GET | `/stats` | Model statistics (vocab size, contexts) |

---

## Troubleshooting

**"No predictions showing"** → Check that Flask is running on port 5000

**"Groq predictions not working"** → Verify your GROQ_API_KEY is set correctly

**"ModuleNotFoundError"** → Ensure your virtual environment is activated and `pip install -r requirements.txt` ran successfully

**App runs but predictions seem poor** → Use the **TRAIN MODEL** feature to add domain-specific text

---

## License

MIT — free to use, modify, and distribute.
