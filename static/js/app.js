// =====================
// SentimentIQ — app.js
// =====================

const SAMPLES = {
  ecommerce: `The product quality is absolutely amazing, exceeded my expectations!
Delivery was super fast and packaging was perfect.
Terrible experience, the item arrived broken and customer support was useless.
Decent product for the price, does what it says.
Love this! Already ordered a second one for my friend.
The color is slightly different from the photo but overall okay.
Worst purchase ever. Stopped working after 2 days.
Great value for money, highly recommend to everyone.
Average product, nothing special but gets the job done.
Five stars! Beautiful design and works perfectly.`,

  restaurant: `Best biryani I've had in Chennai, absolutely delicious!
Service was slow and the food was cold when it arrived.
Decent place, nothing extraordinary but clean and affordable.
Loved the ambiance, very cozy and the staff were super friendly.
The portion sizes are too small for the price they charge.
Amazing experience overall, will definitely come back.
Food was mediocre, not worth the wait or the money.
Great for a family dinner, kids loved the menu options.
The new menu items are fantastic, especially the pasta.
Disappointing visit today, food quality has gone down.`,

  app: `This app has completely changed how I manage my schedule!
Too many ads and the premium plan is overpriced.
Works fine but the UI could be more intuitive.
Crashes every time I try to upload a photo. Very frustrating.
Love the new update, so much smoother and faster now.
Battery drain is insane. Uninstalling after one week.
Simple and effective. Does exactly what I need.
Best productivity app I've used. Worth every rupee.
Average rating - some features are good, others not so much.
Customer support responded within hours and solved my issue!`
};

// Live review counter
document.getElementById('reviewInput').addEventListener('input', updateCount);

function updateCount() {
  const text = document.getElementById('reviewInput').value.trim();
  if (!text) {
    document.getElementById('reviewCount').textContent = '0 reviews detected';
    return;
  }
  const lines = text.split('\n').filter(l => l.trim().length > 5);
  const count = lines.length;
  document.getElementById('reviewCount').textContent = `${count} review${count !== 1 ? 's' : ''} detected`;
}

function loadSample(type) {
  document.getElementById('reviewInput').value = SAMPLES[type];
  updateCount();
}

function clearInput() {
  document.getElementById('reviewInput').value = '';
  document.getElementById('sourceInput').value = '';
  updateCount();
}

async function runAnalysis() {
  const text = document.getElementById('reviewInput').value.trim();
  const source = document.getElementById('sourceInput').value.trim();

  if (!text) {
    document.getElementById('reviewInput').focus();
    return;
  }

  const btn = document.getElementById('analyzeBtn');
  const btnText = btn.querySelector('.btn-text');
  const btnLoading = btn.querySelector('.btn-loading');

  btn.disabled = true;
  btnText.style.display = 'none';
  btnLoading.style.display = 'flex';

  try {
    const response = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, source })
    });

    const data = await response.json();

    if (data.error) {
      alert('Error: ' + data.error);
      return;
    }

    renderResults(data);

  } catch (err) {
    alert('Could not connect to server. Make sure Flask is running on port 5000.');
  } finally {
    btn.disabled = false;
    btnText.style.display = 'inline';
    btnLoading.style.display = 'none';
  }
}

function renderResults(data) {
  document.getElementById('emptyState').style.display = 'none';
  const content = document.getElementById('resultsContent');
  content.style.display = 'flex';

  // Score card
  const scoreEl = document.getElementById('overallScore');
  animateNumber(scoreEl, 0, data.overall_score, 800);

  const badge = document.getElementById('overallBadge');
  badge.textContent = data.overall;
  badge.className = 'overall-badge ' + data.overall;

  document.getElementById('scoreMeta').textContent = `Based on ${data.total} review${data.total !== 1 ? 's' : ''}`;

  // Color the score value
  const scoreColors = { Positive: '#1a7a4a', Neutral: '#7a6a1a', Negative: '#7a1a1a' };
  document.getElementById('overallScore').style.color = scoreColors[data.overall];

  // Breakdown bars
  const total = data.total || 1;
  setTimeout(() => {
    document.getElementById('positiveFill').style.width = (data.positive / total * 100) + '%';
    document.getElementById('neutralFill').style.width  = (data.neutral  / total * 100) + '%';
    document.getElementById('negativeFill').style.width = (data.negative / total * 100) + '%';
  }, 100);

  document.getElementById('positiveCount').textContent = data.positive;
  document.getElementById('neutralCount').textContent  = data.neutral;
  document.getElementById('negativeCount').textContent = data.negative;

  // Themes
  const themesCard = document.getElementById('themesCard');
  const themesList = document.getElementById('themesList');
  if (data.themes && data.themes.length > 0) {
    themesList.innerHTML = data.themes.map(t => `<span class="theme-tag">${t}</span>`).join('');
    themesCard.style.display = 'block';
  } else {
    themesCard.style.display = 'none';
  }

  // Keywords
  const keywordsCard = document.getElementById('keywordsCard');
  const keywordsList = document.getElementById('keywordsList');
  if (data.keywords && data.keywords.length > 0) {
    keywordsList.innerHTML = data.keywords.map(k => `<span class="keyword-tag">${k}</span>`).join('');
    keywordsCard.style.display = 'block';
  } else {
    keywordsCard.style.display = 'none';
  }

  // Individual reviews
  const reviewsList = document.getElementById('reviewsList');
  reviewsList.innerHTML = data.reviews.map(r => `
    <div class="review-item ${r.sentiment}">
      <div class="review-text">${escapeHtml(r.text)}</div>
      <div class="review-meta">
        <span class="review-sentiment">${r.sentiment}</span>
        <span class="review-score">Score: ${r.display_score}/100</span>
      </div>
    </div>
  `).join('');

  // Scroll to results on mobile
  if (window.innerWidth < 900) {
    content.scrollIntoView({ behavior: 'smooth' });
  }
}

function animateNumber(el, from, to, duration) {
  const start = performance.now();
  const update = (time) => {
    const elapsed = time - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(from + (to - from) * eased);
    if (progress < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
