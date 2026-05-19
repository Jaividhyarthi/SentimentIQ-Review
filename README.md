# SentimentIQ — Review Sentiment Analyzer

A full-stack AI-powered web application that analyzes customer reviews and returns sentiment breakdown, detected themes, top keywords, and per-review scores. Built with Python (Flask + VADER) and a clean editorial frontend.

---

## Features

- Paste any number of reviews — one per line
- Overall sentiment score (0–100) with Positive / Neutral / Negative label
- Breakdown bar chart showing distribution
- Auto-detected themes (Quality, Delivery, Price, Service, etc.)
- Top keywords extracted from the reviews
- Per-review sentiment with individual scores
- Full analytics dashboard with history at `/history`
- SQLite database — every analysis saved automatically
- 3 built-in sample datasets (E-commerce, Restaurant, Mobile App)

---

## Project Structure

```
sentiment-analyzer/
├── app.py                  — Flask backend + analysis API
├── requirements.txt        — Python dependencies
├── analyses.db             — SQLite database (auto-created)
├── templates/
│   ├── index.html          — Main analyzer UI
│   └── history.html        — Analytics dashboard
├── static/
│   ├── css/styles.css      — All styling
│   └── js/app.js           — Frontend logic
└── README.md
```

---

## Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
python app.py
```

Open `http://localhost:5000`

---

## API Reference

### POST /analyze
**Request:**
```json
{
  "text": "Review 1\nReview 2\nReview 3",
  "source": "Amazon"
}
```

**Response:**
```json
{
  "total": 3,
  "positive": 2,
  "negative": 1,
  "neutral": 0,
  "overall": "Positive",
  "overall_score": 72.4,
  "themes": ["Quality", "Delivery"],
  "keywords": ["great", "fast", "broken"],
  "reviews": [...]
}
```

### GET /api/history — past analyses
### GET /api/stats — aggregate statistics
### DELETE /api/clear — wipe all data

---

## Tech Stack

- **Backend:** Python, Flask, VADER Sentiment
- **Database:** SQLite
- **Frontend:** Vanilla HTML, CSS, JavaScript
- **Fonts:** Bricolage Grotesque + Instrument Sans

---

Built by Jaividhyarthi Vivekanand
