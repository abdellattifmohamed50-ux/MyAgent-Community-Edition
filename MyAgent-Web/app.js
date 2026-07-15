"use strict";

const API = "/api/v1";
const REFRESH_EXCLUDED_PATHS = new Set([
  "/auth/login",
  "/auth/register",
  "/auth/refresh",
  "/auth/logout",
]);
const state = {
  accessToken: sessionStorage.getItem("myagent_access") || "",
  refreshToken: sessionStorage.getItem("myagent_refresh") || "",
  user: null,
  conversations: [],
  conversationId: null,
  provider: "mock",
  registerMode: false,
  sending: false,
  abortController: null,
  viewRevision: 0,
};

let refreshPromise = null;

const $ = (selector) => document.querySelector(selector);
const authView = $("#authView");
const appView = $("#appView");
const messages = $("#messages");
const emptyState = $("#emptyState");

function setTokens(payload) {
  state.accessToken = payload.access_token;
  state.refreshToken = payload.refresh_token;
  sessionStorage.setItem("myagent_access", state.accessToken);
  sessionStorage.setItem("myagent_refresh", state.refreshToken);
}

function clearSession() {
  state.accessToken = "";
  state.refreshToken = "";
  state.user = null;
  state.abortController?.abort();
  state.abortController = null;
  state.conversations = [];
  state.conversationId = null;
  state.provider = "mock";
  state.sending = false;
  state.viewRevision += 1;
  sessionStorage.removeItem("myagent_access");
  sessionStorage.removeItem("myagent_refresh");
  messages.replaceChildren(emptyState);
  emptyState.classList.remove("hidden");
  $("#conversationList")?.replaceChildren();
  $("#knowledgeList")?.replaceChildren();
  const knowledgeDialog = $("#knowledgeDialog");
  if (knowledgeDialog?.open) knowledgeDialog.close();
}

