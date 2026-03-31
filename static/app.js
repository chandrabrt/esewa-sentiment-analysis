// ── Utility Helpers ──────────────────────────────────────
const $ = (s, ctx = document) => ctx.querySelector(s);
const $$ = (s, ctx = document) => [...ctx.querySelectorAll(s)];

function showToast(message, type = "success") {
  const container = document.getElementById("toast-container") || (() => {
    const c = document.createElement("div");
    c.id = "toast-container";
    c.className = "toast-container";
    document.body.appendChild(c);
    return c;
  })();
  const t = document.createElement("div");
  t.className = `toast${type === "error" ? " error" : ""}`;
  t.innerHTML = `<span>${type === "error" ? "⚠️" : "✅"}</span>${message}`;
  container.appendChild(t);
  setTimeout(() => t.remove(), 4000);
}

function formatDate(isoStr) {
  if (!isoStr) return "—";
  return new Date(isoStr).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

function starsHTML(rating) {
  const full = Math.round(rating);
  return Array.from({length: 5}, (_, i) => `<span>${i < full ? "★" : "☆"}</span>`).join("");
}

function sentimentTag(s) {
  const map = { positive: "✅", negative: "❌", neutral: "➖" };
  return `<span class="tag tag-${s}">${map[s] || ""} ${s}</span>`;
}

function platformBadge(platform) {
  const icon = platform === "playstore" ? "🤖" : "🍎";
  const label = platform === "playstore" ? "Play Store" : "App Store";
  return `<span class="platform-badge">${icon} ${label}</span>`;
}

function avatarLetter(name) {
  return (name || "?")[0].toUpperCase();
}

function avatarColor(name) {
  const colors = ["#2e6800","#3f6354","#5d5f00","#2563eb","#7c3aed","#b45309"];
  let h = 0; for (let c of (name || "")) h = c.charCodeAt(0) + ((h << 5) - h);
  return colors[Math.abs(h) % colors.length];
}

// ── Stats Loader ──────────────────────────────────────────
async function loadSummary(elMap) {
  try {
    const res = await fetch("/api/stats/summary");
    const d = await res.json();
    if (elMap.totalReviews) elMap.totalReviews.textContent = d.total_reviews.toLocaleString();
    if (elMap.avgRating) elMap.avgRating.textContent = `${d.avg_rating.toFixed(1)} ⭐`;
    if (elMap.positivePct) elMap.positivePct.textContent = `${d.sentiment_overall.positive_pct}%`;
    if (elMap.negativePct) elMap.negativePct.textContent = `${d.sentiment_overall.negative_pct}%`;
    if (elMap.posPlaystore) elMap.posPlaystore.textContent = `${d.sentiment_playstore.positive_pct}%`;
    if (elMap.posAppstore) elMap.posAppstore.textContent = `${d.sentiment_appstore.positive_pct}%`;
    if (elMap.avgPlaystore) elMap.avgPlaystore.textContent = `${d.avg_rating_playstore.toFixed(1)} ⭐`;
    if (elMap.avgAppstore) elMap.avgAppstore.textContent = `${d.avg_rating_appstore.toFixed(1)} ⭐`;
    return d;
  } catch(e) {
    console.error("Stats load failed", e);
  }
}

// ── Chart Builder (Chart.js) ─────────────────────────────
function buildDonutChart(canvasId, data, labels, colors) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  return new Chart(ctx, {
    type: "doughnut",
    data: { labels, datasets: [{ data, backgroundColor: colors, borderWidth: 0, hoverOffset: 4 }] },
    options: {
      cutout: "70%",
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: i => ` ${i.label}: ${i.raw}%` } } },
      animation: { duration: 800 },
    }
  });
}

async function buildTrendChart(canvasId) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  let rows = [];
  try {
    const r = await fetch("/api/stats/trends"); rows = await r.json();
  } catch(e) {}

  const labels = rows.map(r => r.month);
  const pos = rows.map(r => r.positive || 0);
  const neu = rows.map(r => r.neutral || 0);
  const neg = rows.map(r => r.negative || 0);

  return new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        { label: "Positive", data: pos, borderColor: "#60b527", backgroundColor: "rgba(96,181,39,0.08)", fill: true, tension: 0.4, pointRadius: 4, pointBackgroundColor: "#60b527" },
        { label: "Neutral",  data: neu, borderColor: "#94a3b8", backgroundColor: "rgba(148,163,184,0.06)", fill: true, tension: 0.4, pointRadius: 4, pointBackgroundColor: "#94a3b8" },
        { label: "Negative", data: neg, borderColor: "#f95630", backgroundColor: "rgba(249,86,48,0.06)", fill: true, tension: 0.4, pointRadius: 4, pointBackgroundColor: "#f95630" },
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: "top", labels: { boxWidth: 10, font: { family: "Manrope", size: 11 } } } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { family: "Manrope", size: 10 } } },
        y: { beginAtZero: true, grid: { color: "rgba(0,0,0,0.04)" }, ticks: { font: { family: "Manrope", size: 10 } } },
      },
      animation: { duration: 800 },
    }
  });
}

