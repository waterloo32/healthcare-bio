// 정적 배포판: 서버 API 대신 data/articles.json을 한 번 불러와 브라우저에서 필터링한다.

const CATEGORIES = [
  { key: "marketing_branding", label: "마케팅/브랜딩", priority: true },
  { key: "new_business_strategy", label: "신사업/전략", priority: true },
  { key: "service_launch", label: "서비스 출시/업데이트", priority: true },
  { key: "rnd_clinical", label: "R&D/임상 연구", priority: false },
  { key: "investment_ma", label: "투자/M&A", priority: false },
  { key: "regulatory_policy", label: "규제/정책", priority: false },
  { key: "other", label: "기타", priority: false },
];

const SOURCES = [
  { key: "fierce_biotech", name: "Fierce Biotech" },
  { key: "fierce_pharma", name: "Fierce Pharma" },
  { key: "endpoints_news", name: "Endpoints News" },
  { key: "stat_news", name: "STAT News" },
  { key: "medcity_news", name: "MedCity News" },
];

const state = {
  category: "",
  source: "",
  q: "",
  date_from: "",
  date_to: "",
  page: 1,
  page_size: 20,
};

let allArticles = [];

const els = {
  chips: document.getElementById("category-chips"),
  search: document.getElementById("search-input"),
  sourceSelect: document.getElementById("source-select"),
  dateFrom: document.getElementById("date-from"),
  dateTo: document.getElementById("date-to"),
  resetBtn: document.getElementById("reset-btn"),
  statusBar: document.getElementById("status-bar"),
  list: document.getElementById("article-list"),
  prevPage: document.getElementById("prev-page"),
  nextPage: document.getElementById("next-page"),
  pageInfo: document.getElementById("page-info"),
};

function debounce(fn, delay) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

function renderCategoryChips() {
  els.chips.appendChild(makeChip("", "전체", false));
  CATEGORIES.forEach((c) => els.chips.appendChild(makeChip(c.key, c.label, c.priority)));
}

function makeChip(key, label, priority) {
  const chip = document.createElement("button");
  chip.className = "chip" + (priority ? " priority" : "") + (key === "" ? " active" : "");
  chip.textContent = label;
  chip.dataset.key = key;
  chip.addEventListener("click", () => {
    state.category = key;
    state.page = 1;
    [...els.chips.children].forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    render();
  });
  return chip;
}

function renderSourceOptions() {
  SOURCES.forEach((s) => {
    const opt = document.createElement("option");
    opt.value = s.key;
    opt.textContent = s.name;
    els.sourceSelect.appendChild(opt);
  });
}

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("ko-KR", { year: "numeric", month: "2-digit", day: "2-digit" });
}

function applyFilters() {
  const q = state.q.toLowerCase();
  return allArticles.filter((a) => {
    if (state.category) {
      const matches =
        a.primary_category === state.category ||
        (a.secondary_categories || []).includes(state.category);
      if (!matches) return false;
    }
    if (state.source && a.source_key !== state.source) return false;
    if (q) {
      const haystack = `${a.title} ${a.summary || ""}`.toLowerCase();
      if (!haystack.includes(q)) return false;
    }
    const dateStr = (a.published_at || a.collected_at || "").slice(0, 10);
    if (state.date_from && dateStr && dateStr < state.date_from) return false;
    if (state.date_to && dateStr && dateStr > state.date_to) return false;
    return true;
  });
}

function renderArticles(items, total) {
  els.list.innerHTML = "";
  if (items.length === 0) {
    els.list.innerHTML = '<div class="empty-state">조건에 맞는 뉴스가 없습니다.</div>';
  }

  items.forEach((a) => {
    const card = document.createElement("article");
    card.className = "card";

    const tags = [
      `<span class="tag primary">${a.primary_category_label}</span>`,
      ...(a.secondary_category_labels || []).map((l) => `<span class="tag">${l}</span>`),
    ].join("");

    const summaryClass = a.summary_failed ? "card-summary failed" : "card-summary";
    const summaryText = a.summary || "요약 생성 실패 — 원문을 확인해주세요.";

    card.innerHTML = `
      <div class="card-meta">
        <span>${a.source_name}</span>
        <span>${formatDate(a.published_at || a.collected_at)}</span>
      </div>
      <h3 class="card-title"><a href="${a.source_url}" target="_blank" rel="noopener noreferrer">${a.title}</a></h3>
      <div class="card-tags">${tags}</div>
      <p class="${summaryClass}">${summaryText}</p>
      <a class="card-link" href="${a.source_url}" target="_blank" rel="noopener noreferrer">원문 보기 →</a>
    `;
    els.list.appendChild(card);
  });

  const totalPages = Math.max(1, Math.ceil(total / state.page_size));
  els.pageInfo.textContent = `${state.page} / ${totalPages} 페이지 · 총 ${total}건`;
  els.prevPage.disabled = state.page <= 1;
  els.nextPage.disabled = state.page >= totalPages;
  els.statusBar.textContent = `${total}건의 뉴스`;
}

function render() {
  const filtered = applyFilters();
  const start = (state.page - 1) * state.page_size;
  const pageItems = filtered.slice(start, start + state.page_size);
  renderArticles(pageItems, filtered.length);
}

els.search.addEventListener(
  "input",
  debounce((e) => {
    state.q = e.target.value.trim();
    state.page = 1;
    render();
  }, 300)
);

els.sourceSelect.addEventListener("change", (e) => {
  state.source = e.target.value;
  state.page = 1;
  render();
});

els.dateFrom.addEventListener("change", (e) => {
  state.date_from = e.target.value;
  state.page = 1;
  render();
});

els.dateTo.addEventListener("change", (e) => {
  state.date_to = e.target.value;
  state.page = 1;
  render();
});

els.resetBtn.addEventListener("click", () => {
  state.category = "";
  state.source = "";
  state.q = "";
  state.date_from = "";
  state.date_to = "";
  state.page = 1;
  els.search.value = "";
  els.sourceSelect.value = "";
  els.dateFrom.value = "";
  els.dateTo.value = "";
  [...els.chips.children].forEach((c) => c.classList.remove("active"));
  els.chips.children[0].classList.add("active");
  render();
});

els.prevPage.addEventListener("click", () => {
  if (state.page > 1) {
    state.page -= 1;
    render();
  }
});

els.nextPage.addEventListener("click", () => {
  state.page += 1;
  render();
});

async function loadMeta() {
  try {
    const res = await fetch("data/meta.json", { cache: "no-store" });
    const meta = await res.json();
    const el = document.getElementById("last-updated");
    if (el && meta.generated_at) {
      const d = new Date(meta.generated_at);
      el.textContent = `마지막 업데이트: ${d.toLocaleString("ko-KR")}`;
    }
  } catch (err) {
    console.error(err);
  }
}

(async function init() {
  renderCategoryChips();
  renderSourceOptions();
  els.statusBar.textContent = "불러오는 중...";
  loadMeta();
  try {
    const res = await fetch("data/articles.json", { cache: "no-store" });
    allArticles = await res.json();
    render();
  } catch (err) {
    els.statusBar.textContent = "뉴스를 불러오지 못했습니다.";
    console.error(err);
  }
})();