async function refreshAccessToken() {
  if (!state.refreshToken) return false;
  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const response = await fetch(`${API}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: state.refreshToken }),
        });
        if (!response.ok) return false;
        setTokens(await response.json());
        return true;
      } catch (_) {
        return false;
      } finally {
        refreshPromise = null;
      }
    })();
  }
  return refreshPromise;
}

async function authorizedFetch(path, options = {}, retry = true) {
  const headers = new Headers(options.headers || {});
  if (!(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (state.accessToken) headers.set("Authorization", `Bearer ${state.accessToken}`);
  let response;
  try {
    response = await fetch(`${API}${path}`, { ...options, headers });
    setConnectionStatus(true);
  } catch (error) {
    setConnectionStatus(false);
    throw error;
  }
  if (response.status === 401 && retry && state.refreshToken && !REFRESH_EXCLUDED_PATHS.has(path)) {
    if (await refreshAccessToken()) {
      return authorizedFetch(path, options, false);
    }
    clearSession();
    showAuth();
  }
  return response;
}

async function request(path, options = {}, retry = true) {
  const response = await authorizedFetch(path, options, retry);
  if (!response.ok) {
    let detail = { message: "تعذر إكمال الطلب" };
    try { detail = await response.json(); } catch (_) { /* bounded fallback */ }
    throw new Error(detail.message || `HTTP ${response.status}`);
  }
  if (response.status === 204) return null;
  return response.json();
}

async function boot() {
  bindEvents();
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
  if (!state.accessToken) return showAuth();
  try {
    state.user = await request("/auth/me");
    await showApp();
  } catch (_) {
    clearSession();
    showAuth();
  }
}

function showAuth() {
  authView.classList.remove("hidden");
  appView.classList.add("hidden");
}

function setConnectionStatus(connected) {
  const status = $("#connectionStatus");
  if (!status) return;
  status.classList.toggle("offline", !connected);
  $("#connectionText").textContent = connected ? "Engine متصل" : "Engine غير متصل";
}

async function showApp() {
  authView.classList.add("hidden");
  appView.classList.remove("hidden");
  $("#userName").textContent = state.user.display_name;
  $("#userEmail").textContent = state.user.email;
  $("#avatar").textContent = state.user.display_name.trim().charAt(0).toUpperCase() || "M";
  await Promise.all([loadConversations(), loadProviders()]);
}

async function authenticate(event) {
  event.preventDefault();
  const submit = $("#authSubmit");
  submit.disabled = true;
  $("#authError").textContent = "";
  try {
    const body = {
      email: $("#email").value.trim(),
      password: $("#password").value,
    };
    if (state.registerMode) body.display_name = $("#displayName").value.trim();
    const payload = await request(state.registerMode ? "/auth/register" : "/auth/login", {
      method: "POST",
      body: JSON.stringify(body),
    });
    setTokens(payload);
    state.user = payload.user;
    await showApp();
  } catch (error) {
    $("#authError").textContent = error.message;
  } finally {
    submit.disabled = false;
  }
}

function toggleAuthMode() {
  state.registerMode = !state.registerMode;
  $("#nameField").classList.toggle("hidden", !state.registerMode);
  $("#displayName").required = state.registerMode;
  $("#authTitle").textContent = state.registerMode ? "إنشاء حساب" : "تسجيل الدخول";
  $("#password").autocomplete = state.registerMode ? "new-password" : "current-password";
  $("#password").minLength = state.registerMode ? 10 : 8;
  $("#authSubmit").firstChild.textContent = state.registerMode ? "إنشاء الحساب " : "دخول آمن ";
  $("#authToggle").textContent = state.registerMode
    ? "لديك حساب؟ سجّل الدخول"
    : "مستخدم جديد؟ أنشئ حسابًا";
}

async function logout() {
  try {
    if (state.refreshToken) {
      await request("/auth/logout", {
        method: "POST",
        body: JSON.stringify({ refresh_token: state.refreshToken }),
      });
    }
  } catch (_) { /* local logout still proceeds */ }
  clearSession();
  showAuth();
}

async function loadProviders() {
  const providers = await request("/providers");
  const select = $("#providerSelect");
  select.replaceChildren();
  providers.filter((item) => item.configured && item.healthy).forEach((item) => {
    const option = document.createElement("option");
    option.value = item.name;
    option.textContent = `${item.name} · ${item.model}`;
    option.selected = item.is_default;
    select.append(option);
  });
  state.provider = select.value || "mock";
}

async function loadConversations() {
  state.conversations = await request("/conversations");
  renderConversations();
}

function renderConversations() {
  const list = $("#conversationList");
  list.replaceChildren();
  for (const item of state.conversations) {
    const row = document.createElement("div");
    row.className = `conversation${item.id === state.conversationId ? " active" : ""}`;
    const open = document.createElement("button");
    open.className = "conversation";
    const label = document.createElement("span");
    label.textContent = item.title;
    open.append("◌", label);
    open.addEventListener("click", () => openConversation(item.id));
    const remove = document.createElement("button");
    remove.className = "delete";
    remove.textContent = "×";
    remove.title = "حذف";
    remove.addEventListener("click", async (event) => {
      event.stopPropagation();
      if (!window.confirm("هل تريد حذف هذه المحادثة؟")) return;
      await request(`/conversations/${item.id}`, { method: "DELETE" });
      if (state.conversationId === item.id) newChat();
      await loadConversations();
    });
    row.append(open, remove);
    list.append(row);
  }
}

async function openConversation(id) {
  state.abortController?.abort();
  const revision = ++state.viewRevision;
  state.conversationId = id;
  let history;
  try {
    history = await request(`/conversations/${id}/messages`);
  } catch (_) {
    if (state.viewRevision === revision) toast("تعذر فتح المحادثة");
    return;
  }
  if (state.viewRevision !== revision || state.conversationId !== id) return;
  messages.replaceChildren();
  for (const item of history) appendMessage(item.role, item.content, item.provider);
  renderConversations();
  $("#sidebar").classList.remove("open");
  scrollBottom();
}

function newChat() {
  state.abortController?.abort();
  state.viewRevision += 1;
  state.conversationId = null;
  messages.replaceChildren(emptyState);
  emptyState.classList.remove("hidden");
  renderConversations();
  $("#messageInput").focus();
  $("#sidebar").classList.remove("open");
}

function appendMessage(role, text, provider = null, pending = false) {
  emptyState.classList.add("hidden");
  const row = document.createElement("article");
  row.className = `message-row ${role}`;
  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = role === "assistant" ? "✦" : (state.user?.display_name?.charAt(0) || "U");
  const bubble = document.createElement("div");
  bubble.className = `bubble${pending ? " typing" : ""}`;
  bubble.textContent = text;
  if (provider) {
    const meta = document.createElement("small");
    meta.textContent = provider;
    bubble.append(meta);
  }
  row.append(avatar, bubble);
  messages.append(row);
  scrollBottom();
  return bubble;
}

async function sendMessage(event) {
  event.preventDefault();
  if (state.sending) {
    state.abortController?.abort();
    return;
  }
  const input = $("#messageInput");
  const text = input.value.trim();
  if (!text) return;
  state.sending = true;
  const revision = state.viewRevision;
  state.abortController = new AbortController();
  $("#sendButton").textContent = "■";
  $("#sendButton").setAttribute("aria-label", "إيقاف");
  input.value = "";
  resizeComposer();
  appendMessage("user", text);
  const assistant = appendMessage("assistant", "", state.provider, true);
  try {
    const response = await authorizedFetch("/chat/stream", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${state.accessToken}`,
      },
      body: JSON.stringify({
        message: text,
        conversation_id: state.conversationId,
        provider: state.provider,
      }),
      signal: state.abortController.signal,
    });
    if (!response.ok || !response.body) throw new Error("تعذر الاتصال بالمحرك");
    assistant.classList.remove("typing");
    assistant.textContent = "";
    await consumeEventStream(response.body, (payload) => {
      if (state.viewRevision !== revision) return;
      if (payload.type === "start") state.conversationId = payload.conversation_id;
      if (payload.type === "delta") assistant.append(document.createTextNode(payload.delta));
      scrollBottom();
    });
    await loadConversations();
  } catch (error) {
    assistant.classList.remove("typing");
    assistant.textContent = error.name === "AbortError" ? "تم إيقاف الرد." : `حدث خطأ: ${error.message}`;
  } finally {
    state.sending = false;
    state.abortController = null;
    $("#sendButton").textContent = "↑";
    $("#sendButton").setAttribute("aria-label", "إرسال");
    input.focus();
  }
}