// ── Paginated Table ───────────────────────────────────────
class ReviewTable {
  constructor({ containerId, platform, page_size = 20 }) {
    this.container = document.getElementById(containerId);
    this.platform = platform;
    this.page_size = page_size;
    this.page = 1;
    this.total = 0;
    this.filters = {};
  }

  async load(filters = {}) {
    this.filters = filters;
    this.page = 1;
    await this._fetch();
  }

  async goPage(p) {
    this.page = p;
    await this._fetch();
  }

  async _fetch() {
    if (!this.container) return;
    const params = new URLSearchParams({
      page: this.page,
      page_size: this.page_size,
      ...this.filters,
    });
    Object.keys(params).forEach(k => params.get(k) === "" && params.delete(k));

    this.container.innerHTML = `<div class="empty-state"><div class="skeleton" style="height:200px"></div></div>`;
    try {
      const res = await fetch(`/api/reviews/${this.platform}?${params}`);
      const d = await res.json();
      this.total = d.total;
      this._render(d.items, d.total);
    } catch(e) {
      this.container.innerHTML = `<div class="empty-state"><div class="icon">⚠️</div><h3>Failed to load</h3><p>Check your connection.</p></div>`;
    }
  }

  _render(items, total) {
    if (!items.length) {
      this.container.innerHTML = `<div class="empty-state"><div class="icon">🔍</div><h3>No reviews found</h3><p>Try adjusting your filters or scrape new data.</p></div>`;
      return;
    }

    const rows = items.map(r => `
      <tr>
        <td><div class="user-cell">
          <div class="u-avatar" style="background:${avatarColor(r.user_name)}">${avatarLetter(r.user_name)}</div>
          <span class="u-name">${escHtml(r.user_name)}</span>
        </div></td>
        <td><div class="stars">${starsHTML(r.rating)}</div></td>
        <td><div class="review-text-cell" title="${escHtml(r.text)}">${escHtml(r.text)}</div></td>
        <td>${r.app_version || "—"}</td>
        <td>${formatDate(r.review_date)}</td>
        <td>${sentimentTag(r.sentiment)}</td>
        <td><button class="btn-view" onclick='openReviewModal(${JSON.stringify(r)})'>View</button></td>
      </tr>`).join("");

    const totalPages = Math.ceil(total / this.page_size);
    const pagesBtns = Array.from({length: Math.min(totalPages, 7)}, (_, i) => {
      const p = i + 1;
      return `<button class="page-btn${p === this.page ? " active" : ""}" onclick="window._tbl_${this.platform}.goPage(${p})">${p}</button>`;
    }).join("");

    this.container.innerHTML = `
      <div class="reviews-table-wrapper">
        <table class="reviews-table">
          <thead><tr>
            <th>User</th><th>Rating</th><th>Review</th><th>Version</th><th>Date</th><th>Sentiment</th><th></th>
          </tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
      <div class="pagination">
        <span>${total.toLocaleString()} reviews</span>
        <div class="pagination-controls">
          <button class="page-btn" onclick="window._tbl_${this.platform}.goPage(${this.page - 1})" ${this.page <= 1 ? "disabled" : ""}>‹</button>
          ${pagesBtns}
          <button class="page-btn" onclick="window._tbl_${this.platform}.goPage(${this.page + 1})" ${this.page >= totalPages ? "disabled" : ""}>›</button>
        </div>
      </div>`;

    window[`_tbl_${this.platform}`] = this;
  }
}

