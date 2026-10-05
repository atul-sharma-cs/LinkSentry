// ===================== THEME TOGGLE =====================
const themeToggle = document.getElementById("theme-toggle");
const iconMoon = document.getElementById("icon-moon");
const iconSun = document.getElementById("icon-sun");
const htmlEl = document.documentElement;

function applyTheme(theme) {
  htmlEl.setAttribute("data-theme", theme);
  localStorage.setItem("linksentry-theme", theme);
  // Note: SVG elements don't reliably support the `.hidden` boolean property
  // in all browsers, so we toggle `display` directly instead.
  iconMoon.style.display = theme === "light" ? "none" : "";
  iconSun.style.display = theme === "dark" ? "none" : "";
}

// Load saved theme, or default to dark
applyTheme(localStorage.getItem("linksentry-theme") || "dark");

themeToggle.addEventListener("click", () => {
  const current = htmlEl.getAttribute("data-theme");
  applyTheme(current === "dark" ? "light" : "dark");
});

// ===================== CONTACT MODAL =====================
const contactBtn = document.getElementById("contact-btn");
const contactModal = document.getElementById("contact-modal");
const contactClose = document.getElementById("contact-close");

contactBtn.addEventListener("click", () => { contactModal.hidden = false; });
contactClose.addEventListener("click", () => { contactModal.hidden = true; });
contactModal.addEventListener("click", (e) => {
  if (e.target === contactModal) contactModal.hidden = true;
});

// ===================== LEARN MORE TOGGLE =====================
const learnMoreBtn = document.getElementById("learn-more-btn");
const agreementDetail = document.getElementById("agreement-detail");
learnMoreBtn.addEventListener("click", () => {
  agreementDetail.hidden = !agreementDetail.hidden;
});

// ===================== TABS (URL / FILE) =====================
const tabs = document.querySelectorAll(".tab");
const panelUrl = document.getElementById("panel-url");
const panelFile = document.getElementById("panel-file");

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    const target = tab.dataset.tab;
    panelUrl.hidden = target !== "url";
    panelFile.hidden = target !== "file";
    resultSection.hidden = true; // reset any previous result when switching tabs
  });
});

// ===================== SHARED RESULT ELEMENTS =====================
const resultSection = document.getElementById("result-section");
const scanningState = document.getElementById("scanning-state");
const scanningText = document.getElementById("scanning-text");
const verdictCard = document.getElementById("verdict-card");
const errorState = document.getElementById("error-state");
const errorText = document.getElementById("error-text");

function labelToClass(label) {
  switch (label) {
    case "DANGER": return "danger";
    case "CAUTION": return "caution";
    case "SAFE": return "safe";
    default: return "unknown";
  }
}

function showScanning(message) {
  resultSection.hidden = false;
  scanningState.hidden = false;
  verdictCard.hidden = true;
  errorState.hidden = true;
  scanningText.textContent = message;
}

function showError(message) {
  scanningState.hidden = true;
  errorState.hidden = false;
  errorText.textContent = message;
}

function renderResult(data, subjectLabel, signalsHeading) {
  scanningState.hidden = true;
  verdictCard.hidden = false;

  const { final, ai_based, rule_based } = data;
  const cssClass = labelToClass(final.label);

  document.getElementById("verdict-icon").className = "verdict-icon " + cssClass;

  const badge = document.getElementById("verdict-badge");
  badge.className = "verdict-badge " + cssClass;
  document.getElementById("verdict-label").textContent = final.label;

  document.getElementById("verdict-message").textContent = final.message;
  document.getElementById("verdict-subject").textContent = subjectLabel;
  document.getElementById("signals-heading").textContent = signalsHeading;

  const ruleScore = final.rule_score;
  const aiConfidence = final.ai_confidence;

  document.getElementById("rule-score").textContent = ruleScore + "/100";
  document.getElementById("ai-confidence").textContent = aiConfidence + "%";

  const ruleFill = document.getElementById("rule-score-fill");
  ruleFill.style.width = ruleScore + "%";
  ruleFill.className = "meter-fill " + cssClass;

  const aiFill = document.getElementById("ai-confidence-fill");
  aiFill.style.width = aiConfidence + "%";
  aiFill.className = "meter-fill " + cssClass;

  document.getElementById("ai-reasoning").textContent =
    ai_based.reasoning || "No reasoning was returned.";

  const aiFlagsList = document.getElementById("ai-flags");
  aiFlagsList.innerHTML = "";
  (ai_based.red_flags || []).forEach((flag) => {
    const li = document.createElement("li");
    li.textContent = flag;
    aiFlagsList.appendChild(li);
  });

  const ruleFlagsList = document.getElementById("rule-flags");
  ruleFlagsList.innerHTML = "";
  const reasons = rule_based.rule_reasons || [];
  if (reasons.length === 0) {
    const li = document.createElement("li");
    li.textContent = "No suspicious signals were found.";
    ruleFlagsList.appendChild(li);
  } else {
    reasons.forEach((reason) => {
      const li = document.createElement("li");
      li.textContent = reason;
      ruleFlagsList.appendChild(li);
    });
  }
}