async function consumeEventStream(body, onEvent) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() || "";
    for (const block of blocks) {
      const data = block
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trimStart())
        .join("\n");
      if (data) onEvent(JSON.parse(data));
    }
    if (done) break;
  }
  if (buffer.trim().startsWith("data:")) {
    onEvent(JSON.parse(buffer.trim().slice(5).trimStart()));
  }
}

async function openKnowledge() {
  $("#knowledgeDialog").showModal();
  await loadKnowledge();
}

async function loadKnowledge() {
  const items = await request("/knowledge");
  const list = $("#knowledgeList");
  list.replaceChildren();
  if (!items.length) {
    const empty = document.createElement("p");
    empty.className = "demo-note";
    empty.textContent = "لا توجد مصادر بعد.";
    list.append(empty);
    return;
  }
  for (const item of items) {
    const row = document.createElement("div");
    row.className = "knowledge-item";
    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = item.title;
    const detail = document.createElement("small");
    detail.textContent = `${item.source_type} · ${item.content.length} حرف`;
    copy.append(title, detail);
    const remove = document.createElement("button");
    remove.className = "icon-btn";
    remove.textContent = "×";
    remove.addEventListener("click", async () => {
      if (!window.confirm("هل تريد حذف هذا المصدر؟")) return;
      await request(`/knowledge/${item.id}`, { method: "DELETE" });
      await loadKnowledge();
    });
    row.append(copy, remove);
    list.append(row);
  }
}

async function addKnowledge(event) {
  event.preventDefault();
  await request("/knowledge", {
    method: "POST",
    body: JSON.stringify({
      title: $("#knowledgeTitle").value.trim(),
      content: $("#knowledgeContent").value.trim(),
      source_type: "text",
    }),
  });
  event.target.reset();
  await loadKnowledge();
  toast("تمت إضافة المصدر إلى الذاكرة الخاصة");
}

function resizeComposer() {
  const input = $("#messageInput");
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
}

function scrollBottom() {
  messages.scrollTo({ top: messages.scrollHeight, behavior: "smooth" });
}

function toast(text) {
  const element = $("#toast");
  element.textContent = text;
  element.classList.add("show");
  setTimeout(() => element.classList.remove("show"), 2600);
}

let deferredInstall = null;
function bindEvents() {
  $("#authForm").addEventListener("submit", authenticate);
  $("#authToggle").addEventListener("click", toggleAuthMode);
  $("#logout").addEventListener("click", logout);
  $("#newChat").addEventListener("click", newChat);
  $("#chatForm").addEventListener("submit", sendMessage);
  $("#messageInput").addEventListener("input", resizeComposer);
  $("#messageInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      $("#chatForm").requestSubmit();
    }
  });
  $("#providerSelect").addEventListener("change", (event) => { state.provider = event.target.value; });
  $("#openSidebar").addEventListener("click", () => $("#sidebar").classList.add("open"));
  $("#closeSidebar").addEventListener("click", () => $("#sidebar").classList.remove("open"));
  $("#knowledgeOpen").addEventListener("click", openKnowledge);
  $("#knowledgeForm").addEventListener("submit", addKnowledge);
  document.querySelectorAll("[data-prompt]").forEach((button) => button.addEventListener("click", () => {
    $("#messageInput").value = button.dataset.prompt;
    $("#chatForm").requestSubmit();
  }));
  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredInstall = event;
    $("#installApp").classList.remove("hidden");
  });
  $("#installApp").addEventListener("click", async () => {
    if (!deferredInstall) return;
    deferredInstall.prompt();
    await deferredInstall.userChoice;
    deferredInstall = null;
    $("#installApp").classList.add("hidden");
  });
}

boot();