function escHtml(str) {
  return (str || "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

// ── WebSocket Live Feed ───────────────────────────────────
function initLiveFeed(feedId) {
  const feed = document.getElementById(feedId);
  if (!feed) return;

  const wsProto = location.protocol === "https:" ? "wss:" : "ws:";
  const ws = new WebSocket(`${wsProto}//${location.host}/ws/live-reviews`);

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === "new_review") {
      const r = msg.data;
      const item = document.createElement("div");
      item.className = "feed-item";
      item.innerHTML = `
        <div class="feed-item-header">
          <div class="feed-avatar" style="background:${avatarColor(r.user_name)}">${avatarLetter(r.user_name)}</div>
          <span class="feed-user">${escHtml(r.user_name)}</span>
          ${platformBadge(r.platform)}
          <span class="feed-date">${formatDate(r.review_date)}</span>
        </div>
        <div class="feed-text">${escHtml(r.text)}</div>
        <div class="feed-footer">
          <div class="stars">${starsHTML(r.rating)}</div>
          ${sentimentTag(r.sentiment)}
        </div>`;
      feed.prepend(item);
      // keep feed max 30 items
      while (feed.children.length > 30) feed.lastChild.remove();
    }
  };

  ws.onerror = () => console.warn("[WS] Connection error");
  return ws;
}

// ── Scrape Trigger ────────────────────────────────────────
async function triggerScrape(platform) {
  showToast(`Scraping ${platform === "playstore" ? "Play Store" : "App Store"} reviews...`);
  try {
    const res = await fetch(`/api/reviews/${platform}/scrape?count=100`, { method: "POST" });
    const d = await res.json();
    showToast(`✅ Done! ${d.new_records} new reviews added.`);
    return d;
  } catch(e) {
    showToast("Scrape failed. Please retry.", "error");
  }
}

// ── Review Details Modal ──────────────────────────────────
function openReviewModal(r) {
  // Remove existing modal if any
  const existing = document.getElementById("review-modal-overlay");
  if (existing) existing.remove();

  const scoreBar = r.sentiment_score != null
    ? `<div class="rdm-score-bar-track"><div class="rdm-score-bar-fill" style="width:${Math.round(r.sentiment_score * 100)}%"></div></div><span class="rdm-score-label">${(r.sentiment_score * 100).toFixed(1)}% confidence</span>`
    : `<span class="rdm-score-label">N/A</span>`;

  const thumbsHtml = r.thumbs_up != null
    ? `<span class="rdm-meta-val">👍 ${r.thumbs_up.toLocaleString()} helpful votes</span>`
    : `<span class="rdm-meta-val">—</span>`;

  const overlay = document.createElement("div");
  overlay.id = "review-modal-overlay";
  overlay.className = "rdm-overlay";
  overlay.innerHTML = `
    <div class="rdm-panel" role="dialog" aria-modal="true" aria-label="Review Details">
      <div class="rdm-header">
        <div class="rdm-user-block">
          <div class="rdm-avatar" style="background:${avatarColor(r.user_name)}">${avatarLetter(r.user_name)}</div>
          <div>
            <div class="rdm-username">${escHtml(r.user_name)}</div>
            <div class="rdm-date">${formatDate(r.review_date)}</div>
          </div>
        </div>
        <div class="rdm-header-right">
          ${sentimentTag(r.sentiment)}
          ${platformBadge(r.platform)}
          <button class="rdm-close" onclick="document.getElementById('review-modal-overlay').remove()" aria-label="Close">✕</button>
        </div>
      </div>

      <div class="rdm-stars"><div class="stars rdm-big-stars">${starsHTML(r.rating)}</div><span class="rdm-rating-num">${r.rating} / 5</span></div>

      <div class="rdm-section-label">Review</div>
      <div class="rdm-review-body">${escHtml(r.text)}</div>

      <div class="rdm-meta-grid">
        <div class="rdm-meta-item">
          <span class="rdm-meta-key">App Version</span>
          <span class="rdm-meta-val">${r.app_version || "—"}</span>
        </div>
        <div class="rdm-meta-item">
          <span class="rdm-meta-key">Helpful Votes</span>
          ${thumbsHtml}
        </div>
        <div class="rdm-meta-item">
          <span class="rdm-meta-key">Platform</span>
          <span class="rdm-meta-val">${r.platform === "playstore" ? "🤖 Google Play" : "🍎 App Store"}</span>
        </div>
        <div class="rdm-meta-item">
          <span class="rdm-meta-key">Review ID</span>
          <span class="rdm-meta-val rdm-mono">${escHtml(r.review_id || "—")}</span>
        </div>
      </div>

      <div class="rdm-section-label">Sentiment Confidence</div>
      <div class="rdm-score-row">${scoreBar}</div>
    </div>
  `;

  // Close on backdrop click
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });
  // Close on Escape
  const onKey = (e) => { if (e.key === "Escape") { overlay.remove(); document.removeEventListener("keydown", onKey); } };
  document.addEventListener("keydown", onKey);

  document.body.appendChild(overlay);
  // Trigger animation
  requestAnimationFrame(() => overlay.classList.add("rdm-visible"));
}
