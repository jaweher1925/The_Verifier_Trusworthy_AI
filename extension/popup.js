const API = "http://localhost:8000";

const SEV_COLOR = {
  critical: "#ef4444",
  high:     "#f97316",
  medium:   "#eab308",
  low:      "#3b82f6"
};

// ── On load ───────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  checkServer();
  loadLiveMetrics();

  chrome.storage.local.get(["lastInput", "selectedText"], (data) => {
    if (data.selectedText) {
      document.getElementById("input").value = data.selectedText;
      chrome.storage.local.remove("selectedText");
    } else if (data.lastInput) {
      document.getElementById("input").value = data.lastInput;
    }
  });

  document.getElementById("verifyBtn").addEventListener("click", verify);
  document.getElementById("scanBtn").addEventListener("click",   scanSelected);
  document.getElementById("clearBtn").addEventListener("click",  clearAll);

  document.getElementById("input").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && e.ctrlKey) verify();
  });
});

// ── Server status ─────────────────────────────────────────────────────────────
async function checkServer() {
  const dot = document.getElementById("dot");
  try {
    const r = await fetch(`${API}/health`, { signal: AbortSignal.timeout(2000) });
    if (r.ok) {
      const h = await r.json();
      dot.style.background = "#10b981";
      dot.title = `Online | Groq: ${h.groq ? "✓" : "✗"} | Chunks: ${h.chunks}`;
    } else {
      dot.style.background = "#ef4444";
    }
  } catch {
    dot.style.background = "#ef4444";
    dot.title = "Server offline — run: python server.py";
  }
}

// ── Load live metrics (ROUGE-L, Accuracy, Recall) from server ────────────────
async function loadLiveMetrics() {
  try {
    const r    = await fetch(`${API}/rouge`, { signal: AbortSignal.timeout(2000) });
    const data = await r.json();
    const rl   = data.rouge_l;
    const acc  = data.accuracy;
    const rec  = data.recall;

    if (rl !== null && rl !== undefined) {
      const rlColor  = rl  >= 0.5 ? "#10b981" : rl  >= 0.3 ? "#f97316" : "#ef4444";
      const accColor = acc >= 0.8 ? "#3b82f6" : acc >= 0.6 ? "#f97316" : "#ef4444";
      const recColor = rec >= 0.8 ? "#6366f1" : rec >= 0.6 ? "#f97316" : "#ef4444";

      document.getElementById("metricRow").innerHTML = `
        <div class="metric-badge" style="border-top-color:${rlColor}">
          <div class="metric-label">ROUGE-L</div>
          <div class="metric-val" style="color:${rlColor}">${rl.toFixed(3)}</div>
          <div class="metric-note">correction</div>
        </div>
        <div class="metric-badge" style="border-top-color:${accColor}">
          <div class="metric-label">Accuracy</div>
          <div class="metric-val" style="color:${accColor}">${acc ? acc.toFixed(3) : "—"}</div>
          <div class="metric-note">correct/total</div>
        </div>
        <div class="metric-badge" style="border-top-color:${recColor}">
          <div class="metric-label">Recall</div>
          <div class="metric-val" style="color:${recColor}">${rec ? rec.toFixed(3) : "—"}</div>
          <div class="metric-note">caught</div>
        </div>`;
    } else {
      document.getElementById("metricRow").innerHTML = `
        <div style="font-size:9px;color:#475569;text-align:center;padding:4px;width:100%">
          Metrics appear after first verification ↑
        </div>`;
    }
  } catch {
    // server offline — metrics stay empty
  }
}

// ── Scan selected text ────────────────────────────────────────────────────────
async function scanSelected() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  chrome.scripting.executeScript(
    { target: { tabId: tab.id }, func: () => window.getSelection()?.toString()?.trim() || "" },
    (results) => {
      const text = results?.[0]?.result || "";
      if (text.length > 5) {
        document.getElementById("input").value = text;
        verify();
      } else {
        showError("No text selected on the page. Please select some text first.");
      }
    }
  );
}

// ── Main verify ───────────────────────────────────────────────────────────────
async function verify() {
  const text = document.getElementById("input").value.trim();
  if (!text) return;

  chrome.storage.local.set({ lastInput: text });

  const btn = document.getElementById("verifyBtn");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Verifying...';
  document.getElementById("result").innerHTML = "";

  try {
    const response = await fetch(`${API}/verify`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ text })
    });

    if (!response.ok) throw new Error(`Server error ${response.status}`);

    const data = await response.json();
    showResult(data);

    // Refresh live metrics after every verification
    loadLiveMetrics();

  } catch (e) {
    if (e.message.includes("fetch") || e.message.includes("Failed")) {
      showError("Cannot reach backend.<br><strong>Run:</strong><br><code>cd backend<br>python server.py</code>");
    } else {
      showError("Error: " + e.message);
    }
  } finally {
    btn.disabled = false;
    btn.innerHTML = "⚡ Verify";
  }
}

