/* ==========================================================================
   全能短剧/小说资源下载器 - 客户端 REST API 绑定与 UI 控制 (App.js)
   E2 商业闭环：多租户登录/注册 -> 兑卡 -> 见 VIP -> 建任务 -> 进度 -> 打开产物
   ========================================================================== */

(function () {
  "use strict";

  // HTML 字符转义工具（XSS 防范）
  function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // 格式化 ISO 日期时间
  function formatDate(isoStr) {
    if (!isoStr) return "未开通";
    try {
      const d = new Date(isoStr);
      if (isNaN(d.getTime())) return isoStr;
      const yyyy = d.getFullYear();
      const mm = String(d.getMonth() + 1).padStart(2, "0");
      const dd = String(d.getDate()).padStart(2, "0");
      const hh = String(d.getHours()).padStart(2, "0");
      const min = String(d.getMinutes()).padStart(2, "0");
      return `${yyyy}-${mm}-${dd} ${hh}:${min}`;
    } catch (_) {
      return isoStr;
    }
  }

  function isLoopbackApi(base) {
    try {
      const url = new URL(base);
      return ["127.0.0.1", "localhost", "::1", "[::1]"].includes(url.hostname);
    } catch (_) {
      return false;
    }
  }

  function isSecureApiBase(base) {
    try {
      const url = new URL(base);
      return url.protocol === "https:" || (url.protocol === "http:" && isLoopbackApi(base));
    } catch (_) {
      return false;
    }
  }

  function defaultApiKeyFor(base) {
    return isLoopbackApi(base) ? "dev-key-change-me" : "";
  }

  // 全局应用状态 State
  const state = {
    theme: localStorage.getItem("theme") || "light",
    platform: localStorage.getItem("platform") || "all",
    // 当前选中结果的平台（聚合搜索时可能与 tab 的 all 不同）
    selectedPlatform: (() => {
      const p = localStorage.getItem("platform") || "hongguo";
      return p === "fanqie" || p === "hongguo" ? p : "hongguo";
    })(),
    activePage: "page-home",
    // 正式用户：同源写死；开发者可在折叠区覆盖
    apiBase: (() => {
      const saved = localStorage.getItem("apiBase");
      if (saved) return saved;
      try {
        if (typeof location !== "undefined" && location.origin && location.protocol.startsWith("http")) {
          return location.origin;
        }
      } catch (_) {}
      return "http://127.0.0.1:8000";
    })(),
    apiKey: localStorage.getItem("apiKey") || defaultApiKeyFor(
      localStorage.getItem("apiBase") || (typeof location !== "undefined" ? location.origin : "")
    ),
    accessToken: localStorage.getItem("accessToken") || "",
    nativeApiBase: "",
    user: null,
    authMode: "login",
    currentDetail: null,
    searchResults: [],
    allSearchResults: [],
    searchFilter: "all",
    lastPlatformErrors: {},
    selectedEpisodes: new Set(),
    jobsPollTimer: null,
    libraryFilter: "all",
    librarySearch: "",
    libraryFiles: [],
    lastHealth: null,
    depsPanelOpen: false,
    discoverPlatform: "hongguo",
    discoverView: "discover",
    discoverData: null,
    homeSelectedItems: new Map(),
    // 下载偏好（本地持久化）
    prefs: {
      outputDir: localStorage.getItem("pref_outputDir") || "",
      rememberOutputDir: localStorage.getItem("pref_rememberOutputDir") !== "0",
      quality: localStorage.getItem("pref_quality") || "1080p",
      rememberQuality: localStorage.getItem("pref_rememberQuality") !== "0",
      openFolderOnComplete: localStorage.getItem("pref_openFolderOnComplete") === "1",
      downloadCover: localStorage.getItem("pref_downloadCover") === "1",
      downloadDesc: localStorage.getItem("pref_downloadDesc") === "1",
      concurrency: parseInt(localStorage.getItem("pref_concurrency") || "2", 10) || 2,
      nameUsePrefix: localStorage.getItem("pref_nameUsePrefix") !== "0",
      nameIncludeTitle: localStorage.getItem("pref_nameIncludeTitle") !== "0",
      nameUseSuffix: localStorage.getItem("pref_nameUseSuffix") === "1",
      numberStyle: localStorage.getItem("pref_numberStyle") || "01",
      nameSeparator: localStorage.getItem("pref_nameSeparator") || ".",
    },
    watchedJobSuccess: {}, // job_id -> opened
  };

  // DOM 元素缓存
  const elements = {
    appHtml: document.documentElement,
    titlebarVersionTag: document.getElementById("titlebarVersionTag"),
    themeToggleBtn: document.getElementById("themeToggleBtn"),
    platformTabs: document.querySelectorAll(".platform-tab"),
    navItems: document.querySelectorAll(".nav-item"),
    subpages: document.querySelectorAll(".subpage"),

    // 侧栏 VIP & 账号区
    vipUserAvatar: document.getElementById("vipUserAvatar"),
    vipUsername: document.getElementById("vipUsername"),
    vipExpireDate: document.getElementById("vipExpireDate"),
    btnOpenAuthModal: document.getElementById("btnOpenAuthModal"),
    btnRedeemKey: document.getElementById("btnRedeemKey"),
    btnLogoutBtn: document.getElementById("btnLogoutBtn"),

    // 首页
    homeSearchQuery: document.getElementById("homeSearchQuery"),
    btnHomeSearch: document.getElementById("btnHomeSearch"),
    btnRefreshDiscover: document.getElementById("btnRefreshDiscover"),
    homeSections: document.getElementById("homeSections"),
    homeDiscoverNote: document.getElementById("homeDiscoverNote"),
    homePlatformTabs: document.querySelectorAll(".home-platform-tab"),
    homeModeTabs: document.querySelectorAll(".home-mode-tab"),
    homeSelectionBar: document.getElementById("homeSelectionBar"),
    homeSelectionCount: document.getElementById("homeSelectionCount"),
    btnHomeSelectAll: document.getElementById("btnHomeSelectAll"),
    btnHomeClearSelection: document.getElementById("btnHomeClearSelection"),
    btnHomeAddQueue: document.getElementById("btnHomeAddQueue"),

    // 搜索页面
    inputSearchQuery: document.getElementById("inputSearchQuery"),
    btnSearch: document.getElementById("btnSearch"),
    btnLoad: document.getElementById("btnLoad"),
    searchResultsList: document.getElementById("searchResultsList"),
    btnLoadMore: document.getElementById("btnLoadMore"),
    searchBanner: document.getElementById("searchBanner"),
    searchFilterRow: document.getElementById("searchFilterRow"),
    searchResultMeta: document.getElementById("searchResultMeta"),
    searchFilterChips: document.querySelectorAll(".filter-chip"),
    toastContainer: document.getElementById("toastContainer"),

    // 详情面板
    searchRightPanel: document.getElementById("searchRightPanel"),
    detailSourceBadge: document.getElementById("detailSourceBadge"),
    detailBannerImg: document.getElementById("detailBannerImg"),
    detailTitle: document.getElementById("detailTitle"),
    detailEpCount: document.getElementById("detailEpCount"),
    detailPlatformLabel: document.getElementById("detailPlatformLabel"),
    detailId: document.getElementById("detailId"),
    detailSynopsis: document.getElementById("detailSynopsis"),
    cardQualityWrapper: document.getElementById("cardQualityWrapper"),
    selectQuality: document.getElementById("selectQuality"),
    epiPagination: document.getElementById("epiPagination"),
    epiChipGrid: document.getElementById("epiChipGrid"),
    btnDownloadAll: document.getElementById("btnDownloadAll"),
    btnDownloadSelected: document.getElementById("btnDownloadSelected"),
    lblBtnDownloadSelected: document.getElementById("lblBtnDownloadSelected"),

    // 下载任务页面
    jobsList: document.getElementById("jobsList"),
    btnOpenOutputDir: document.getElementById("btnOpenOutputDir"),
    jobCountBadge: document.getElementById("jobCountBadge"),
    statActiveJobs: document.querySelector(".jobs-stat-item:nth-child(1) .jobs-stat-val"),
    statCompletedJobs: document.querySelector(".jobs-stat-item:nth-child(2) .jobs-stat-val"),
    statTotalSpeed: document.querySelector(".jobs-stat-item:nth-child(3) .jobs-stat-val"),
    statDiskFree: document.querySelector(".jobs-stat-item:nth-child(4) .jobs-stat-val"),

    // 本地资源页面
    libraryGrid: document.querySelector(".library-grid"),
    libraryFilterTabs: document.querySelectorAll(".filter-tab-pill"),
    librarySearchInput: document.querySelector(".library-filter-bar input"),
    btnLibraryOpenDir: document.getElementById("btnLibraryOpenDir"),

    // 设置页面
    settingUsernameVal: document.getElementById("settingUsernameVal"),
    settingVipExpireVal: document.getElementById("settingVipExpireVal"),
    settingQuotaVal: document.getElementById("settingQuotaVal"),
    settingBtnAuthModal: document.getElementById("settingBtnAuthModal"),
    settingBtnLogout: document.getElementById("settingBtnLogout"),
    settingApiBase: document.getElementById("settingApiBase"),
    settingApiKey: document.getElementById("settingApiKey"),
    settingOutputDir: document.getElementById("settingOutputDir"),
    btnChooseOutputDir: document.getElementById("btnChooseOutputDir"),
    settingRememberOutputDir: document.getElementById("settingRememberOutputDir"),
    settingRememberQuality: document.getElementById("settingRememberQuality"),
    settingOpenFolderOnComplete: document.getElementById("settingOpenFolderOnComplete"),
    settingDownloadCover: document.getElementById("settingDownloadCover"),
    settingDownloadDesc: document.getElementById("settingDownloadDesc"),
    settingConcurrency: document.getElementById("settingConcurrency"),
    settingNameUsePrefix: document.getElementById("settingNameUsePrefix"),
    settingNameIncludeTitle: document.getElementById("settingNameIncludeTitle"),
    settingNameUseSuffix: document.getElementById("settingNameUseSuffix"),
    settingNameSeparator: document.getElementById("settingNameSeparator"),
    settingNamePreview: document.getElementById("settingNamePreview"),
    settingQualityPills: document.querySelectorAll("#settingQualityPills .quality-pill"),
    settingNumberStylePills: document.querySelectorAll("#settingNumberStylePills .quality-pill"),
    btnToggleDevSettings: document.getElementById("btnToggleDevSettings"),
    devSettingsBody: document.getElementById("devSettingsBody"),
    settingAppVersionVal: document.getElementById("settingAppVersionVal"),
    btnResetApiKey: document.getElementById("btnResetApiKey"),
    btnSaveSettings: document.getElementById("btnSaveSettings"),
    btnResetSettings: document.getElementById("btnResetSettings"),
    btnCheckUpdate: document.getElementById("btnCheckUpdate"),

    // 登录 / 注册弹窗
    modalAuth: document.getElementById("modalAuth"),
    btnAuthModalClose: document.getElementById("btnAuthModalClose"),
    tabAuthLogin: document.getElementById("tabAuthLogin"),
    tabAuthRegister: document.getElementById("tabAuthRegister"),
    inputAuthUsername: document.getElementById("inputAuthUsername"),
    inputAuthPassword: document.getElementById("inputAuthPassword"),
    authErrorMessage: document.getElementById("authErrorMessage"),
    btnAuthSubmit: document.getElementById("btnAuthSubmit"),

    // 卡密弹窗
    modalRedeemKey: document.getElementById("modalRedeemKey"),
    btnModalClose: document.getElementById("btnModalClose"),
    btnModalSubmit: document.getElementById("btnModalSubmit"),
    inputCardKey: document.getElementById("inputCardKey"),
    redeemErrorMessage: document.getElementById("redeemErrorMessage"),

    // 状态栏 / 依赖检查
    serverStatusText: document.getElementById("serverStatusText"),
    serverStatusDot: document.getElementById("serverStatusDot"),
    serverStatusBlock: document.getElementById("serverStatusBlock"),
    depsPanel: document.getElementById("depsPanel"),
    depsList: document.getElementById("depsList"),
    depsSummary: document.getElementById("depsSummary"),
    settingHealthStatus: document.getElementById("settingHealthStatus"),
    settingHealthSummary: document.getElementById("settingHealthSummary"),
    settingDepsList: document.getElementById("settingDepsList"),
    btnRefreshHealth: document.getElementById("btnRefreshHealth"),
  };

  const PLATFORM_META = {
    hongguo: { label: "红果短剧", short: "红果", emoji: "🔴", tag: "MP4", kind: "短剧" },
    fanqie: { label: "番茄小说", short: "番茄", emoji: "🍅", tag: "TXT", kind: "小说" },
  };

  function platformOf(itemOrName) {
    if (!itemOrName) return state.selectedPlatform || "hongguo";
    if (typeof itemOrName === "string") {
      const p = itemOrName.toLowerCase();
      if (p === "fanqie" || p === "hongguo") return p;
      return state.selectedPlatform || "hongguo";
    }
    const p = (itemOrName.platform || itemOrName.source_label || "").toString().toLowerCase();
    if (p.includes("fanqie") || p.includes("番茄")) return "fanqie";
    if (p.includes("hongguo") || p.includes("红果")) return "hongguo";
    return state.selectedPlatform || "hongguo";
  }

  function jobStatusLabel(job) {
    const status = String(job.status || "");
    if (status === "pending") return "等待服务端处理";
    if (status === "running") return `服务端处理中 · ${Math.round(job.progress || 0)}%`;
    if (status === "cancelling") return "正在安全取消";
    if (status === "cancelled") return "任务已取消";
    if (status === "success") return `服务端处理完成 · ${job.files ? job.files.length : 0} 个文件可下载`;
    if (status === "failed") return `处理失败 · ${job.error || job.message || "请重试"}`;
    return job.message || status || "状态未知";
  }

  function sourceLabelOf(item) {
    if (item && item.source_label) return item.source_label;
    const p = platformOf(item);
    return (PLATFORM_META[p] && PLATFORM_META[p].label) || p;
  }

  function displayTitle(item) {
    if (!item) return "未命名";
    const t = (item.title || "").toString().trim();
    const id = (item.id || "").toString();
    if (t && t !== id) return t;
    if (item.author) return String(item.author);
    return id ? `资源 ${id}` : "未命名";
  }

  /** 非阻断提示；error 默认更久 */
  function toast(message, type, durationMs) {
    const text = String(message || "").trim();
    if (!text) return;
    const kind = type || "info";
    const ms = durationMs != null ? durationMs : kind === "error" ? 4500 : 2800;
    const host = elements.toastContainer;
    if (!host) {
      console.log(`[toast:${kind}]`, text);
      return;
    }
    const el = document.createElement("div");
    el.className = `toast-item ${kind}`;
    el.textContent = text;
    host.appendChild(el);
    setTimeout(() => {
      el.style.opacity = "0";
      el.style.transition = "opacity 0.2s ease";
      setTimeout(() => el.remove(), 220);
    }, ms);
  }

  function setSearchBanner(html, kind) {
    if (!elements.searchBanner) return;
    if (!html) {
      elements.searchBanner.style.display = "none";
      elements.searchBanner.innerHTML = "";
      return;
    }
    elements.searchBanner.style.display = "block";
    elements.searchBanner.className = `search-banner ${kind || "warning"}`;
    elements.searchBanner.innerHTML = html;
  }

  function renderSearchSkeleton() {
    if (!elements.searchResultsList) return;
    elements.searchResultsList.innerHTML = `
      <div class="search-skeleton">
        ${[1, 2, 3].map(() => `
          <div class="skeleton-card">
            <div class="skeleton-cover"></div>
            <div class="skeleton-lines">
              <div class="skeleton-line w80"></div>
              <div class="skeleton-line w60"></div>
              <div class="skeleton-line w40"></div>
            </div>
          </div>
        `).join("")}
      </div>
    `;
  }

  function encodeFilePath(fileId) {
    if (!fileId) return "";
    return fileId.split("/").map(encodeURIComponent).join("/");
  }

  // 通用 REST Fetch 辅助函数 (E2 统一鉴权: Bearer token 优先; 无 token 时用 X-API-Key)
  // options.timeoutMs: 超时毫秒，默认 30000；搜索等可单独加长/缩短
  async function apiFetch(endpoint, options = {}) {
    const baseUrl = state.apiBase.replace(/\/+$/, "");
    const url = `${baseUrl}${endpoint}`;
    const timeoutMs = options.timeoutMs != null ? options.timeoutMs : 30000;
    const { timeoutMs: _tm, ...fetchOpts } = options;

    const headers = {
      "Content-Type": "application/json",
      ...(fetchOpts.headers || {}),
    };

    if (state.accessToken) {
      headers["Authorization"] = `Bearer ${state.accessToken}`;
    } else if (state.apiKey) {
      headers["X-API-Key"] = state.apiKey;
    }

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    let response;
    try {
      response = await fetch(url, { ...fetchOpts, headers, signal: controller.signal });
    } catch (err) {
      if (err && err.name === "AbortError") {
        throw new Error(`请求超时（${Math.round(timeoutMs / 1000)} 秒）。番茄书名搜索需服务端签名环境，可改用书籍数字 ID。`);
      }
      throw err;
    } finally {
      clearTimeout(timer);
    }

    if (!response.ok) {
      const errData = await response.json().catch(() => ({ detail: response.statusText }));
      const errorDetail = errData.detail || `HTTP ${response.status}`;

      // 401: token 过期或无效
      if (response.status === 401 && state.accessToken && !endpoint.includes("/v1/auth/login")) {
        state.accessToken = "";
        localStorage.removeItem("accessToken");
        state.user = null;
        updateAuthUI();
        toast("登录凭证已失效或过期，请重新登录", "warning");
      }
      throw new Error(typeof errorDetail === "string" ? errorDetail : JSON.stringify(errorDetail));
    }
    return response.json();
  }

  function authHeaders(includeJson = false) {
    const headers = {};
    if (includeJson) headers["Content-Type"] = "application/json";
    if (state.accessToken) headers["Authorization"] = `Bearer ${state.accessToken}`;
    else if (state.apiKey) headers["X-API-Key"] = state.apiKey;
    return headers;
  }

  async function downloadFileInBrowser(file) {
    const fileId = file.file_id;
    const baseUrl = state.apiBase.replace(/\/+$/, "");
    const response = await fetch(`${baseUrl}/v1/files/${encodeFilePath(fileId)}`, {
      headers: authHeaders(false),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || `HTTP ${response.status}`);
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    try {
      const link = document.createElement("a");
      link.href = url;
      link.download = file.name || file.title || fileId.split("/").pop() || "download.bin";
      document.body.appendChild(link);
      link.click();
      link.remove();
    } finally {
      setTimeout(() => URL.revokeObjectURL(url), 30000);
    }
    return { success: true, browser: true };
  }

  async function deliverFileLocal(file, action = "download") {
    if (!file || !file.file_id) {
      toast("文件信息不完整，无法下载", "error");
      return;
    }
    const filename = file.name || file.title || file.file_id.split("/").pop() || "download.bin";
    try {
      toast(`正在传输到本机：${filename}`, "info", 2500);
      if (window.pywebview && window.pywebview.api && window.pywebview.api.download_file) {
        const result = await window.pywebview.api.download_file(
          file.file_id,
          filename,
          state.accessToken || "",
          state.apiKey || ""
        );
        if (!result || !result.success) {
          throw new Error((result && result.message) || "客户端下载失败");
        }
        toast(`已保存到本机：${result.path}`, "success", 4500);
        if (action === "play" || action === "folder") {
          const opened = await window.pywebview.api.open_local_file(file.file_id, action);
          if (!opened || !opened.success) {
            throw new Error((opened && opened.message) || "无法打开本机文件");
          }
        }
        return result;
      }

      const result = await downloadFileInBrowser(file);
      toast(
        action === "download"
          ? "文件已交给浏览器下载"
          : "文件已下载，请从浏览器下载列表打开",
        "success",
        4000
      );
      return result;
    } catch (e) {
      toast(`文件交付失败：${e.message}`, "error", 5000);
      throw e;
    }
  }

  // 获取 /v1/auth/me 并更新状态
  async function fetchMe() {
    if (!state.accessToken) {
      state.user = null;
      updateAuthUI();
      return;
    }
    try {
      const me = await apiFetch("/v1/auth/me");
      state.user = me;
    } catch (err) {
      console.warn("拉取用户信息失败 (可能未登录或凭证无效):", err.message);
      state.user = null;
    } finally {
      updateAuthUI();
    }
  }

  // 判断用户 VIP 是否在有效期内
  function isVipActive(u) {
    if (!u || !u.vip_expires_at) return false;
    const t = new Date(u.vip_expires_at).getTime();
    return !isNaN(t) && t > Date.now();
  }

  // 更新所有与账号/VIP相关的 UI
  function updateAuthUI() {
    const u = state.user;
    const isVip = isVipActive(u);
    if (u) {
      // 登录状态
      if (elements.vipUsername) elements.vipUsername.textContent = u.username;
      if (elements.vipUserAvatar) elements.vipUserAvatar.textContent = isVip ? "👑" : "👤";
      if (elements.vipExpireDate) {
        if (isVip && u.vip_expires_at) {
          elements.vipExpireDate.textContent = `VIP 到期: ${formatDate(u.vip_expires_at)}`;
        } else {
          elements.vipExpireDate.textContent = "未开通 VIP";
        }
      }

      if (elements.btnOpenAuthModal) elements.btnOpenAuthModal.style.display = "none";
      if (elements.btnRedeemKey) elements.btnRedeemKey.style.display = "flex";
      if (elements.btnLogoutBtn) elements.btnLogoutBtn.style.display = "block";

      // 设置页面
      if (elements.settingUsernameVal) elements.settingUsernameVal.textContent = `${u.username} (${isVip ? "VIP 会员" : "普通用户"})`;
      if (elements.settingVipExpireVal) {
        elements.settingVipExpireVal.textContent = isVip && u.vip_expires_at ? formatDate(u.vip_expires_at) : "未开通 VIP";
      }
      if (elements.settingQuotaVal) {
        if (typeof u.jobs_today === "number" && typeof u.jobs_limit === "number") {
          const lim = u.jobs_limit <= 0 ? "不限" : String(u.jobs_limit);
          elements.settingQuotaVal.textContent = `今日 ${u.jobs_today} / ${lim}`;
        } else {
          elements.settingQuotaVal.textContent = isVip ? "VIP 生效中" : "登录后可见额度";
        }
      }
      if (elements.settingBtnAuthModal) elements.settingBtnAuthModal.style.display = "none";
      if (elements.settingBtnLogout) elements.settingBtnLogout.style.display = "inline-block";
    } else {
      // 未登录状态
      if (elements.vipUsername) elements.vipUsername.textContent = "未登录";
      if (elements.vipUserAvatar) elements.vipUserAvatar.textContent = "👤";
      if (elements.vipExpireDate) elements.vipExpireDate.textContent = "登录后解锁完整功能";

      if (elements.btnOpenAuthModal) elements.btnOpenAuthModal.style.display = "flex";
      if (elements.btnRedeemKey) elements.btnRedeemKey.style.display = "none";
      if (elements.btnLogoutBtn) elements.btnLogoutBtn.style.display = "none";

      // 设置页面
      if (elements.settingUsernameVal) elements.settingUsernameVal.textContent = "未登录";
      if (elements.settingVipExpireVal) elements.settingVipExpireVal.textContent = "未开通 VIP";
      if (elements.settingQuotaVal) elements.settingQuotaVal.textContent = "未登录";
      if (elements.settingBtnAuthModal) elements.settingBtnAuthModal.style.display = "inline-block";
      if (elements.settingBtnLogout) elements.settingBtnLogout.style.display = "none";
    }
  }

  // Auth 弹窗控制
  function openAuthModal(mode = "login") {
    state.authMode = mode;
    setAuthTab(mode);
    if (elements.authErrorMessage) elements.authErrorMessage.style.display = "none";
    if (elements.inputAuthUsername) elements.inputAuthUsername.value = "";
    if (elements.inputAuthPassword) elements.inputAuthPassword.value = "";
    if (elements.modalAuth) elements.modalAuth.classList.add("active");
  }

  function closeAuthModal() {
    if (elements.modalAuth) elements.modalAuth.classList.remove("active");
  }

  function setAuthTab(mode) {
    state.authMode = mode;
    if (elements.tabAuthLogin) {
      elements.tabAuthLogin.classList.toggle("active", mode === "login");
      elements.tabAuthLogin.style.background = mode === "login" ? "var(--bg-card-hover)" : "transparent";
      elements.tabAuthLogin.style.color = mode === "login" ? "var(--text-primary)" : "var(--text-secondary)";
    }
    if (elements.tabAuthRegister) {
      elements.tabAuthRegister.classList.toggle("active", mode === "register");
      elements.tabAuthRegister.style.background = mode === "register" ? "var(--bg-card-hover)" : "transparent";
      elements.tabAuthRegister.style.color = mode === "register" ? "var(--text-primary)" : "var(--text-secondary)";
    }
    if (elements.btnAuthSubmit) {
      elements.btnAuthSubmit.textContent = mode === "login" ? "立即登录" : "立即注册";
    }
  }

  // 登录/注册操作
  async function doAuthSubmit() {
    const username = elements.inputAuthUsername.value.trim();
    const password = elements.inputAuthPassword.value.trim();

    if (!username || !password) {
      showAuthError("用户名和密码不能为空");
      return;
    }

    elements.btnAuthSubmit.disabled = true;
    if (elements.authErrorMessage) elements.authErrorMessage.style.display = "none";

    if (state.authMode === "login") {
      try {
        const res = await apiFetch("/v1/auth/login", {
          method: "POST",
          body: JSON.stringify({ username, password }),
        });

        state.accessToken = res.access_token;
        localStorage.setItem("accessToken", res.access_token);
        await fetchMe();
        closeAuthModal();
        toast(`登录成功，欢迎 ${username}`, "success");
      } catch (err) {
        showAuthError(`登录失败: ${err.message}`);
      } finally {
        elements.btnAuthSubmit.disabled = false;
      }
    } else {
      // 注册
      try {
        await apiFetch("/v1/auth/register", {
          method: "POST",
          body: JSON.stringify({ username, password }),
        });

        toast("注册成功，正在自动登录…", "success");
        // 自动登录
        const res = await apiFetch("/v1/auth/login", {
          method: "POST",
          body: JSON.stringify({ username, password }),
        });
        state.accessToken = res.access_token;
        localStorage.setItem("accessToken", res.access_token);
        await fetchMe();
        closeAuthModal();
      } catch (err) {
        showAuthError(`注册失败: ${err.message}`);
      } finally {
        elements.btnAuthSubmit.disabled = false;
      }
    }
  }

  function showAuthError(msg) {
    if (elements.authErrorMessage) {
      elements.authErrorMessage.textContent = msg;
      elements.authErrorMessage.style.display = "block";
    } else {
      toast(msg, "error");
    }
  }

  function doLogout() {
    state.accessToken = "";
    localStorage.removeItem("accessToken");
    state.user = null;
    updateAuthUI();
    toast("已退出登录", "info");
  }

  // 1. 初始化主题与配置
  function initTheme() {
    setTheme(state.theme);
  }

  function setTheme(themeName) {
    state.theme = themeName;
    localStorage.setItem("theme", themeName);
    elements.appHtml.setAttribute("data-theme", themeName);
    if (elements.themeToggleBtn) {
      elements.themeToggleBtn.textContent =
        themeName === "dark" ? "☀️ 切换浅色主题" : "🌙 切换深色主题";
    }
  }

  function formatNamePreview(index, title) {
    const p = state.prefs;
    const n = Number(index) || 1;
    let num = String(n);
    if (p.numberStyle === "01") num = String(n).padStart(2, "0");
    else if (p.numberStyle === "001") num = String(n).padStart(3, "0");
    const sep = p.nameSeparator != null ? p.nameSeparator : ".";
    const parts = [];
    if (p.nameUsePrefix) parts.push(num);
    if (p.nameIncludeTitle) parts.push(title || "标题");
    let name = parts.join(sep);
    if (!name) name = num;
    if (p.nameUseSuffix) name += ".txt";
    else name += ".txt";
    return name;
  }

  function updateNamePreview() {
    if (elements.settingNamePreview) {
      elements.settingNamePreview.textContent = formatNamePreview(1, "空屋");
    }
  }

  function readPrefsFromForm() {
    const p = state.prefs;
    if (elements.settingOutputDir) p.outputDir = elements.settingOutputDir.value.trim();
    if (elements.settingRememberOutputDir) p.rememberOutputDir = !!elements.settingRememberOutputDir.checked;
    if (elements.settingRememberQuality) p.rememberQuality = !!elements.settingRememberQuality.checked;
    if (elements.settingOpenFolderOnComplete) p.openFolderOnComplete = !!elements.settingOpenFolderOnComplete.checked;
    if (elements.settingDownloadCover) p.downloadCover = !!elements.settingDownloadCover.checked;
    if (elements.settingDownloadDesc) p.downloadDesc = !!elements.settingDownloadDesc.checked;
    if (elements.settingConcurrency) {
      const n = parseInt(elements.settingConcurrency.value, 10);
      p.concurrency = Math.min(12, Math.max(1, isNaN(n) ? 2 : n));
    }
    if (elements.settingNameUsePrefix) p.nameUsePrefix = !!elements.settingNameUsePrefix.checked;
    if (elements.settingNameIncludeTitle) p.nameIncludeTitle = !!elements.settingNameIncludeTitle.checked;
    if (elements.settingNameUseSuffix) p.nameUseSuffix = !!elements.settingNameUseSuffix.checked;
    if (elements.settingNameSeparator) p.nameSeparator = elements.settingNameSeparator.value || ".";
    // quality / numberStyle 由 pill 写入 state.prefs
    if (elements.selectQuality && p.rememberQuality) {
      // 同步详情页清晰度选择到 prefs（若用户刚改过）
    }
  }

  function persistPrefs() {
    const p = state.prefs;
    const set = (k, v) => localStorage.setItem(k, v);
    if (p.rememberOutputDir) set("pref_outputDir", p.outputDir || "");
    else localStorage.removeItem("pref_outputDir");
    set("pref_rememberOutputDir", p.rememberOutputDir ? "1" : "0");
    if (p.rememberQuality) set("pref_quality", p.quality || "1080p");
    set("pref_rememberQuality", p.rememberQuality ? "1" : "0");
    set("pref_openFolderOnComplete", p.openFolderOnComplete ? "1" : "0");
    set("pref_downloadCover", p.downloadCover ? "1" : "0");
    set("pref_downloadDesc", p.downloadDesc ? "1" : "0");
    set("pref_concurrency", String(p.concurrency || 2));
    set("pref_nameUsePrefix", p.nameUsePrefix ? "1" : "0");
    set("pref_nameIncludeTitle", p.nameIncludeTitle ? "1" : "0");
    set("pref_nameUseSuffix", p.nameUseSuffix ? "1" : "0");
    set("pref_numberStyle", p.numberStyle || "01");
    set("pref_nameSeparator", p.nameSeparator || ".");
  }

  function initSettingsForm() {
    if (elements.settingApiBase) elements.settingApiBase.value = state.apiBase;
    if (elements.settingApiKey) elements.settingApiKey.value = state.apiKey;
    const p = state.prefs;
    if (elements.settingOutputDir) elements.settingOutputDir.value = p.outputDir || "";
    if (elements.settingRememberOutputDir) elements.settingRememberOutputDir.checked = !!p.rememberOutputDir;
    if (elements.settingRememberQuality) elements.settingRememberQuality.checked = !!p.rememberQuality;
    if (elements.settingOpenFolderOnComplete) elements.settingOpenFolderOnComplete.checked = !!p.openFolderOnComplete;
    if (elements.settingDownloadCover) elements.settingDownloadCover.checked = !!p.downloadCover;
    if (elements.settingDownloadDesc) elements.settingDownloadDesc.checked = !!p.downloadDesc;
    if (elements.settingConcurrency) elements.settingConcurrency.value = String(p.concurrency || 2);
    if (elements.settingNameUsePrefix) elements.settingNameUsePrefix.checked = !!p.nameUsePrefix;
    if (elements.settingNameIncludeTitle) elements.settingNameIncludeTitle.checked = !!p.nameIncludeTitle;
    if (elements.settingNameUseSuffix) elements.settingNameUseSuffix.checked = !!p.nameUseSuffix;
    if (elements.settingNameSeparator) elements.settingNameSeparator.value = p.nameSeparator || ".";
    if (elements.settingQualityPills) {
      elements.settingQualityPills.forEach((btn) => {
        btn.classList.toggle("active", btn.getAttribute("data-quality") === p.quality);
      });
    }
    if (elements.settingNumberStylePills) {
      elements.settingNumberStylePills.forEach((btn) => {
        btn.classList.toggle("active", btn.getAttribute("data-style") === p.numberStyle);
      });
    }
    if (elements.selectQuality && p.quality) {
      elements.selectQuality.value = p.quality;
    }
    updateNamePreview();
  }

  function buildJobOptions() {
    const p = state.prefs;
    let quality = p.quality || "1080p";
    if (elements.selectQuality && elements.selectQuality.value) {
      quality = elements.selectQuality.value;
      if (p.rememberQuality) {
        p.quality = quality;
        localStorage.setItem("pref_quality", quality);
      }
    }
    return {
      quality,
      concurrency: p.concurrency || 2,
      download_cover: !!p.downloadCover,
      download_desc: !!p.downloadDesc,
      naming: {
        use_prefix: !!p.nameUsePrefix,
        include_title: !!p.nameIncludeTitle,
        use_suffix: !!p.nameUseSuffix,
        number_style: p.numberStyle || "01",
        separator: p.nameSeparator || ".",
      },
    };
  }

  // 2. 平台选择器（all = 聚合搜索）
  function setPlatform(platformName) {
    const name = platformName || "all";
    state.platform = name;
    localStorage.setItem("platform", name);
    // 非 all 时同步 selectedPlatform，便于详情/下载
    if (name === "fanqie" || name === "hongguo") {
      state.selectedPlatform = name;
    }
    elements.platformTabs.forEach((tab) => {
      tab.classList.toggle("active", tab.getAttribute("data-platform") === name);
    });

    if (elements.cardQualityWrapper) {
      const p = state.selectedPlatform;
      elements.cardQualityWrapper.style.display = p === "fanqie" ? "none" : "block";
    }

    if (elements.inputSearchQuery && elements.inputSearchQuery.value.trim()) {
      doSearch();
    }
  }

  // 3. 路由与页面切换
  function switchPage(pageId) {
    state.activePage = pageId;
    elements.navItems.forEach((nav) => {
      nav.classList.toggle("active", nav.getAttribute("data-page") === pageId);
    });
    elements.subpages.forEach((page) => {
      page.classList.toggle("active", page.id === pageId);
    });

    if (pageId === "page-home") {
      loadDiscover();
      stopJobsPolling();
    } else if (pageId === "page-library") {
      loadLocalFiles();
      stopJobsPolling();
    } else if (pageId === "page-jobs") {
      refreshJobsPage();
      startJobsPolling();
    } else {
      stopJobsPolling();
    }
  }

  function goSearchWithQuery(q) {
    if (elements.inputSearchQuery) elements.inputSearchQuery.value = q || "";
    switchPage("page-search");
    if (q && String(q).trim()) doSearch();
  }

  // 4. 执行资源搜索（支持 platform=all 聚合 + 来源标记）
  async function doSearch() {
    const query = elements.inputSearchQuery.value.trim();
    if (!query) {
      toast(
        state.platform === "fanqie"
          ? "请输入书名、书籍 ID 或 fanqienovel 链接"
          : state.platform === "hongguo"
            ? "请输入剧名、剧集 ID 或链接"
            : "请输入关键词；将同时搜索红果与番茄",
        "warning"
      );
      return;
    }
    elements.btnSearch.textContent = "搜索中...";
    elements.btnSearch.disabled = true;
    setSearchBanner("正在搜索…（聚合时可能需等待签名环境）", "info");
    renderSearchSkeleton();

    try {
      const platParam = state.platform || "all";
      const timeoutMs = platParam === "hongguo" ? 30000 : 45000;
      const data = await apiFetch(
        `/v1/search?platform=${encodeURIComponent(platParam)}&q=${encodeURIComponent(query)}`,
        { timeoutMs }
      );
      const items = Array.isArray(data) ? data : (data.items || []);
      const platformErrors = Array.isArray(data) ? {} : (data.platform_errors || {});
      state.allSearchResults = items;
      state.lastPlatformErrors = platformErrors;
      state.searchFilter = "all";
      if (elements.searchFilterChips) {
        elements.searchFilterChips.forEach((c) => {
          c.classList.toggle("active", c.getAttribute("data-filter") === "all");
        });
      }
      applySearchFilter();

      const errKeys = Object.keys(platformErrors);
      if (items.length > 0) {
        if (errKeys.length > 0) {
          const errHtml = errKeys
            .map((k) => `<div>· <b>${escapeHtml(k)}</b>: ${escapeHtml(platformErrors[k])}</div>`)
            .join("");
          setSearchBanner(`部分平台失败，已展示可用结果：${errHtml}`, "warning");
          toast(`部分平台搜索失败：${errKeys.join("、")}`, "warning");
        } else {
          setSearchBanner("", "");
        }
        if (elements.searchRightPanel) elements.searchRightPanel.style.display = "flex";
        const first = (state.searchResults && state.searchResults[0]) || items[0];
        state.selectedPlatform = platformOf(first);
        loadDetail(first.id, state.selectedPlatform);
      } else {
        let msg = "未搜索到相关资源，请尝试更改关键词或使用「载入 ID」。";
        if (errKeys.length > 0) {
          msg = "各平台均未返回结果。";
          setSearchBanner(
            errKeys.map((k) => `· <b>${escapeHtml(k)}</b>: ${escapeHtml(platformErrors[k])}`).join("<br>"),
            "error"
          );
        } else {
          setSearchBanner(msg, "warning");
        }
        toast(msg, "warning");
      }
    } catch (e) {
      setSearchBanner(`搜索失败：${escapeHtml(e.message)}`, "error");
      toast(`搜索失败: ${e.message}`, "error");
      state.allSearchResults = [];
      state.searchResults = [];
      renderSearchResults([]);
    } finally {
      elements.btnSearch.textContent = "搜索";
      elements.btnSearch.disabled = false;
    }
  }

  function applySearchFilter() {
    const filter = state.searchFilter || "all";
    const all = state.allSearchResults || [];
    const filtered =
      filter === "all" ? all : all.filter((it) => platformOf(it) === filter);
    state.searchResults = filtered;

    const nHg = all.filter((it) => platformOf(it) === "hongguo").length;
    const nFq = all.filter((it) => platformOf(it) === "fanqie").length;
    if (elements.searchFilterRow) {
      elements.searchFilterRow.style.display = all.length ? "flex" : "none";
    }
    if (elements.searchResultMeta) {
      elements.searchResultMeta.textContent = all.length
        ? `共 ${all.length} 条 · 红果 ${nHg} · 番茄 ${nFq}` +
          (filter !== "all" ? ` · 筛选后 ${filtered.length}` : "")
        : "";
    }
    renderSearchResults(filtered);
  }

  function renderSearchResults(items) {
    if (!elements.searchResultsList) return;
    elements.searchResultsList.innerHTML = "";

    if (!items || items.length === 0) {
      elements.searchResultsList.innerHTML = `
        <div class="search-empty-state" style="text-align: center; padding: 60px 20px; color: var(--text-secondary);">
          <div style="font-size: 48px; margin-bottom: 12px;">🔍</div>
          <div style="font-size: 14px; font-weight: 600;">未查找到结果</div>
        </div>
      `;
      return;
    }

    items.forEach((item, index) => {
      const plat = platformOf(item);
      const meta = PLATFORM_META[plat] || PLATFORM_META.hongguo;
      const label = sourceLabelOf(item);
      const title = displayTitle(item);
      const card = document.createElement("div");
      card.className = `resource-card-item ${index === 0 ? "selected" : ""}`;
      card.setAttribute("data-id", item.id);
      card.setAttribute("data-platform", plat);

      const coverHtml = item.cover
        ? `<img src="${escapeHtml(item.cover)}" alt="封面" onerror="this.replaceWith(Object.assign(document.createElement('div'),{className:'card-cover-placeholder',textContent:'${meta.emoji}'}))">`
        : `<div class="card-cover-placeholder">${escapeHtml(meta.emoji)}</div>`;

      card.innerHTML = `
        <div class="card-cover-wrapper">
          <span class="card-media-badge">${escapeHtml(meta.tag)}</span>
          ${coverHtml}
        </div>
        <div class="card-content">
          <div class="card-title">${escapeHtml(title)}</div>
          <div class="card-id-line">ID: ${escapeHtml(String(item.id || ""))}</div>
          <div class="card-desc">${escapeHtml(item.desc || item.author || "暂无简介…")}</div>
          <div class="card-meta-row">
            <span class="source-badge ${escapeHtml(plat)}">${escapeHtml(meta.emoji)} ${escapeHtml(label)}</span>
            <button class="btn-quick-dl" title="加载详情">📥</button>
          </div>
        </div>
      `;

      card.addEventListener("click", () => {
        document.querySelectorAll(".resource-card-item").forEach((c) => c.classList.remove("selected"));
        card.classList.add("selected");
        state.selectedPlatform = plat;
        if (elements.cardQualityWrapper) {
          elements.cardQualityWrapper.style.display = plat === "fanqie" ? "none" : "block";
        }
        if (elements.searchRightPanel) elements.searchRightPanel.style.display = "flex";
        loadDetail(item.id, plat);
      });

      elements.searchResultsList.appendChild(card);
    });
  }

  // 5. 加载详情信息与选集网格
  async function loadDetail(itemId, platformOverride) {
    const plat =
      platformOverride ||
      state.selectedPlatform ||
      (state.platform !== "all" ? state.platform : "hongguo");
    state.selectedPlatform = plat;
    try {
      const detail = await apiFetch(
        `/v1/detail?platform=${encodeURIComponent(plat)}&id=${encodeURIComponent(itemId)}`
      );
      state.currentDetail = detail;
      if (detail.platform) {
        state.selectedPlatform = platformOf(detail.platform);
      }

      if (elements.detailTitle) elements.detailTitle.textContent = displayTitle(detail);
      if (elements.detailId) elements.detailId.textContent = detail.id;
      if (elements.detailSynopsis) {
        elements.detailSynopsis.textContent = detail.desc || "暂无详细描述";
      }
      const segCount = detail.segments ? detail.segments.length : 0;
      if (elements.detailEpCount) {
        elements.detailEpCount.textContent =
          segCount > 0 ? `${segCount} 条` : "暂无选集数据";
      }

      const isHongguo = state.selectedPlatform === "hongguo";
      const meta = PLATFORM_META[state.selectedPlatform] || PLATFORM_META.hongguo;
      if (elements.detailSourceBadge) {
        elements.detailSourceBadge.textContent = isHongguo
          ? "🔴 红果短剧"
          : "🍅 番茄小说";
      }
      if (elements.detailPlatformLabel) {
        elements.detailPlatformLabel.textContent = meta.label;
        elements.detailPlatformLabel.style.color = isHongguo
          ? "var(--color-hongguo)"
          : "var(--color-fanqie)";
      }
      if (elements.cardQualityWrapper) {
        elements.cardQualityWrapper.style.display = isHongguo ? "block" : "none";
      }
      if (elements.detailBannerImg) {
        if (detail.cover) {
          elements.detailBannerImg.src = detail.cover;
          elements.detailBannerImg.style.display = "";
        } else {
          elements.detailBannerImg.removeAttribute("src");
          elements.detailBannerImg.style.display = "none";
        }
      }

      renderEpisodesGrid(detail.segments || []);
    } catch (e) {
      toast(`获取详情失败: ${e.message}`, "error");
    }
  }

  function renderEpisodesGrid(segments) {
    if (!elements.epiChipGrid) return;
    elements.epiChipGrid.innerHTML = "";
    state.selectedEpisodes.clear();

    if (!segments || segments.length === 0) {
      elements.epiChipGrid.innerHTML =
        `<div class="epi-empty-hint">暂无章节/剧集列表。可尝试「下载全部」，或确认资源 ID 是否正确。</div>`;
      updateSelectedCountLabel();
      return;
    }

    segments.forEach((seg, idx) => {
      const epIndex = seg.index || idx + 1;
      state.selectedEpisodes.add(epIndex);
      const label = document.createElement("label");
      label.className = "epi-chip-item";
      label.innerHTML = `
        <input type="checkbox" checked value="${epIndex}">
        <span>${escapeHtml(seg.title || "第 " + epIndex + " 集")}</span>
      `;

      label.querySelector("input").addEventListener("change", (e) => {
        if (e.target.checked) {
          state.selectedEpisodes.add(epIndex);
        } else {
          state.selectedEpisodes.delete(epIndex);
        }
        updateSelectedCountLabel();
      });

      elements.epiChipGrid.appendChild(label);
    });

    updateSelectedCountLabel();
  }

  // 首页发现：按平台 tab（红果 / 番茄），各展示热榜 + 今日上新
  function setDiscoverPlatform(plat) {
    const p = plat === "fanqie" ? "fanqie" : "hongguo";
    state.discoverPlatform = p;
    state.homeSelectedItems.clear();
    updateHomeSelectionBar();
    if (elements.homePlatformTabs) {
      elements.homePlatformTabs.forEach((tab) => {
        tab.classList.toggle("active", tab.getAttribute("data-platform") === p);
      });
    }
    if (state.discoverView === "discover") {
      loadDiscover();
    } else {
      renderHomeFeatureView(state.discoverView);
    }
  }

  function setDiscoverView(view) {
    const supported = ["discover", "ranking", "calendar", "following"];
    const nextView = supported.includes(view) ? view : "discover";
    state.discoverView = nextView;
    state.homeSelectedItems.clear();
    updateHomeSelectionBar();
    elements.homeModeTabs.forEach((tab) => {
      tab.classList.toggle("active", tab.getAttribute("data-view") === nextView);
    });
    if (nextView === "discover") {
      loadDiscover();
    } else {
      renderHomeFeatureView(nextView);
    }
  }

  function updateHomeSelectionBar() {
    if (!elements.homeSelectionBar || !elements.homeSelectionCount) return;
    const count = state.homeSelectedItems.size;
    elements.homeSelectionBar.hidden = count === 0;
    elements.homeSelectionCount.textContent = `已选 ${count} 项`;
  }

  function syncHomeCardSelections() {
    document.querySelectorAll(".home-card").forEach((card) => {
      const key = `${card.getAttribute("data-platform")}:${card.getAttribute("data-id")}`;
      const selected = state.homeSelectedItems.has(key);
      card.classList.toggle("selected", selected);
      const checkbox = card.querySelector(".home-card-checkbox");
      if (checkbox) checkbox.checked = selected;
    });
  }

  function renderHomeFeatureView(view) {
    if (!elements.homeSections) return;
    const plat = state.discoverPlatform || "hongguo";
    const meta = PLATFORM_META[plat] || PLATFORM_META.hongguo;
    const configs = {
      ranking: {
        eyebrow: "RANKING",
        icon: "↗",
        title: `${meta.short}排行榜`,
        copy: "按热度、涨幅和口碑发现近期值得关注的作品。",
        chips: ["热度榜", "飙升榜", "新作榜"],
        action: "先去搜索热门作品",
      },
      calendar: {
        eyebrow: "CALENDAR",
        icon: "▦",
        title: `${meta.short}上线日历`,
        copy: "按日期查看待上线与近期更新内容，减少错过新作和新集。",
        chips: ["今天", "明天", "本周", "下周"],
        action: "搜索近期作品",
      },
      following: {
        eyebrow: "FOLLOWING",
        icon: "♡",
        title: "我的追更",
        copy: "收藏作品并订阅更新，后续可在发现新集时提醒或自动加入队列。",
        chips: ["全部订阅", "今日更新", "等待更新"],
        action: "查找想追更的作品",
      },
    };
    const config = configs[view] || configs.ranking;
    if (elements.homeDiscoverNote) {
      elements.homeDiscoverNote.innerHTML =
        `<span class="home-note-dot"></span>${escapeHtml(config.title)}界面已就绪，内容服务后续接入`;
    }
    elements.homeSections.innerHTML = `
      <section class="home-feature-shell" data-view="${escapeHtml(view)}">
        <div class="home-feature-head">
          <div>
            <div class="home-feature-eyebrow">${escapeHtml(config.eyebrow)}</div>
            <h2>${escapeHtml(config.title)}</h2>
            <p>${escapeHtml(config.copy)}</p>
          </div>
          <div class="home-feature-icon">${escapeHtml(config.icon)}</div>
        </div>
        <div class="home-feature-filters">
          ${config.chips
            .map((chip, index) => `<button class="home-feature-chip${index === 0 ? " active" : ""}" disabled>${escapeHtml(chip)}</button>`)
            .join("")}
        </div>
        <div class="home-feature-empty">
          <div class="home-feature-empty-visual">
            <span>${escapeHtml(config.icon)}</span>
          </div>
          <div class="home-empty-title">${escapeHtml(config.title)}即将可用</div>
          <div class="home-empty-copy">页面结构已经完成；接入对应接口后即可显示真实内容和操作状态。</div>
          <button class="btn-primary" id="btnHomeFeatureSearch">${escapeHtml(config.action)}</button>
        </div>
      </section>`;
    const searchBtn = document.getElementById("btnHomeFeatureSearch");
    if (searchBtn) {
      searchBtn.addEventListener("click", () => {
        if (typeof setPlatform === "function") setPlatform(plat);
        switchPage("page-search");
      });
    }
  }

  async function loadDiscover() {
    if (!elements.homeSections) return;
    const plat = state.discoverPlatform || "hongguo";
    const meta = PLATFORM_META[plat] || PLATFORM_META.hongguo;
    if (elements.homeDiscoverNote) {
      elements.homeDiscoverNote.innerHTML = `<span class="home-note-dot"></span>正在更新 ${escapeHtml(meta.short)} 内容`;
    }
    elements.homeSections.innerHTML = `
      <div class="home-loading" aria-label="正在加载 ${escapeHtml(meta.label)} 内容">
        <div class="home-loading-card"></div>
        <div class="home-loading-card"></div>
      </div>`;
    try {
      const data = await apiFetch(
        `/v1/discover?platform=${encodeURIComponent(plat)}&kinds=hot,new`,
        { timeoutMs: 15000 }
      );
      state.discoverData = data;
      renderDiscover(data);
    } catch (e) {
      elements.homeSections.innerHTML = `
        <div class="home-error">
          <div class="home-empty-icon">↻</div>
          <div class="home-error-title">内容暂时加载失败</div>
          <div class="home-error-copy">${escapeHtml(e.message)}</div>
          <div class="home-error-actions">
            <button class="btn-primary" id="btnHomeRetry">重新加载</button>
            <button class="btn-secondary" id="btnHomeGotoSearch">去资源搜索</button>
          </div>
        </div>`;
      if (elements.homeDiscoverNote) {
        elements.homeDiscoverNote.innerHTML = `<span class="home-note-dot"></span>服务连接异常，请稍后重试`;
      }
      const retryBtn = document.getElementById("btnHomeRetry");
      if (retryBtn) retryBtn.addEventListener("click", loadDiscover);
      const btn = document.getElementById("btnHomeGotoSearch");
      if (btn) btn.addEventListener("click", () => switchPage("page-search"));
    }
  }

  function renderDiscover(data) {
    if (!elements.homeSections) return;
    const plat = state.discoverPlatform || "hongguo";
    const meta = PLATFORM_META[plat] || PLATFORM_META.hongguo;

    // 服务端已按 platform 过滤；客户端再滤一次 items 的 platform 字段
    let sections = (data.sections || []).map((sec) => {
      const items = (sec.items || []).filter((it) => {
        if (!it.platform) return true;
        return platformOf(it) === plat;
      });
      return { ...sec, items };
    });

    const totalItems = sections.reduce((total, sec) => total + (sec.items || []).length, 0);
    if (elements.homeDiscoverNote) {
      elements.homeDiscoverNote.innerHTML = totalItems
        ? `<span class="home-note-dot"></span>已更新 ${escapeHtml(meta.short)} · 共 ${totalItems} 条内容`
        : `<span class="home-note-dot"></span>${escapeHtml(meta.short)}榜单正在准备中，资源搜索已可使用`;
    }

    if (!sections.length) {
      elements.homeSections.innerHTML = `
        <div class="home-error">
          <div class="home-empty-icon">${escapeHtml(meta.emoji)}</div>
          <div class="home-error-title">暂时没有发现内容</div>
          <div class="home-error-copy">可以先搜索感兴趣的作品，稍后再回来看看。</div>
          <div class="home-error-actions">
            <button class="btn-primary" id="btnHomeGotoSearch2">去资源搜索</button>
          </div>
        </div>`;
      const btn = document.getElementById("btnHomeGotoSearch2");
      if (btn) btn.addEventListener("click", () => switchPage("page-search"));
      return;
    }

    elements.homeSections.innerHTML = "";
    sections.forEach((sec) => {
      const box = document.createElement("div");
      box.className = "home-section";
      box.setAttribute("data-platform", plat);
      box.setAttribute("data-kind", sec.kind || "");
      const status = sec.available
        ? `${(sec.items || []).length} 条内容`
        : "即将上线";
      const sectionTitle = sec.title || (sec.kind === "hot" ? "🔥 热门榜单" : "✨ 今日上新");

      let body = "";
      if (sec.items && sec.items.length) {
        body = `<div class="home-grid">${sec.items
          .map((it) => {
            const p = platformOf(it) || plat;
            const m = PLATFORM_META[p] || meta;
            const title = displayTitle(it);
            const cover = it.cover
              ? `<img src="${escapeHtml(it.cover)}" alt="">`
              : `<span>${escapeHtml(m.emoji)}</span>`;
            const rank =
              it.rank != null
                ? `<span class="home-card-rank">${escapeHtml(String(it.rank))}</span>`
                : "";
            return `
              <div class="home-card" data-id="${escapeHtml(it.id)}" data-platform="${escapeHtml(p)}">
                <div class="home-card-cover">
                  ${rank}${cover}
                  <label class="home-card-select" title="选择 ${escapeHtml(title)}">
                    <input class="home-card-checkbox" type="checkbox" aria-label="选择 ${escapeHtml(title)}">
                    <span>✓</span>
                  </label>
                </div>
                <div class="home-card-body">
                  <div class="home-card-title">${escapeHtml(title)}</div>
                  <div class="home-card-footer">
                    <span class="source-badge ${escapeHtml(p)}">${escapeHtml(m.emoji)} ${escapeHtml(it.source_label || m.label)}</span>
                    <span class="home-card-open">查看 ›</span>
                  </div>
                </div>
              </div>`;
          })
          .join("")}</div>`;
      } else {
        const emptyTitle =
          sec.kind === "hot" ? `${meta.short}热榜正在准备中` : `${meta.short}上新内容正在准备中`;
        const emptyIcon = sec.kind === "hot" ? "🔥" : "✨";
        body = `
          <div class="home-empty">
            <div class="home-empty-icon">${emptyIcon}</div>
            <div class="home-empty-title">${escapeHtml(emptyTitle)}</div>
            <div class="home-empty-copy">发现内容更新前，可以通过资源搜索直接查找并下载作品。</div>
            <div><button class="btn-secondary btn-home-search-cta">搜索${escapeHtml(meta.short)}作品</button></div>
          </div>`;
      }
      box.innerHTML = `
        <div class="home-section-header">
          <div class="home-section-title">${escapeHtml(sectionTitle)}</div>
          <div class="home-section-status">${escapeHtml(status)}</div>
        </div>
        ${body}`;
      box.querySelectorAll(".home-card").forEach((card) => {
        const checkbox = card.querySelector(".home-card-checkbox");
        if (checkbox) {
          checkbox.addEventListener("click", (event) => event.stopPropagation());
          checkbox.addEventListener("change", () => {
            const id = card.getAttribute("data-id");
            const p = card.getAttribute("data-platform") || plat;
            const key = `${p}:${id}`;
            const item = (sec.items || []).find((candidate) => String(candidate.id) === String(id));
            if (checkbox.checked && item) {
              state.homeSelectedItems.set(key, { ...item, platform: p });
            } else {
              state.homeSelectedItems.delete(key);
            }
            card.classList.toggle("selected", checkbox.checked);
            updateHomeSelectionBar();
          });
        }
        card.addEventListener("click", () => {
          const id = card.getAttribute("data-id");
          const p = card.getAttribute("data-platform") || plat;
          state.selectedPlatform = p;
          switchPage("page-search");
          if (elements.searchRightPanel) elements.searchRightPanel.style.display = "flex";
          loadDetail(id, p);
        });
      });
      box.querySelectorAll(".btn-home-search-cta").forEach((btn) => {
        btn.addEventListener("click", () => {
          state.selectedPlatform = plat;
          // 同步侧栏平台 tab 到对应平台，便于后续搜索
          if (typeof setPlatform === "function") setPlatform(plat);
          switchPage("page-search");
        });
      });
      elements.homeSections.appendChild(box);
    });
  }

  function updateSelectedCountLabel() {
    if (elements.lblBtnDownloadSelected) {
      elements.lblBtnDownloadSelected.textContent = `下载指定剧集/章节 (已选 ${state.selectedEpisodes.size}项)`;
    }
  }

  // 6. 创建下载任务 (E2 VIP 403 与 429 诚实提示)
  async function createDownloadJob(rangeSpec) {
    if (!state.currentDetail) {
      toast("请先选择要下载的资源", "warning");
      return;
    }

    // 检查是否未登录
    if (!state.accessToken && (!state.apiKey || state.apiKey === "dev-key-change-me")) {
      toast("请先登录账号（商业路径）", "warning");
      openAuthModal("login");
      return;
    }

    const jobPlatform =
      platformOf(state.currentDetail && state.currentDetail.platform) ||
      state.selectedPlatform ||
      (state.platform !== "all" ? state.platform : "hongguo");
    const options = buildJobOptions();
    // 带上标题，任务列表展示用
    if (state.currentDetail && state.currentDetail.title) {
      options.title = state.currentDetail.title;
    }
    try {
      const res = await apiFetch("/v1/jobs", {
        method: "POST",
        body: JSON.stringify({
          platform: jobPlatform,
          id: state.currentDetail.id,
          range: rangeSpec,
          options,
        }),
      });

      toast(`下载任务已创建：${res.job_id}`, "success");
      if (res.job_id) state.watchedJobSuccess[res.job_id] = false;
      switchPage("page-jobs");
    } catch (e) {
      const msg = e.message || "";
      if (msg.includes("VIP") || msg.includes("403")) {
        toast(`VIP 不足：${msg}`, "warning", 4000);
        if (elements.modalRedeemKey) elements.modalRedeemKey.classList.add("active");
      } else if (msg.includes("配额") || msg.includes("quota")) {
        toast(`配额不足：${msg}`, "warning", 4000);
      } else if (msg.includes("频繁") || msg.includes("上限")) {
        toast(`创建受限：${msg}`, "warning");
      } else {
        toast(`任务创建失败：${msg}`, "error");
      }
    }
  }

  // 7. 动态任务列表与状态轮询
  async function refreshJobsPage() {
    try {
      const [summary, jobsRes] = await Promise.all([
        apiFetch("/v1/jobs/summary"),
        apiFetch("/v1/jobs?page=1&page_size=50"),
      ]);

      if (elements.statActiveJobs) elements.statActiveJobs.textContent = summary.active_jobs;
      if (elements.statCompletedJobs) elements.statCompletedJobs.textContent = summary.completed_jobs;
      if (elements.statTotalSpeed) elements.statTotalSpeed.textContent = summary.total_speed_human;
      if (elements.statDiskFree) elements.statDiskFree.textContent = summary.disk_free_human;
      if (elements.jobCountBadge) elements.jobCountBadge.textContent = summary.active_jobs;

      const jobs = jobsRes.items || [];
      renderJobsList(jobs);
      // 任务成功后按偏好打开目录（每个 job 只触发一次）
      if (state.prefs.openFolderOnComplete) {
        jobs.forEach((job) => {
          if (job.status === "success" && state.watchedJobSuccess[job.job_id] === false) {
            state.watchedJobSuccess[job.job_id] = true;
            const file = job.files && job.files.length > 0 ? job.files[0] : null;
            if (file) deliverFileLocal(file, "folder").catch(() => {});
          }
        });
      }
    } catch (e) {
      console.warn("刷新任务列表错误:", e);
    }
  }

  function renderJobsList(jobs) {
    if (!elements.jobsList) return;
    elements.jobsList.innerHTML = "";

    if (jobs.length === 0) {
      elements.jobsList.innerHTML = `
        <div style="text-align: center; padding: 40px; color: var(--text-muted);">
          暂无下载任务，请在资源搜索页面新建任务。
        </div>
      `;
      return;
    }

    jobs.forEach((job) => {
      const card = document.createElement("div");
      card.className = "job-item-card";
      const isHongguo = job.platform === "hongguo";
      const isSuccess = job.status === "success";
      const isFailed = job.status === "failed";
      const isCancelled = job.status === "cancelled";
      const isRunning = job.status === "running" || job.status === "pending";

      let statusBadge = escapeHtml(jobStatusLabel(job));
      if (isSuccess) statusBadge = `✅ ${statusBadge}`;
      else if (isFailed) statusBadge = `❌ ${statusBadge}`;
      else if (isCancelled) statusBadge = `⏹️ ${statusBadge}`;

      const progressPct = Math.min(100, Math.max(0, job.progress || 0));

      card.innerHTML = `
        <div class="job-item-info" style="width: 100%;">
          <div class="job-item-header">
            <span class="job-item-title">${isHongguo ? '🔴' : '🍅'} ${escapeHtml((job.extra && job.extra.title) || job.item_id)} <span style="opacity:.65;font-weight:500">[${escapeHtml(job.platform)} · ${escapeHtml(job.item_id)}]</span></span>
            <span class="job-item-speed">${isSuccess ? '✅ 完成' : isFailed ? '❌ 失败' : isRunning ? '⚡ 进行中' : '已停止'}</span>
          </div>
          <div class="job-progress-bar-bg">
            <div class="job-progress-bar-fill" style="width: ${progressPct}%; ${isSuccess ? 'background: var(--color-success);' : isFailed ? 'background: var(--color-danger, #ef4444);' : ''}"></div>
          </div>
          <div class="job-item-footer">
            <span>${statusBadge}</span>
            <div class="job-controls">
              ${isRunning ? `<button class="btn-secondary btn-cancel-job" data-id="${job.job_id}">✕ 取消</button>` : ''}
              ${isSuccess && job.files.length > 0 ? `<button class="btn-primary btn-download-local">⬇️ 下载到本机</button>` : ''}
              ${isSuccess && job.files.length > 0 ? `<button class="btn-secondary btn-open-media">▶️ 下载并打开</button>` : ''}
              ${isSuccess && job.files.length > 0 ? `<button class="btn-secondary btn-open-job-folder">📂 本机目录</button>` : ''}
            </div>
          </div>
        </div>
      `;

      const btnCancel = card.querySelector(".btn-cancel-job");
      if (btnCancel) {
        btnCancel.addEventListener("click", async () => {
          try {
            await apiFetch(`/v1/jobs/${job.job_id}`, { method: "DELETE" });
            refreshJobsPage();
          } catch (err) {
            toast(`取消任务失败: ${err.message}`, "error");
          }
        });
      }

      const btnDownloadLocal = card.querySelector(".btn-download-local");
      if (btnDownloadLocal) {
        btnDownloadLocal.addEventListener("click", () => {
          deliverFileLocal(job.files[0], "download").catch(() => {});
        });
      }

      const btnOpenMedia = card.querySelector(".btn-open-media");
      if (btnOpenMedia) {
        btnOpenMedia.addEventListener("click", () => {
          deliverFileLocal(job.files[0], "play").catch(() => {});
        });
      }

      const btnOpenFolder = card.querySelector(".btn-open-job-folder");
      if (btnOpenFolder) {
        btnOpenFolder.addEventListener("click", () => {
          deliverFileLocal(job.files[0], "folder").catch(() => {});
        });
      }

      elements.jobsList.appendChild(card);
    });
  }

  function startJobsPolling() {
    stopJobsPolling();
    state.jobsPollTimer = setInterval(refreshJobsPage, 3000);
  }

  function stopJobsPolling() {
    if (state.jobsPollTimer) {
      clearInterval(state.jobsPollTimer);
      state.jobsPollTimer = null;
    }
  }

  // 8. 加载与过滤本地媒体库 (/v1/files)
  async function loadLocalFiles() {
    try {
      const data = await apiFetch("/v1/files");
      state.libraryFiles = data.items || [];
      renderLibraryGrid();
    } catch (e) {
      toast(`加载本地资源失败: ${e.message}`, "error");
    }
  }

  function renderLibraryGrid() {
    if (!elements.libraryGrid) return;
    elements.libraryGrid.innerHTML = "";

    let files = state.libraryFiles;

    // 过滤类型
    if (state.libraryFilter === "hongguo") {
      files = files.filter((f) => f.media_type === "video/mp4" || f.platform === "hongguo");
    } else if (state.libraryFilter === "fanqie") {
      files = files.filter((f) => f.media_type === "text/plain" || f.platform === "fanqie");
    }

    // 搜索关键字
    if (state.librarySearch) {
      const q = state.librarySearch.toLowerCase();
      files = files.filter((f) => f.title.toLowerCase().includes(q) || f.file_id.toLowerCase().includes(q));
    }

    if (files.length === 0) {
      elements.libraryGrid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 60px; color: var(--text-muted);">
          暂无可下载的已完成文件，或没有匹配当前筛选条件。
        </div>
      `;
      return;
    }

    files.forEach((file) => {
      const isVideo = file.media_type === "video/mp4";
      const card = document.createElement("div");
      card.className = "media-card-item";
      card.innerHTML = `
        <div class="media-thumb-wrapper">
          <span class="media-type-tag" style="${isVideo ? '' : 'background: var(--color-fanqie);'}">${isVideo ? '🔴 MP4' : '🍅 TXT'}</span>
          <div class="media-placeholder" aria-hidden="true">${isVideo ? '🎬' : '📖'}</div>
        </div>
        <div class="media-body">
          <div>
            <div class="media-title">${escapeHtml(file.title)}</div>
            <div class="media-meta">大小: ${escapeHtml(file.size_human)}</div>
          </div>
          <div class="media-actions">
            <button class="btn-primary btn-deliver-media" data-action="download">⬇️ 下载到本机</button>
            <button class="btn-secondary btn-deliver-media" data-action="play">${isVideo ? '▶️ 下载并播放' : '📖 下载并阅读'}</button>
            <button class="btn-secondary btn-deliver-media" data-action="folder">📂 本机目录</button>
          </div>
        </div>
      `;

      card.querySelectorAll(".btn-deliver-media").forEach((btn) => {
        btn.addEventListener("click", () => {
          deliverFileLocal(file, btn.getAttribute("data-action")).catch(() => {});
        });
      });

      elements.libraryGrid.appendChild(card);
    });
  }

  async function openLocalDownloadDirectory() {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.open_download_directory) {
      const result = await window.pywebview.api.open_download_directory();
      if (!result || !result.success) {
        toast((result && result.message) || "无法打开本机下载目录", "error");
      }
      return;
    }
    toast("浏览器模式的文件位于浏览器默认下载目录", "info", 4000);
  }

  async function syncNativeDownloadDirectory() {
    if (!(window.pywebview && window.pywebview.api && window.pywebview.api.get_download_directory)) {
      if (elements.btnChooseOutputDir) elements.btnChooseOutputDir.disabled = true;
      if (elements.settingOutputDir) elements.settingOutputDir.value = "由浏览器管理下载目录";
      return;
    }
    if (window.pywebview.api.get_runtime_info) {
      const runtime = await window.pywebview.api.get_runtime_info();
      if (runtime && runtime.success && runtime.api_base) {
        state.nativeApiBase = runtime.api_base;
        state.apiBase = runtime.api_base;
        localStorage.removeItem("apiBase");
        if (elements.settingApiBase) {
          elements.settingApiBase.value = runtime.api_base;
          elements.settingApiBase.readOnly = true;
        }
      }
    }
    const result = await window.pywebview.api.get_download_directory();
    if (result && result.success && result.path) {
      state.prefs.outputDir = result.path;
      if (elements.settingOutputDir) elements.settingOutputDir.value = result.path;
    }
  }

  // 9. 检查软件版本更新 (/v1/version)
  async function checkVersion() {
    try {
      const data = await apiFetch("/v1/version");
      toast(`版本 ${data.latest_version}：${data.release_notes || "无说明"}`, "info", 4000);
    } catch (e) {
      toast(`检查版本失败: ${e.message}`, "error");
    }
  }

  // 10. 检查服务端健康状态 + 依赖完整性 UI
  function renderDepsList(container, checks, opts) {
    if (!container) return;
    container.innerHTML = "";
    const onlyFail = opts && opts.onlyFail;
    let list = checks || [];
    if (onlyFail) {
      list = list.filter((c) => !c.ok);
    }
    if (!list.length) {
      container.innerHTML = onlyFail
        ? `<li style="color: var(--color-success);">全部依赖就绪</li>`
        : `<li style="color: var(--text-muted);">无检查项</li>`;
      return;
    }
    list.forEach((c) => {
      const li = document.createElement("li");
      const ok = !!c.ok;
      const required = c.required !== false;
      let iconClass = "dep-ok";
      let icon = "✓";
      if (!ok) {
        icon = required ? "✗" : "!";
        iconClass = required ? "dep-fail" : "dep-optional-fail";
      }
      const msg = c.message || (ok ? "就绪" : "未就绪");
      const hints =
        !ok && c.hints && c.hints.length
          ? `<div class="dep-msg">${escapeHtml(c.hints[0])}</div>`
          : "";
      li.innerHTML = `
        <span class="dep-icon ${iconClass}">${icon}</span>
        <span class="dep-body">
          <span class="dep-label">${escapeHtml(c.label || c.key || "")}</span>
          <span class="dep-msg"> — ${escapeHtml(msg)}</span>
          ${hints}
        </span>
      `;
      if (!ok && c.hints && c.hints.length) {
        li.title = c.hints.join("\n");
      }
      container.appendChild(li);
    });
  }

  function applyHealthToUI(data) {
    state.lastHealth = data;
    const verStr = data.version || "1.0.0";
    const status = (data.status || "ok").toLowerCase();
    const summary = data.summary || "";
    const checks = data.checks || [];

    if (elements.titlebarVersionTag) elements.titlebarVersionTag.textContent = `v${verStr}`;
    if (elements.settingAppVersionVal) elements.settingAppVersionVal.textContent = `v${verStr}-desktop`;

    let statusText = `服务正常 (v${verStr})`;
    let dotClass = "";
    if (status === "degraded") {
      const failCount = checks.filter((c) => !c.ok && c.required !== false).length;
      statusText = `依赖降级 (v${verStr})` + (failCount ? ` · ${failCount}项` : "");
      dotClass = "degraded";
    } else if (status === "error") {
      statusText = `服务异常 (v${verStr})`;
      dotClass = "error";
    }

    if (elements.serverStatusText) elements.serverStatusText.textContent = statusText;
    if (elements.serverStatusDot) {
      elements.serverStatusDot.classList.remove("degraded", "error");
      if (dotClass) elements.serverStatusDot.classList.add(dotClass);
      elements.serverStatusDot.style.backgroundColor = "";
    }

    if (elements.depsSummary) {
      elements.depsSummary.textContent = summary || "";
    }
    // 侧栏只展示失败项，避免挤占导航
    renderDepsList(elements.depsList, checks, { onlyFail: true });

    // 设置页完整列表
    if (elements.settingHealthStatus) {
      const color =
        status === "ok"
          ? "var(--color-success)"
          : status === "degraded"
            ? "var(--color-warning)"
            : "var(--color-error)";
      elements.settingHealthStatus.textContent =
        status === "ok" ? `正常 (v${verStr})` : status === "degraded" ? `降级 (v${verStr})` : `异常 (v${verStr})`;
      elements.settingHealthStatus.style.color = color;
    }
    if (elements.settingHealthSummary) {
      elements.settingHealthSummary.textContent = summary || "无摘要";
    }
    renderDepsList(elements.settingDepsList, checks, { onlyFail: false });

    // 有缺失时默认展开侧栏依赖面板一次
    if (status !== "ok" && elements.depsPanel && !state.depsPanelOpen) {
      elements.depsPanel.style.display = "block";
      state.depsPanelOpen = true;
    } else if (status === "ok" && elements.depsPanel && state.depsPanelOpen) {
      // 全部就绪时收起，减少干扰
      elements.depsPanel.style.display = "none";
      state.depsPanelOpen = false;
    }
  }

  async function checkServerHealth() {
    try {
      const data = await apiFetch("/health");
      applyHealthToUI(data);
    } catch (e) {
      if (elements.serverStatusText) {
        elements.serverStatusText.textContent = "服务不可达";
      }
      if (elements.serverStatusDot) {
        elements.serverStatusDot.classList.remove("degraded");
        elements.serverStatusDot.classList.add("error");
        elements.serverStatusDot.style.backgroundColor = "";
      }
      if (elements.settingHealthStatus) {
        elements.settingHealthStatus.textContent = "服务不可达";
        elements.settingHealthStatus.style.color = "var(--color-error)";
      }
      if (elements.settingHealthSummary) {
        elements.settingHealthSummary.textContent = String(e.message || e);
      }
      if (elements.depsList) {
        elements.depsList.innerHTML = `<li class="dep-fail">无法连接 ${escapeHtml(state.apiBase)}</li>`;
      }
      if (elements.settingDepsList) {
        elements.settingDepsList.innerHTML = `<li class="dep-fail">无法连接 ${escapeHtml(state.apiBase)}</li>`;
      }
    }
  }

  // 11. 初始化与事件绑定
  document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initSettingsForm();
    setPlatform(state.platform);

    // 拉取当前用户登录态
    fetchMe();
    // 默认首页发现
    loadDiscover();

    if (elements.themeToggleBtn) {
      elements.themeToggleBtn.addEventListener("click", () => setTheme(state.theme === "dark" ? "light" : "dark"));
    }

    elements.platformTabs.forEach((tab) => {
      tab.addEventListener("click", () => setPlatform(tab.getAttribute("data-platform")));
    });

    elements.navItems.forEach((nav) => {
      nav.addEventListener("click", () => switchPage(nav.getAttribute("data-page")));
    });

    if (elements.btnSearch) elements.btnSearch.addEventListener("click", doSearch);
    if (elements.inputSearchQuery) {
      elements.inputSearchQuery.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          doSearch();
        }
      });
    }

    if (elements.searchFilterChips) {
      elements.searchFilterChips.forEach((chip) => {
        chip.addEventListener("click", () => {
          const f = chip.getAttribute("data-filter") || "all";
          state.searchFilter = f;
          elements.searchFilterChips.forEach((c) => {
            c.classList.toggle("active", c.getAttribute("data-filter") === f);
          });
          applySearchFilter();
        });
      });
    }

    // 首页
    if (elements.btnHomeSearch) {
      elements.btnHomeSearch.addEventListener("click", () => {
        const q = elements.homeSearchQuery ? elements.homeSearchQuery.value.trim() : "";
        goSearchWithQuery(q);
      });
    }
    if (elements.homeSearchQuery) {
      elements.homeSearchQuery.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          const q = elements.homeSearchQuery.value.trim();
          goSearchWithQuery(q);
        }
      });
    }
    if (elements.btnRefreshDiscover) {
      elements.btnRefreshDiscover.addEventListener("click", () => {
        if (state.discoverView === "discover") loadDiscover();
        else renderHomeFeatureView(state.discoverView);
      });
    }
    elements.homeModeTabs.forEach((tab) => {
      tab.addEventListener("click", () => setDiscoverView(tab.getAttribute("data-view") || "discover"));
    });
    if (elements.homePlatformTabs) {
      elements.homePlatformTabs.forEach((tab) => {
        tab.addEventListener("click", () => {
          setDiscoverPlatform(tab.getAttribute("data-platform") || "hongguo");
        });
      });
      // 同步初始 active
      elements.homePlatformTabs.forEach((tab) => {
        tab.classList.toggle(
          "active",
          tab.getAttribute("data-platform") === (state.discoverPlatform || "hongguo")
        );
      });
    }
    if (elements.btnHomeClearSelection) {
      elements.btnHomeClearSelection.addEventListener("click", () => {
        state.homeSelectedItems.clear();
        syncHomeCardSelections();
        updateHomeSelectionBar();
      });
    }
    if (elements.btnHomeSelectAll) {
      elements.btnHomeSelectAll.addEventListener("click", () => {
        document.querySelectorAll(".home-card").forEach((card) => {
          const id = card.getAttribute("data-id");
          const p = card.getAttribute("data-platform") || state.discoverPlatform;
          const key = `${p}:${id}`;
          const item = (state.discoverData?.sections || [])
            .flatMap((section) => section.items || [])
            .find((candidate) => String(candidate.id) === String(id));
          if (item) state.homeSelectedItems.set(key, { ...item, platform: p });
        });
        syncHomeCardSelections();
        updateHomeSelectionBar();
      });
    }
    if (elements.btnHomeAddQueue) {
      elements.btnHomeAddQueue.addEventListener("click", () => {
        toast(`已选择 ${state.homeSelectedItems.size} 项；批量队列接口接入后即可提交`, "info", 4500);
      });
    }

    if (elements.btnLoad) {
      elements.btnLoad.addEventListener("click", () => {
        const query = elements.inputSearchQuery.value.trim();
        if (!query) {
          toast("请输入要载入的资源 ID 或 URL", "warning");
          return;
        }
        if (elements.searchRightPanel) elements.searchRightPanel.style.display = "flex";
        const plat =
          state.platform === "fanqie" || state.platform === "hongguo"
            ? state.platform
            : state.selectedPlatform || "hongguo";
        state.selectedPlatform = plat;
        loadDetail(query, plat);
      });
    }

    if (elements.serverStatusBlock) {
      elements.serverStatusBlock.addEventListener("click", () => {
        state.depsPanelOpen = !state.depsPanelOpen;
        if (elements.depsPanel) {
          elements.depsPanel.style.display = state.depsPanelOpen ? "block" : "none";
        }
      });
    }
    if (elements.btnRefreshHealth) {
      elements.btnRefreshHealth.addEventListener("click", () => checkServerHealth());
    }

    if (elements.btnCheckUpdate) elements.btnCheckUpdate.addEventListener("click", checkVersion);

    if (elements.btnDownloadAll) {
      elements.btnDownloadAll.addEventListener("click", () => createDownloadJob("all"));
    }
    if (elements.btnDownloadSelected) {
      elements.btnDownloadSelected.addEventListener("click", () => {
        const selectedArr = Array.from(state.selectedEpisodes).sort((a, b) => a - b);
        createDownloadJob(selectedArr.join(",") || "all");
      });
    }

    // 账号 Login / Logout 事件绑定
    if (elements.btnOpenAuthModal) {
      elements.btnOpenAuthModal.addEventListener("click", () => openAuthModal("login"));
    }
    if (elements.settingBtnAuthModal) {
      elements.settingBtnAuthModal.addEventListener("click", () => openAuthModal("login"));
    }
    if (elements.btnAuthModalClose) {
      elements.btnAuthModalClose.addEventListener("click", closeAuthModal);
    }
    if (elements.tabAuthLogin) {
      elements.tabAuthLogin.addEventListener("click", () => setAuthTab("login"));
    }
    if (elements.tabAuthRegister) {
      elements.tabAuthRegister.addEventListener("click", () => setAuthTab("register"));
    }
    if (elements.btnAuthSubmit) {
      elements.btnAuthSubmit.addEventListener("click", doAuthSubmit);
    }
    if (elements.btnLogoutBtn) {
      elements.btnLogoutBtn.addEventListener("click", doLogout);
    }
    if (elements.settingBtnLogout) {
      elements.settingBtnLogout.addEventListener("click", doLogout);
    }

    // 设置页：pill / 命名预览 / 开发者折叠
    if (elements.settingQualityPills) {
      elements.settingQualityPills.forEach((btn) => {
        btn.addEventListener("click", () => {
          const q = btn.getAttribute("data-quality") || "1080p";
          state.prefs.quality = q;
          elements.settingQualityPills.forEach((b) => {
            b.classList.toggle("active", b.getAttribute("data-quality") === q);
          });
          if (elements.selectQuality) elements.selectQuality.value = q;
        });
      });
    }
    if (elements.settingNumberStylePills) {
      elements.settingNumberStylePills.forEach((btn) => {
        btn.addEventListener("click", () => {
          const s = btn.getAttribute("data-style") || "01";
          state.prefs.numberStyle = s;
          elements.settingNumberStylePills.forEach((b) => {
            b.classList.toggle("active", b.getAttribute("data-style") === s);
          });
          updateNamePreview();
        });
      });
    }
    ["settingNameUsePrefix", "settingNameIncludeTitle", "settingNameUseSuffix", "settingNameSeparator"].forEach((id) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.addEventListener("change", () => {
        readPrefsFromForm();
        updateNamePreview();
      });
      el.addEventListener("input", () => {
        readPrefsFromForm();
        updateNamePreview();
      });
    });
    if (elements.btnToggleDevSettings && elements.devSettingsBody) {
      elements.btnToggleDevSettings.addEventListener("click", () => {
        const body = elements.devSettingsBody;
        const open = body.style.display !== "none";
        body.style.display = open ? "none" : "block";
      });
    }

    // 设置页面保存与重置绑定
    if (elements.btnSaveSettings) {
      elements.btnSaveSettings.addEventListener("click", () => {
        const candidateBase = elements.settingApiBase && elements.settingApiBase.value.trim();
        if (state.nativeApiBase && candidateBase && candidateBase !== state.nativeApiBase) {
          toast("桌面客户端的服务端地址由安装配置固定，不能在页面内切换", "error", 4500);
          return;
        }
        if (candidateBase && !isSecureApiBase(candidateBase)) {
          toast("远程服务端必须使用 HTTPS；HTTP 仅允许 127.0.0.1/localhost", "error", 5000);
          return;
        }
        readPrefsFromForm();
        persistPrefs();
        // 开发者选项：仅在表单有值时覆盖
        if (candidateBase) {
          state.apiBase = candidateBase;
          localStorage.setItem("apiBase", state.apiBase);
        }
        if (elements.settingApiKey) {
          state.apiKey = elements.settingApiKey.value.trim() || defaultApiKeyFor(state.apiBase);
          if (state.apiKey) localStorage.setItem("apiKey", state.apiKey);
          else localStorage.removeItem("apiKey");
        }
        if (elements.selectQuality && state.prefs.quality) {
          elements.selectQuality.value = state.prefs.quality;
        }
        toast("设置已保存", "success");
        checkServerHealth();
      });
    }

    if (elements.btnResetApiKey) {
      elements.btnResetApiKey.addEventListener("click", () => {
        state.apiKey = defaultApiKeyFor(state.apiBase);
        localStorage.removeItem("apiKey");
        if (elements.settingApiKey) elements.settingApiKey.value = state.apiKey;
        toast(state.apiKey ? "已恢复本机开发 Key" : "已清除运维 API Key", "info");
      });
    }

    if (elements.btnResetSettings) {
      elements.btnResetSettings.addEventListener("click", () => {
        // 恢复下载偏好默认；API 回同源
        try {
          if (location.origin && location.protocol.startsWith("http")) {
            state.apiBase = location.origin;
          } else {
            state.apiBase = "http://127.0.0.1:8000";
          }
        } catch (_) {
          state.apiBase = "http://127.0.0.1:8000";
        }
        state.apiKey = defaultApiKeyFor(state.apiBase);
        localStorage.removeItem("apiBase");
        localStorage.removeItem("apiKey");
        state.prefs = {
          outputDir: "",
          rememberOutputDir: true,
          quality: "1080p",
          rememberQuality: true,
          openFolderOnComplete: false,
          downloadCover: false,
          downloadDesc: false,
          concurrency: 2,
          nameUsePrefix: true,
          nameIncludeTitle: true,
          nameUseSuffix: false,
          numberStyle: "01",
          nameSeparator: ".",
        };
        [
          "pref_outputDir",
          "pref_rememberOutputDir",
          "pref_quality",
          "pref_rememberQuality",
          "pref_openFolderOnComplete",
          "pref_downloadCover",
          "pref_downloadDesc",
          "pref_concurrency",
          "pref_nameUsePrefix",
          "pref_nameIncludeTitle",
          "pref_nameUseSuffix",
          "pref_numberStyle",
          "pref_nameSeparator",
        ].forEach((k) => localStorage.removeItem(k));
        initSettingsForm();
        toast("设置已恢复默认", "info");
        checkServerHealth();
      });
    }

    if (elements.btnOpenOutputDir) {
      elements.btnOpenOutputDir.addEventListener("click", () => {
        openLocalDownloadDirectory();
      });
    }

    if (elements.btnLibraryOpenDir) {
      elements.btnLibraryOpenDir.addEventListener("click", () => {
        openLocalDownloadDirectory();
      });
    }

    if (elements.btnChooseOutputDir) {
      elements.btnChooseOutputDir.addEventListener("click", async () => {
        if (!(window.pywebview && window.pywebview.api && window.pywebview.api.choose_download_directory)) {
          toast("浏览器模式下请在浏览器设置中修改下载目录", "info", 4000);
          return;
        }
        const result = await window.pywebview.api.choose_download_directory();
        if (result && result.success) {
          state.prefs.outputDir = result.path;
          if (elements.settingOutputDir) elements.settingOutputDir.value = result.path;
          persistPrefs();
          toast(`本机保存目录已更新：${result.path}`, "success", 4000);
        } else if (!(result && result.cancelled)) {
          toast((result && result.message) || "选择目录失败", "error");
        }
      });
    }

    // VIP 卡密兑换弹窗 (E2 硬约束: success===true 才能关弹窗并刷新 me)
    if (elements.btnRedeemKey) {
      elements.btnRedeemKey.addEventListener("click", () => {
        if (!state.accessToken) {
          if (confirm("请先登录账号后再兑换 VIP 卡密。是否立即登录？")) {
            openAuthModal("login");
          }
          return;
        }
        if (elements.redeemErrorMessage) elements.redeemErrorMessage.style.display = "none";
        elements.modalRedeemKey.classList.add("active");
      });
    }
    if (elements.btnModalClose) {
      elements.btnModalClose.addEventListener("click", () => elements.modalRedeemKey.classList.remove("active"));
    }
    if (elements.btnModalSubmit) {
      elements.btnModalSubmit.addEventListener("click", async () => {
        const key = elements.inputCardKey.value.trim();
        if (!key) {
          showRedeemError("卡密序列号不能为空！");
          return;
        }

        elements.btnModalSubmit.disabled = true;
        if (elements.redeemErrorMessage) elements.redeemErrorMessage.style.display = "none";

        try {
          const res = await apiFetch("/v1/auth/redeem", {
            method: "POST",
            body: JSON.stringify({ card_code: key }),
          });

          // 硬约束: success === true 才能关弹窗并刷新 me
          if (res && res.success === true) {
            elements.modalRedeemKey.classList.remove("active");
            elements.inputCardKey.value = "";
            await fetchMe();
            toast(res.message || "卡密兑换成功", "success", 4000);
          } else {
            showRedeemError(res.message || "卡密兑换失败，请核对卡密后重试！");
          }
        } catch (e) {
          showRedeemError(`卡密兑换失败: ${e.message}`);
        } finally {
          elements.btnModalSubmit.disabled = false;
        }
      });
    }

    function showRedeemError(msg) {
      if (elements.redeemErrorMessage) {
        elements.redeemErrorMessage.textContent = msg;
        elements.redeemErrorMessage.style.display = "block";
      } else {
        toast(msg, "error");
      }
    }

    // 本地资源库过滤绑定
    if (elements.libraryFilterTabs) {
      elements.libraryFilterTabs.forEach((tab, index) => {
        tab.addEventListener("click", () => {
          elements.libraryFilterTabs.forEach((t) => t.classList.remove("active"));
          tab.classList.add("active");
          state.libraryFilter = index === 1 ? "hongguo" : index === 2 ? "fanqie" : "all";
          renderLibraryGrid();
        });
      });
    }

    if (elements.librarySearchInput) {
      elements.librarySearchInput.addEventListener("input", (e) => {
        state.librarySearch = e.target.value.trim();
        renderLibraryGrid();
      });
    }

    checkServerHealth();
    setInterval(checkServerHealth, 10000);
    syncNativeDownloadDirectory().catch(() => {});
  });

  window.addEventListener("pywebviewready", () => {
    syncNativeDownloadDirectory().catch(() => {});
  });
})();