// ===================== URL SCAN =====================
const scanForm = document.getElementById("scan-form");
const urlInput = document.getElementById("url-input");
const scanBtn = document.getElementById("scan-btn");

scanForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const url = urlInput.value.trim();
  if (!url) return;

  showScanning(`Analyzing ${url}…`);
  scanBtn.disabled = true;

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    if (!response.ok) throw new Error("The server returned an error. Please try again.");

    const data = await response.json();
    renderResult(data, url, "Structural signals");

  } catch (err) {
    showError(err.message || "Something went wrong. Please try again.");
  } finally {
    scanBtn.disabled = false;
  }
});

// ===================== FILE SCAN =====================
const fileForm = document.getElementById("file-form");
const fileInput = document.getElementById("file-input");
const dropzone = document.getElementById("dropzone");
const dropzoneText = document.getElementById("dropzone-text");
const fileScanBtn = document.getElementById("file-scan-btn");

let selectedFile = null;

fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) {
    selectedFile = fileInput.files[0];
    dropzoneText.textContent = selectedFile.name;
    fileScanBtn.disabled = false;
  }
});

// Drag and drop support
["dragenter", "dragover"].forEach((evt) => {
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.add("drag-over");
  });
});
["dragleave", "drop"].forEach((evt) => {
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.remove("drag-over");
  });
});
dropzone.addEventListener("drop", (e) => {
  const file = e.dataTransfer.files[0];
  if (file) {
    selectedFile = file;
    fileInput.files = e.dataTransfer.files;
    dropzoneText.textContent = file.name;
    fileScanBtn.disabled = false;
  }
});

// Compute SHA-256 hash entirely in the browser — the file's contents
// never leave the device, only the resulting hash + basic metadata do.
async function computeSHA256(file) {
  const buffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
}

fileForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!selectedFile) return;

  showScanning(`Analyzing ${selectedFile.name}…`);
  fileScanBtn.disabled = true;

  try {
    const sha256 = await computeSHA256(selectedFile);

    const response = await fetch("/analyze-file", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        filename: selectedFile.name,
        size: selectedFile.size,
        sha256,
      }),
    });

    if (!response.ok) throw new Error("The server returned an error. Please try again.");

    const data = await response.json();
    renderResult(data, selectedFile.name, "File signals");

  } catch (err) {
    showError(err.message || "Something went wrong. Please try again.");
  } finally {
    fileScanBtn.disabled = false;
  }
});


// ===================== CHAT WIDGET =====================
const chatFab = document.getElementById("chat-fab");
const chatPanel = document.getElementById("chat-panel");
const chatClose = document.getElementById("chat-close");
const chatMessages = document.getElementById("chat-messages");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatSend = document.getElementById("chat-send");

// Conversation history sent to the backend so Gemini has multi-turn context
let chatHistory = [];

chatFab.addEventListener("click", () => {
  chatPanel.hidden = !chatPanel.hidden;
  if (!chatPanel.hidden) chatInput.focus();
});
chatClose.addEventListener("click", () => { chatPanel.hidden = true; });

function addChatMessage(text, sender) {
  const div = document.createElement("div");
  div.className = "chat-msg " + (sender === "user" ? "chat-msg-user" : "chat-msg-bot");
  div.textContent = text;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return div;
}

function showTyping() {
  const div = document.createElement("div");
  div.className = "chat-msg-typing";
  div.id = "chat-typing-indicator";
  div.innerHTML = "<span></span><span></span><span></span>";
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTyping() {
  const el = document.getElementById("chat-typing-indicator");
  if (el) el.remove();
}

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  addChatMessage(message, "user");
  chatInput.value = "";
  chatSend.disabled = true;
  showTyping();

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history: chatHistory }),
    });

    hideTyping();

    if (!response.ok) throw new Error("The assistant is unavailable right now.");

    const data = await response.json();
    addChatMessage(data.reply, "bot");

    // Update history for multi-turn context on the next message
    chatHistory.push({ role: "user", text: message });
    chatHistory.push({ role: "model", text: data.reply });

    // Keep history from growing unbounded
    if (chatHistory.length > 20) chatHistory = chatHistory.slice(-20);

  } catch (err) {
    hideTyping();
    addChatMessage(err.message || "Something went wrong. Please try again.", "bot");
  } finally {
    chatSend.disabled = false;
  }
});
const contactForm = document.getElementById("contact-form");
const contactStatus = document.getElementById("contact-status");
const contactSubmit = document.getElementById("contact-submit");

contactForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  contactSubmit.disabled = true;
  contactStatus.hidden = true;

  const payload = {
    name: document.getElementById("contact-name").value,
    email: document.getElementById("contact-email").value,
    message: document.getElementById("contact-message").value,
  };

  try {
    const response = await fetch("https://formspree.io/f/xbgdrbdg", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(payload),
    });

    if (response.ok) {
      contactStatus.textContent = "Message sent! I'll get back to you soon.";
      contactStatus.className = "contact-status success";
      contactForm.reset();
    } else {
      throw new Error();
    }
  } catch {
    contactStatus.textContent = "Something went wrong. Please try the email link above instead.";
    contactStatus.className = "contact-status error";
  } finally {
    contactStatus.hidden = false;
    contactSubmit.disabled = false;
  }
});