// ── Render result ─────────────────────────────────────────────────────────────
function showResult(data) {
  const score  = Math.round(data.score || 0);
  const color  = score >= 60 ? "#ef4444" : score >= 30 ? "#f97316" : score >= 10 ? "#eab308" : "#10b981";
  const label  = score >= 60 ? "🚨 High Risk" : score >= 30 ? "⚠️ Medium Risk" :
                 score >= 10 ? "🔶 Low Risk"  : "✅ Clean";
  const circ   = 2 * Math.PI * 27;
  const offset = circ * (1 - score / 100);

  // Issues
  let issuesHtml = "";
  (data.issues || []).slice(0, 5).forEach(issue => {
    const c = SEV_COLOR[issue.severity] || "#6366f1";
    issuesHtml += `
      <div class="issue">
        <div class="issue-header">
          <div class="sev-dot" style="background:${c}"></div>
          <span style="color:${c};font-size:9px;font-weight:700;text-transform:uppercase">${issue.severity}</span>
          <span style="color:#475569;font-size:9px"> · ${issue.subdomain}</span>
        </div>
        ${escapeHtml(issue.reason)}
      </div>`;
  });

  // Corrected text
  let correctedHtml = "";
  const original = document.getElementById("input").value.trim();
  if (data.corrected && data.corrected !== original) {
    correctedHtml = `
      <div class="corrected">
        <div class="corrected-label">✅ Corrected Response</div>
        <div class="corrected-text">${escapeHtml(data.corrected)}</div>
      </div>`;
  }

  // Live ROUGE-L for this specific verification
  let rougeHtml = "";
  if (data.rouge_l !== null && data.rouge_l !== undefined) {
    const rc = data.rouge_l >= 0.5 ? "#10b981" : data.rouge_l >= 0.3 ? "#f97316" : "#ef4444";
    rougeHtml = `
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;
                  background:rgba(255,255,255,0.03);border-radius:6px;padding:6px 8px">
        <span style="font-size:9px;color:#64748b;font-weight:700;text-transform:uppercase">
          ROUGE-L this text
        </span>
        <span style="font-size:14px;font-weight:700;color:${rc};margin-left:auto">
          ${data.rouge_l.toFixed(3)}
        </span>
        <span style="font-size:9px;color:#475569">correction quality</span>
      </div>`;
  }

  // Sources
  let sourcesHtml = "";
  if (data.sources && data.sources.length > 0) {
    sourcesHtml = `<div style="font-size:9px;color:#475569;margin-bottom:8px">
      📚 ${data.sources.map(s => s.replace(".txt","")).join(" · ")}
    </div>`;
  }

  document.getElementById("result").innerHTML = `
    <div class="score-card">
      <div class="ring">
        <svg width="68" height="68">
          <circle cx="34" cy="34" r="27" stroke="rgba(255,255,255,0.06)" stroke-width="6" fill="none"/>
          <circle cx="34" cy="34" r="27"
            stroke="${color}" stroke-width="6" fill="none"
            stroke-dasharray="${circ.toFixed(1)}"
            stroke-dashoffset="${offset.toFixed(1)}"
            stroke-linecap="round"
            style="transition:stroke-dashoffset 0.8s ease"/>
        </svg>
        <div class="ring-text">
          <span class="ring-pct" style="color:${color}">${score}%</span>
          <span class="ring-unit">halluc.</span>
        </div>
      </div>
      <div class="score-info">
        <h3>${label}</h3>
        <p>${data.reason ? data.reason.slice(0, 80) : "Analysis complete"}</p>
        <span class="tag">${data.subdomain || "general"}</span>
      </div>
    </div>
    ${issuesHtml}
    ${rougeHtml}
    ${correctedHtml}
    ${sourcesHtml}
    <div class="meta">
      <span>⏱ ${data.time_ms || 0}ms</span>
      <span>TF-IDF + Groq LLaMA 3.3</span>
    </div>
  `;
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function clearAll() {
  document.getElementById("input").value = "";
  document.getElementById("result").innerHTML = `
    <div class="empty">
      <div class="empty-icon">🧠</div>
      <p>Paste automotive LLM text above<br>and click <strong>Verify</strong> to detect hallucinations.</p>
    </div>`;
  chrome.storage.local.remove("lastInput");
}

function showError(msg) {
  document.getElementById("result").innerHTML = `
    <div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2);
                border-radius:8px;padding:12px;font-size:11px;color:#fca5a5;line-height:1.7">
      ⚠️ ${msg}
    </div>`;
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\n/g, "<br>");
}
