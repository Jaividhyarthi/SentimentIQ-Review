"""
app.py — SentimentIQ Backend
Run: python app.py
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import sqlite3
import os
import re
from datetime import datetime
from collections import Counter

app = Flask(__name__)
CORS(app)

analyzer = SentimentIntensityAnalyzer()

# ---- Common theme keywords ----
THEMES = {
    'Quality':      ['quality', 'build', 'material', 'durable', 'sturdy', 'solid', 'cheap', 'flimsy', 'fragile', 'premium'],
    'Delivery':     ['delivery', 'shipping', 'arrived', 'fast', 'slow', 'late', 'quick', 'dispatch', 'courier', 'package'],
    'Price':        ['price', 'cost', 'expensive', 'cheap', 'affordable', 'value', 'worth', 'overpriced', 'money', 'budget'],
    'Service':      ['service', 'support', 'staff', 'helpful', 'rude', 'polite', 'response', 'team', 'customer', 'assist'],
    'Packaging':    ['packaging', 'packed', 'box', 'wrapped', 'damaged', 'broken', 'intact', 'sealed', 'condition'],
    'Performance':  ['performance', 'works', 'working', 'function', 'speed', 'powerful', 'efficient', 'battery', 'feature'],
    'Design':       ['design', 'look', 'appearance', 'color', 'style', 'beautiful', 'ugly', 'sleek', 'aesthetic', 'size'],
    'Food':         ['food', 'taste', 'flavor', 'delicious', 'fresh', 'stale', 'hot', 'cold', 'portion', 'menu'],
}

# ---- Database ----
DB_PATH = os.path.join(os.path.dirname(__file__), 'analyses.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            source      TEXT,
            total       INTEGER,
            positive    INTEGER,
            negative    INTEGER,
            neutral     INTEGER,
            avg_score   REAL,
            themes      TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER,
            text        TEXT,
            sentiment   TEXT,
            score       REAL,
            FOREIGN KEY (analysis_id) REFERENCES analyses(id)
        )
    ''')
    conn.commit()
    conn.close()

def save_analysis(source, results, themes):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    pos = sum(1 for r in results if r['sentiment'] == 'Positive')
    neg = sum(1 for r in results if r['sentiment'] == 'Negative')
    neu = sum(1 for r in results if r['sentiment'] == 'Neutral')
    avg = round(sum(r['score'] for r in results) / len(results), 3) if results else 0

    c.execute('''
        INSERT INTO analyses (timestamp, source, total, positive, negative, neutral, avg_score, themes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), source or 'Manual', len(results), pos, neg, neu, avg, ','.join(themes)))

    analysis_id = c.lastrowid

    for r in results:
        c.execute('INSERT INTO reviews (analysis_id, text, sentiment, score) VALUES (?, ?, ?, ?)',
                  (analysis_id, r['text'][:500], r['sentiment'], r['score']))

    conn.commit()
    conn.close()
    return analysis_id

def get_history(limit=20):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM analyses ORDER BY id DESC LIMIT ?', (limit,))
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows

def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*), SUM(total), SUM(positive), SUM(negative), SUM(neutral), AVG(avg_score) FROM analyses')
    row = c.fetchone()
    conn.close()
    return {
        'analyses': row[0] or 0,
        'total_reviews': row[1] or 0,
        'total_positive': row[2] or 0,
        'total_negative': row[3] or 0,
        'total_neutral': row[4] or 0,
        'avg_score': round((row[5] or 0) * 100, 1)
    }

init_db()

# ---- Analysis logic ----
def classify(compound):
    if compound >= 0.05:  return 'Positive'
    elif compound <= -0.05: return 'Negative'
    else: return 'Neutral'

def detect_themes(reviews_text):
    text_lower = reviews_text.lower()
    found = []
    for theme, keywords in THEMES.items():
        if any(kw in text_lower for kw in keywords):
            found.append(theme)
    return found

def extract_keywords(reviews_text, sentiment_label):
    words = re.findall(r'\b[a-zA-Z]{4,}\b', reviews_text.lower())
    stopwords = {'this', 'that', 'with', 'have', 'from', 'they', 'been', 'were',
                 'their', 'what', 'when', 'very', 'just', 'also', 'would', 'could',
                 'should', 'really', 'product', 'item', 'order', 'will', 'your',
                 'more', 'than', 'much', 'some', 'into', 'over', 'after', 'about'}
    filtered = [w for w in words if w not in stopwords and len(w) > 3]
    common = Counter(filtered).most_common(8)
    return [w for w, _ in common]

# ---- Routes ----
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history_page():
    return render_template('history.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        raw_text = data.get('text', '').strip()
        source = data.get('source', 'Manual').strip()

        if not raw_text:
            return jsonify({'error': 'No text provided'}), 400

        # Split into individual reviews by newline or numbered list
        lines = [l.strip() for l in re.split(r'\n+', raw_text) if l.strip()]
        # Remove numbering like "1." or "1)"
        lines = [re.sub(r'^\d+[\.\)]\s*', '', l) for l in lines if len(l) > 5]

        if not lines:
            return jsonify({'error': 'Could not parse any reviews'}), 400

        results = []
        for line in lines:
            scores = analyzer.polarity_scores(line)
            compound = scores['compound']
            sentiment = classify(compound)
            # Normalize score to 0-100
            normalized = round((compound + 1) / 2 * 100, 1)
            results.append({
                'text': line,
                'sentiment': sentiment,
                'score': compound,
                'display_score': normalized,
                'pos': round(scores['pos'] * 100, 1),
                'neg': round(scores['neg'] * 100, 1),
                'neu': round(scores['neu'] * 100, 1),
            })

        total = len(results)
        positive = sum(1 for r in results if r['sentiment'] == 'Positive')
        negative = sum(1 for r in results if r['sentiment'] == 'Negative')
        neutral  = sum(1 for r in results if r['sentiment'] == 'Neutral')
        avg_compound = sum(r['score'] for r in results) / total
        overall_score = round((avg_compound + 1) / 2 * 100, 1)

        # Overall sentiment label
        if avg_compound >= 0.05:   overall = 'Positive'
        elif avg_compound <= -0.05: overall = 'Negative'
        else: overall = 'Neutral'

        combined_text = ' '.join(r['text'] for r in results)
        themes = detect_themes(combined_text)
        keywords = extract_keywords(combined_text, overall)

        # Save
        save_analysis(source, results, themes)

        return jsonify({
            'total': total,
            'positive': positive,
            'negative': negative,
            'neutral': neutral,
            'overall': overall,
            'overall_score': overall_score,
            'themes': themes,
            'keywords': keywords,
            'reviews': results
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history')
def api_history():
    return jsonify(get_history())

@app.route('/api/stats')
def api_stats():
    return jsonify(get_stats())

@app.route('/api/clear', methods=['DELETE'])
def clear_all():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('DELETE FROM reviews')
    conn.execute('DELETE FROM analyses')
    conn.commit()
    conn.close()
    return jsonify({'status': 'cleared'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
