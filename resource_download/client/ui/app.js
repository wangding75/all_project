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
    // T28 activation-first: normal business requests carry no User/JWT/API key.
    apiKey: "",
    accessToken: "",
    nativeApiBase: "",
    user: null,
    licenseContext: null,
    licenseStatusReason: "LICENSE_STATUS_UNKNOWN",
    currentDetail: null,
    searchResults: [],
    allSearchResults: [],
    searchFilter: "all",
    searchPage: 1,
    searchHasMore: false,
    lastSearchQuery: "",
    lastPlatformErrors: {},
    imageRecognizeData: "",
    batchResults: [],
    batchSelected: new Set(),
    batchResolving: false,
    selectedEpisodes: new Set(),
    downloadSubmitting: false,
    jobsPollTimer: null,
    queueState: null,
    jobs: [],
    jobsFilter: "all",
    jobsSelected: new Set(),
    hongguoMonitor: null,
    libraryFilter: "all",
    librarySearch: "",
    libraryFiles: [],
    lastHealth: null,
    depsPanelOpen: false,
    discoverPlatform: "hongguo",
    discoverView: "discover",
    discoverFilters: {
      genre: "short_play",
      sort: "hot_score",
      gender: "",
      days: "",
      theme: "",
      minEpisodes: 0,
    },
    discoverData: null,
    homeSelectedItems: new Map(),
    followingItems: (() => {
      try {
        const rows = JSON.parse(localStorage.getItem("followingItems") || "[]");
        return new Map(
          (Array.isArray(rows) ? rows : []).map((item) => [
            `${String(item.platform || "hongguo")}:${item.id}`,
            item,
          ])
        );
      } catch (_) {
        return new Map();
      }
    })(),
    currentSegments: [],
    episodePage: 1,
    clientVersion: "1.0.0",
    installId: "",
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
    btnOpenActivation: document.getElementById("btnOpenActivation"),
    licensePlanName: document.getElementById("licensePlanName"),
    licenseExpireStatus: document.getElementById("licenseExpireStatus"),
    licenseStatusReason: document.getElementById("licenseStatusReason"),

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
    homeAdvancedFilters: document.getElementById("homeAdvancedFilters"),
    homeFilterGenre: document.getElementById("homeFilterGenre"),
    homeFilterSort: document.getElementById("homeFilterSort"),
    homeFilterGender: document.getElementById("homeFilterGender"),
    homeFilterDays: document.getElementById("homeFilterDays"),
    homeFilterTheme: document.getElementById("homeFilterTheme"),
    homeFilterMinEpisodes: document.getElementById("homeFilterMinEpisodes"),
    btnApplyHomeFilters: document.getElementById("btnApplyHomeFilters"),
    btnResetHomeFilters: document.getElementById("btnResetHomeFilters"),

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
    imageRecognizeInput: document.getElementById("imageRecognizeInput"),
    imageRecognizePreview: document.getElementById("imageRecognizePreview"),
    imageRecognizeStatus: document.getElementById("imageRecognizeStatus"),
    btnRecognizeImage: document.getElementById("btnRecognizeImage"),

    // 批量导入页面
    batchInputText: document.getElementById("batchInputText"),
    batchFileInput: document.getElementById("batchFileInput"),
    batchPlatformHint: document.getElementById("batchPlatformHint"),
    batchInputCount: document.getElementById("batchInputCount"),
    btnBatchClear: document.getElementById("btnBatchClear"),
    btnBatchResolve: document.getElementById("btnBatchResolve"),
    batchProgress: document.getElementById("batchProgress"),
    batchProgressFill: document.getElementById("batchProgressFill"),
    batchProgressText: document.getElementById("batchProgressText"),
    batchResultSummary: document.getElementById("batchResultSummary"),
    batchResults: document.getElementById("batchResults"),
    btnBatchSelectSuccess: document.getElementById("btnBatchSelectSuccess"),
    btnBatchClearSelection: document.getElementById("btnBatchClearSelection"),
    btnBatchEnqueue: document.getElementById("btnBatchEnqueue"),

    // 详情面板
    searchRightPanel: document.getElementById("searchRightPanel"),
    detailSourceBadge: document.getElementById("detailSourceBadge"),
    detailBannerImg: document.getElementById("detailBannerImg"),
    detailTitle: document.getElementById("detailTitle"),
    detailEpCount: document.getElementById("detailEpCount"),
    detailPlatformLabel: document.getElementById("detailPlatformLabel"),
    detailId: document.getElementById("detailId"),
    detailSynopsis: document.getElementById("detailSynopsis"),
    btnToggleFollow: document.getElementById("btnToggleFollow"),
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
    btnQueuePause: document.getElementById("btnQueuePause"),
    btnRefreshJobs: document.getElementById("btnRefreshJobs"),
    queueStateText: document.getElementById("queueStateText"),
    jobsStatusFilter: document.getElementById("jobsStatusFilter"),
    btnJobsSelectVisible: document.getElementById("btnJobsSelectVisible"),
    btnJobsClearSelected: document.getElementById("btnJobsClearSelected"),
    jobsSelectedCount: document.getElementById("jobsSelectedCount"),
    jobsBulkButtons: document.querySelectorAll("[data-jobs-bulk]"),
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
    settingDeviceIdentityStatus: document.getElementById("settingDeviceIdentityStatus"),
    settingBtnAuthModal: document.getElementById("settingBtnAuthModal"),
    settingBtnLogout: document.getElementById("settingBtnLogout"),
    settingBtnActivate: document.getElementById("settingBtnActivate"),
    settingLicensePlan: document.getElementById("settingLicensePlan"),
    settingLicenseDevice: document.getElementById("settingLicenseDevice"),
    settingLicenseQuota: document.getElementById("settingLicenseQuota"),
    settingLicenseReason: document.getElementById("settingLicenseReason"),
    btnResetDeviceIdentity: document.getElementById("btnResetDeviceIdentity"),
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
    settingHgMonitorEnabled: document.getElementById("settingHgMonitorEnabled"),
    settingHgMonitorAutoQueue: document.getElementById("settingHgMonitorAutoQueue"),
    settingHgMonitorInterval: document.getElementById("settingHgMonitorInterval"),
    settingHgMonitorLimit: document.getElementById("settingHgMonitorLimit"),
    settingHgMonitorMinEpisodes: document.getElementById("settingHgMonitorMinEpisodes"),
    settingHgMonitorMaxEnqueue: document.getElementById("settingHgMonitorMaxEnqueue"),
    settingHgMonitorInclude: document.getElementById("settingHgMonitorInclude"),
    settingHgMonitorExclude: document.getElementById("settingHgMonitorExclude"),
    settingHgMonitorAuthors: document.getElementById("settingHgMonitorAuthors"),
    settingHgMonitorStatus: document.getElementById("settingHgMonitorStatus"),
    settingHgMonitorLogs: document.getElementById("settingHgMonitorLogs"),
    btnScanHgNewNow: document.getElementById("btnScanHgNewNow"),

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
    if (status === "paused") return "队列已暂停";
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

  function followingKey(item) {
    return `${platformOf(item)}:${String(item && item.id || "")}`;
  }

  function persistFollowing() {
    localStorage.setItem(
      "followingItems",
      JSON.stringify(Array.from(state.followingItems.values()))
    );
  }

  function isFollowing(item) {
    return !!(item && item.id && state.followingItems.has(followingKey(item)));
  }

  function toggleFollowing(item) {
    if (!item || !item.id) return false;
    const key = followingKey(item);
    if (state.followingItems.has(key)) {
      state.followingItems.delete(key);
    } else {
      const p = platformOf(item);
      state.followingItems.set(key, {
        id: String(item.id),
        title: displayTitle(item),
        cover: item.cover || "",
        author: item.author || "",
        desc: item.desc || "",
        platform: p,
        source_label: sourceLabelOf(item),
        extra: item.extra || {},
        last_seen_segments: Array.isArray(item.segments) ? item.segments.length : 0,
        followed_at: new Date().toISOString(),
      });
    }
    persistFollowing();
    updateFollowButton();
    return state.followingItems.has(key);
  }

  function updateFollowButton() {
    if (!elements.btnToggleFollow) return;
    const active = isFollowing(state.currentDetail);
    elements.btnToggleFollow.textContent = active ? "♥ 已追更" : "♡ 追更";
    elements.btnToggleFollow.classList.toggle("active", active);
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

  // This is intentionally the same business scope as server/app/license_guard.py.
  // Only the desktop bridge can sign these calls; a normal browser has no key.
  function isProtectedEndpoint(endpoint, method = "GET") {
    let path = endpoint;
    try {
      path = new URL(endpoint, state.apiBase).pathname;
    } catch (_) {}
    const verb = String(method || "GET").toUpperCase();
    if (/^\/v1\/jobs(?:\/.*)?$/.test(path)) return true;
    if (/^\/v1\/files(?:\/.*)?$/.test(path)) return true;
    if ([
      "/v1/search",
      "/v1/detail",
      "/v1/discover",
      "/v1/batch/resolve",
      "/v1/image/recognize",
      "/v1/hongguo/people",
      "/v1/license/status",
    ].includes(path)) return true;
    return path.startsWith("/v1/automation/hongguo-new");
  }

  const licenseReasonMessages = {
    DESKTOP_DEVICE_IDENTITY_REQUIRED: "此操作必须在正式桌面客户端中完成，普通浏览器没有设备私钥。",
    DEVICE_IDENTITY_INVALID: "设备身份损坏或无法验证。请在设置中执行“重置设备身份”，然后重新激活。",
    DEVICE_IDENTITY_STORAGE_UNAVAILABLE: "无法访问当前 Windows 用户的安全设备存储。",
    DEVICE_PROOF_REQUIRED: "设备身份需要重新建立/重新激活。",
    DEVICE_PROOF_INVALID: "设备身份验证失败，请重新激活。",
    DEVICE_PROOF_EXPIRED: "设备证明已过期，请重试。",
    DEVICE_PROOF_REPLAYED: "设备证明已被使用，请重试。",
    DEVICE_NOT_ACTIVATED: "当前设备尚未激活，请先兑换激活码。",
    LICENSE_EXPIRED: "License 已过期。",
    LICENSE_REVOKED: "License 已撤销，商业操作已停止。",
    DEVICE_REVOKED: "设备已撤销，商业操作已停止。",
    DEVICE_LIMIT_REACHED: "已达到 License 的设备数量上限。",
    PLAN_ENTITLEMENT_INVALID: "License 计划权益数据无效，请联系管理员。",
    INVALID_KEY: "激活码无效。",
    LICENSE_SERVICE_UNAVAILABLE: "License Service 暂时不可用，请稍后重试。",
    LICENSE_SERVICE_TIMEOUT: "License Service 暂时不可用，请稍后重试。",
  };

  function licenseReasonMessage(reason) {
    const key = String(reason || "");
    return licenseReasonMessages[key] || key || "请求失败，请稍后重试。";
  }

  function apiError(reason, status = 0) {
    const normalized = String(reason || "REQUEST_FAILED");
    const error = new Error(licenseReasonMessage(normalized));
    error.reason = normalized;
    error.status = status;
    error.userMessage = licenseReasonMessage(error.reason);
    return error;
  }

  function isDesktopBridge() {
    return !!(
      window.pywebview &&
      window.pywebview.api &&
      typeof window.pywebview.api.api_request === "function"
    );
  }

  function handleProtectedFailure(error, prefix = "请求失败") {
    const reason = String((error && error.reason) || "");
    const known = [
      "DESKTOP_DEVICE_IDENTITY_REQUIRED",
      "DEVICE_IDENTITY_INVALID",
      "DEVICE_IDENTITY_STORAGE_UNAVAILABLE",
      "DEVICE_PROOF_REQUIRED",
      "DEVICE_PROOF_INVALID",
      "DEVICE_PROOF_EXPIRED",
      "DEVICE_PROOF_REPLAYED",
      "DEVICE_NOT_ACTIVATED",
      "LICENSE_EXPIRED",
      "LICENSE_REVOKED",
      "DEVICE_REVOKED",
      "DEVICE_LIMIT_REACHED",
      "LICENSE_SERVICE_UNAVAILABLE",
      "LICENSE_SERVICE_TIMEOUT",
    ];
    if (!known.includes(reason)) return false;
    const needsActivation = reason === "DEVICE_NOT_ACTIVATED";
    toast(`${prefix}：${licenseReasonMessage(reason)}`, needsActivation ? "warning" : "error", 5500);
    if (needsActivation && elements.modalRedeemKey) {
      elements.modalRedeemKey.classList.add("active");
    }
    return true;
  }

  // 通用 REST Fetch 辅助函数 (E2 统一鉴权: Bearer token 优先; 无 token 时用 X-API-Key)
  // options.timeoutMs: 超时毫秒，默认 30000；搜索等可单独加长/缩短
  async function apiFetch(endpoint, options = {}) {
    const baseUrl = state.apiBase.replace(/\/+$/, "");
    const url = `${baseUrl}${endpoint}`;
    const timeoutMs = options.timeoutMs != null ? options.timeoutMs : 30000;
    const { timeoutMs: _tm, ...fetchOpts } = options;
    const method = String(fetchOpts.method || "GET").toUpperCase();

    if (isProtectedEndpoint(endpoint, method)) {
      if (!isDesktopBridge()) {
        throw apiError("DESKTOP_DEVICE_IDENTITY_REQUIRED");
      }
      let rawBody = fetchOpts.body;
      if (rawBody === undefined || rawBody === null) rawBody = "";
      if (typeof rawBody !== "string") rawBody = JSON.stringify(rawBody);
      const bridgeResult = await window.pywebview.api.api_request(
        method,
        endpoint,
        rawBody,
        state.accessToken || "",
        state.apiKey || "",
        (fetchOpts.headers && (fetchOpts.headers["Idempotency-Key"] || fetchOpts.headers["idempotency-key"])) || ""
      );
      if (!bridgeResult || bridgeResult.ok !== true) {
        const reason = (bridgeResult && (bridgeResult.reason || bridgeResult.detail)) || "REQUEST_FAILED";
        throw apiError(reason, (bridgeResult && bridgeResult.status) || 0);
      }
      return bridgeResult.data;
    }

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
      response = await fetch(url, { ...fetchOpts, method, headers, signal: controller.signal });
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
      const reason = typeof errorDetail === "string" ? errorDetail : JSON.stringify(errorDetail);
      throw apiError(reason, response.status);
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
    void file;
    throw new Error("DESKTOP_DEVICE_IDENTITY_REQUIRED");
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
  function renderLicenseContext(context, reason = "") {
    const data = context || {};
    const active = String(data.status || "").toUpperCase() === "ACTIVE";
    const plan = data.plan_code
      ? `${data.plan_code}${data.plan_version ? ` v${data.plan_version}` : ""}`
      : "License 未激活";
    const expiry = data.expires_at ? formatDate(data.expires_at) : "未激活";
    const device = data.device_id ? `Device ${String(data.device_id).slice(0, 16)}…` : "Device 未就绪";
    const quota = typeof data.used === "number" && typeof data.limit === "number"
      ? `${data.used} / ${data.limit}`
      : "—";
    const why = reason || data.reason || (active ? "ACTIVE" : "LICENSE_REQUIRED");
    if (elements.licensePlanName) elements.licensePlanName.textContent = plan;
    if (elements.licenseExpireStatus) elements.licenseExpireStatus.textContent = active ? expiry : why;
    if (elements.licenseStatusReason) elements.licenseStatusReason.textContent = why;
    if (elements.settingLicensePlan) elements.settingLicensePlan.textContent = plan;
    if (elements.settingLicenseDevice) elements.settingLicenseDevice.textContent = `${expiry} · ${device}`;
    if (elements.settingLicenseQuota) elements.settingLicenseQuota.textContent = quota;
    if (elements.settingLicenseReason) elements.settingLicenseReason.textContent = why;
    if (elements.vipUsername) elements.vipUsername.textContent = plan;
    if (elements.vipExpireDate) elements.vipExpireDate.textContent = active ? expiry : why;
    if (elements.settingQuotaVal) elements.settingQuotaVal.textContent = quota;
  }

  async function refreshLicenseStatus({ openActivation = true } = {}) {
    try {
      const status = await apiFetch("/v1/license/status");
      state.licenseContext = status;
      state.licenseStatusReason = status.reason || "ACTIVE";
      renderLicenseContext(status);
      if (elements.modalRedeemKey) elements.modalRedeemKey.classList.remove("active");
      return status;
    } catch (err) {
      state.licenseContext = null;
      state.licenseStatusReason = err.reason || err.message || "LICENSE_REQUIRED";
      renderLicenseContext(null, state.licenseStatusReason);
      if (openActivation && elements.modalRedeemKey && isDesktopBridge()) {
        elements.modalRedeemKey.classList.add("active");
      }
      return null;
    }
  }

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
    name += ".txt";
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
    if (elements.settingNameSeparator) elements.settingNameSeparator.value = p.nameSeparator || ".";
    if (elements.btnOpenActivation) {
      elements.btnOpenActivation.addEventListener("click", () => {
        if (elements.redeemErrorMessage) elements.redeemErrorMessage.style.display = "none";
        if (elements.modalRedeemKey) elements.modalRedeemKey.classList.add("active");
      });
    }
    if (elements.settingBtnActivate) {
      elements.settingBtnActivate.addEventListener("click", () => {
        if (elements.modalRedeemKey) elements.modalRedeemKey.classList.add("active");
      });
    }
    const legacyAccountCard = elements.settingUsernameVal && elements.settingUsernameVal.closest(".settings-card");
    if (legacyAccountCard) legacyAccountCard.style.display = "none";

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
      if (state.discoverView === "discover") loadDiscover();
      else renderHomeFeatureView(state.discoverView);
      stopJobsPolling();
    } else if (pageId === "page-library") {
      loadLocalFiles();
      stopJobsPolling();
    } else if (pageId === "page-jobs") {
      refreshJobsPage();
      startJobsPolling();
    } else if (pageId === "page-settings") {
      loadHongguoMonitor();
      stopJobsPolling();
    } else {
      stopJobsPolling();
    }
  }

  function goSearchWithQuery(q) {
    if (elements.inputSearchQuery) elements.inputSearchQuery.value = q || "";
    switchPage("page-search");
    if (q && String(q).trim()) doSearch();
  }

  function parseBatchInputs() {
    const raw = elements.batchInputText ? elements.batchInputText.value : "";
    const seen = new Set();
    const values = [];
    String(raw || "")
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .forEach((value) => {
        if (!seen.has(value)) {
          seen.add(value);
          values.push(value);
        }
      });
    return values;
  }

  function updateBatchInputCount() {
    const count = parseBatchInputs().length;
    if (elements.batchInputCount) elements.batchInputCount.textContent = String(count);
    return count;
  }

  function updateBatchSelection() {
    const selectedCount = state.batchSelected.size;
    if (elements.btnBatchEnqueue) {
      elements.btnBatchEnqueue.disabled = selectedCount === 0 || state.batchResolving;
      elements.btnBatchEnqueue.textContent = selectedCount
        ? `加入队列（${selectedCount}）`
        : "加入队列";
    }
    if (elements.batchResults) {
      elements.batchResults.querySelectorAll(".batch-result-check").forEach((checkbox) => {
        checkbox.checked = state.batchSelected.has(checkbox.getAttribute("data-key") || "");
      });
    }
  }

  function renderBatchResults() {
    if (!elements.batchResults) return;
    const rows = state.batchResults || [];
    const successCount = rows.filter((row) => !!row.content).length;
    const errorCount = rows.length - successCount;
    if (elements.batchResultSummary) {
      elements.batchResultSummary.textContent = rows.length
        ? `共 ${rows.length} 条 · 成功 ${successCount} · 失败 ${errorCount}`
        : "尚未识别";
    }
    if (!rows.length) {
      elements.batchResults.innerHTML = `
        <div class="batch-empty-state">
          <span>⌁</span>
          <strong>等待导入内容</strong>
          <p>识别成功后可在这里核对平台、标题和资源 ID。</p>
        </div>`;
      updateBatchSelection();
      return;
    }
    elements.batchResults.innerHTML = rows
      .map((row, index) => {
        const key = String(index);
        if (!row.content) {
          return `
            <div class="batch-result-row is-error">
              <input class="batch-result-check" type="checkbox" disabled aria-label="识别失败">
              <div class="batch-result-source">
                <strong title="${escapeHtml(row.input)}">${escapeHtml(row.input)}</strong>
                <span>原始输入</span>
              </div>
              <span class="batch-result-arrow">→</span>
              <div class="batch-result-target">
                <strong>${escapeHtml(row.message || "未找到对应资源")}</strong>
                <span>${escapeHtml(row.code || "NOT_FOUND")}</span>
              </div>
            </div>`;
        }
        const item = row.content;
        const platform = platformOf(item);
        const platformLabel = platform === "fanqie" ? "番茄小说" : "红果短剧";
        return `
          <div class="batch-result-row">
            <input class="batch-result-check" type="checkbox" data-key="${key}" aria-label="选择 ${escapeHtml(item.title)}">
            <div class="batch-result-source">
              <strong title="${escapeHtml(row.input)}">${escapeHtml(row.input)}</strong>
              <span>原始输入</span>
            </div>
            <span class="batch-result-arrow">→</span>
            <div class="batch-result-target">
              <strong title="${escapeHtml(item.title)}">${escapeHtml(item.title)}</strong>
              <span>ID ${escapeHtml(item.id)}${item.author ? ` · ${escapeHtml(item.author)}` : ""}</span>
            </div>
            <span class="batch-platform-tag">${platformLabel}</span>
          </div>`;
      })
      .join("");
    elements.batchResults.querySelectorAll(".batch-result-check[data-key]").forEach((checkbox) => {
      checkbox.addEventListener("change", () => {
        const key = checkbox.getAttribute("data-key") || "";
        if (checkbox.checked) state.batchSelected.add(key);
        else state.batchSelected.delete(key);
        updateBatchSelection();
      });
    });
    updateBatchSelection();
  }

  function setBatchProgress(done, total, label) {
    if (elements.batchProgress) elements.batchProgress.hidden = false;
    const ratio = total > 0 ? Math.min(100, Math.round((done / total) * 100)) : 0;
    if (elements.batchProgressFill) elements.batchProgressFill.style.width = `${ratio}%`;
    if (elements.batchProgressText) {
      elements.batchProgressText.textContent = label || `已处理 ${done} / ${total}`;
    }
  }

  async function resolveBatchInputs() {
    if (state.batchResolving) return;
    const inputs = parseBatchInputs();
    if (!inputs.length) {
      toast("请先输入剧名、书名、资源 ID 或分享链接", "warning");
      return;
    }
    if (inputs.length > 1000) {
      toast(`当前有 ${inputs.length} 条，请控制在 1000 条以内`, "warning", 4500);
      return;
    }
    state.batchResolving = true;
    state.batchResults = [];
    state.batchSelected.clear();
    if (elements.btnBatchResolve) {
      elements.btnBatchResolve.disabled = true;
      elements.btnBatchResolve.textContent = "识别中…";
    }
    renderBatchResults();
    const hint = elements.batchPlatformHint ? elements.batchPlatformHint.value : "all";
    try {
      for (let offset = 0; offset < inputs.length; offset += 100) {
        const chunk = inputs.slice(offset, offset + 100);
        setBatchProgress(offset, inputs.length, `正在识别 ${offset + 1}-${offset + chunk.length} 条`);
        const response = await apiFetch("/v1/batch/resolve", {
          method: "POST",
          body: JSON.stringify({ inputs: chunk, platform_hint: hint }),
        });
        const resolvedByInput = new Map(
          (response.items || []).map((row) => [String(row.input), row])
        );
        const errorsByInput = new Map(
          (response.errors || []).map((row) => [String(row.input), row])
        );
        chunk.forEach((input) => {
          const resolved = resolvedByInput.get(input);
          const error = errorsByInput.get(input);
          state.batchResults.push(
            resolved || error || {
              input,
              code: "EMPTY_RESPONSE",
              message: "服务端未返回识别结果",
            }
          );
        });
        setBatchProgress(
          Math.min(offset + chunk.length, inputs.length),
          inputs.length,
          `已处理 ${Math.min(offset + chunk.length, inputs.length)} / ${inputs.length}`
        );
        renderBatchResults();
      }
      state.batchResults.forEach((row, index) => {
        if (row.content) state.batchSelected.add(String(index));
      });
      renderBatchResults();
      const ok = state.batchSelected.size;
      toast(
        `批量识别完成：成功 ${ok} 条，失败 ${state.batchResults.length - ok} 条`,
        ok ? "success" : "warning",
        4500
      );
    } catch (error) {
      toast(`批量识别中断：${error.message}`, "error", 5000);
    } finally {
      state.batchResolving = false;
      if (elements.btnBatchResolve) {
        elements.btnBatchResolve.disabled = false;
        elements.btnBatchResolve.textContent = "开始识别";
      }
      updateBatchSelection();
    }
  }

  async function enqueueBatchResults() {
    const selected = Array.from(state.batchSelected)
      .map((key) => state.batchResults[Number(key)])
      .filter((row) => row && row.content);
    if (!selected.length) {
      toast("请先选择识别成功的资源", "warning");
      return;
    }
    if (elements.btnBatchEnqueue) {
      elements.btnBatchEnqueue.disabled = true;
      elements.btnBatchEnqueue.textContent = "正在入队…";
    }
    let created = 0;
    let skipped = 0;
    let failed = 0;
    try {
      for (let offset = 0; offset < selected.length; offset += 100) {
        const chunk = selected.slice(offset, offset + 100);
        const response = await apiFetch("/v1/jobs/batch", {
          method: "POST",
          body: JSON.stringify({
            items: chunk.map((row) => ({
              platform: platformOf(row.content),
              id: String(row.content.id),
              range: "all",
              options: {
                title: displayTitle(row.content),
                source: "batch_import",
                original_input: row.input,
              },
            })),
            queue_mode: "enqueue",
            duplicate_policy: "skip_completed",
          }),
        });
        created += (response.created || []).length;
        skipped += (response.skipped || []).length;
        failed += (response.errors || []).length;
      }
      toast(
        `批量入队完成：创建 ${created}，跳过 ${skipped}，失败 ${failed}`,
        failed ? "warning" : "success",
        5000
      );
      if (created) switchPage("page-jobs");
    } catch (error) {
      if (handleProtectedFailure(error, "批量加入队列失败")) return;
      toast(`批量加入队列失败：${error.message}`, "error", 5000);
    } finally {
      updateBatchSelection();
    }
  }

  async function recognizeSelectedImage() {
    if (!state.imageRecognizeData) {
      toast("请先上传封面或海报图片", "warning");
      return;
    }
    if (elements.btnRecognizeImage) {
      elements.btnRecognizeImage.disabled = true;
      elements.btnRecognizeImage.textContent = "比对中…";
    }
    if (elements.imageRecognizeStatus) {
      elements.imageRecognizeStatus.textContent = "正在读取热榜与上新封面并计算视觉相似度…";
    }
    renderSearchSkeleton();
    try {
      const platformHint = ["hongguo", "fanqie"].includes(state.platform)
        ? state.platform
        : "all";
      const response = await apiFetch("/v1/image/recognize", {
        method: "POST",
        body: JSON.stringify({
          image_base64: state.imageRecognizeData,
          platform_hint: platformHint,
          max_candidates: 6,
        }),
        timeoutMs: 90000,
      });
      state.allSearchResults = (response.candidates || []).map((candidate) => ({
        ...candidate.content,
        extra: {
          ...(candidate.content.extra || {}),
          recognition_score: candidate.score,
          recognition_confidence: candidate.confidence,
        },
      }));
      state.searchFilter = "all";
      state.searchHasMore = false;
      if (elements.btnLoadMore) elements.btnLoadMore.style.display = "none";
      applySearchFilter();
      const best = (response.candidates || [])[0];
      if (elements.imageRecognizeStatus) {
        elements.imageRecognizeStatus.textContent = best
          ? `已比对 ${response.compared_count || 0} 张封面，最高相似度 ${Math.round(best.score * 100)}%`
          : "没有可比对的可信封面，请尝试关键词搜索";
      }
      if (best) {
        setSearchBanner(
          best.confidence === "high"
            ? "找到高相似候选，请核对标题后打开详情。"
            : "已按相似度列出候选；当前没有高置信匹配，请人工核对。",
          best.confidence === "high" ? "info" : "warning"
        );
      } else {
        setSearchBanner("未找到可用候选封面，可改用剧名或书名搜索。", "warning");
      }
    } catch (error) {
      state.allSearchResults = [];
      state.searchResults = [];
      renderSearchResults([]);
      if (elements.imageRecognizeStatus) {
        elements.imageRecognizeStatus.textContent = `识别失败：${error.message}`;
      }
      toast(`图片识别失败：${error.message}`, "error", 5000);
    } finally {
      if (elements.btnRecognizeImage) {
        elements.btnRecognizeImage.disabled = !state.imageRecognizeData;
        elements.btnRecognizeImage.textContent = "识别图片";
      }
    }
  }

  // 4. 执行资源搜索（支持 platform=all 聚合 + 来源标记）
  async function doSearch(page, append) {
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
    const nextPage = Number(page) > 0 ? Number(page) : 1;
    const isAppend = !!append && query === state.lastSearchQuery;
    if (isAppend && elements.btnLoadMore) {
      elements.btnLoadMore.textContent = "加载中...";
      elements.btnLoadMore.disabled = true;
    } else {
      elements.btnSearch.textContent = "搜索中...";
      elements.btnSearch.disabled = true;
      setSearchBanner("正在搜索…（聚合时可能需等待签名环境）", "info");
      renderSearchSkeleton();
    }

    try {
      const platParam = state.platform || "all";
      const timeoutMs = platParam === "hongguo" ? 30000 : 45000;
      const data = await apiFetch(
        `/v1/search?platform=${encodeURIComponent(platParam)}&q=${encodeURIComponent(query)}&page=${nextPage}`,
        { timeoutMs }
      );
      const items = Array.isArray(data) ? data : (data.items || []);
      const platformErrors = Array.isArray(data) ? {} : (data.platform_errors || {});
      const platformStatus = Array.isArray(data) ? {} : (data.platform_status || {});
      if (isAppend) {
        const merged = [...state.allSearchResults];
        const seen = new Set(merged.map((item) => `${platformOf(item)}:${item.id}`));
        items.forEach((item) => {
          const key = `${platformOf(item)}:${item.id}`;
          if (!seen.has(key)) {
            seen.add(key);
            merged.push(item);
          }
        });
        state.allSearchResults = merged;
      } else {
        state.allSearchResults = items;
      }
      state.searchPage = nextPage;
      state.lastSearchQuery = query;
      state.searchHasMore = !!(data && data.has_more);
      if (elements.btnLoadMore) {
        elements.btnLoadMore.style.display = state.searchHasMore ? "" : "none";
      }
      state.lastPlatformErrors = platformErrors;
      state.searchFilter = "all";
      if (elements.searchFilterChips) {
        elements.searchFilterChips.forEach((c) => {
          c.classList.toggle("active", c.getAttribute("data-filter") === "all");
        });
      }
      applySearchFilter();

      const errKeys = Object.keys(platformErrors);
      if (state.allSearchResults.length > 0) {
        if (errKeys.length > 0) {
          const errHtml = errKeys
            .map((k) => `<div><b>${escapeHtml(platformStatus[k] || "UPSTREAM_UNAVAILABLE")}</b> · ${escapeHtml(k)}: ${escapeHtml(platformErrors[k])}</div>`)
            .join("");
          setSearchBanner(`部分平台失败，已展示可用结果：${errHtml}`, "warning");
          toast(`部分平台搜索失败：${errKeys.join("、")}`, "warning");
        } else {
          setSearchBanner("", "");
        }
        if (elements.searchRightPanel) elements.searchRightPanel.style.display = "flex";
        if (!isAppend) {
          const first = (state.searchResults && state.searchResults[0]) || items[0];
          state.selectedPlatform = platformOf(first);
          loadDetail(first.id, state.selectedPlatform);
        }
      } else {
        let msg = "EMPTY_RESULT: 未搜索到相关资源，请尝试更改关键词或使用「载入 ID」。";
        if (errKeys.length > 0) {
          const statuses = Object.values(platformStatus);
          msg = statuses.includes("RUNTIME_INCOMPATIBLE")
            ? "RUNTIME_INCOMPATIBLE: 平台运行环境版本不兼容，请修复 Frida 后重试。"
            : "UPSTREAM_UNAVAILABLE: 上游平台暂时不可用，请稍后重试。";
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
      state.searchHasMore = false;
      if (elements.btnLoadMore) elements.btnLoadMore.style.display = "none";
      renderSearchResults([]);
    } finally {
      elements.btnSearch.textContent = "搜索";
      elements.btnSearch.disabled = false;
      if (elements.btnLoadMore) {
        elements.btnLoadMore.textContent = "加载更多资源";
        elements.btnLoadMore.disabled = false;
      }
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
      const recognitionScore =
        item.extra && typeof item.extra.recognition_score === "number"
          ? `<span class="recognition-score">相似 ${Math.round(item.extra.recognition_score * 100)}%</span>`
          : "";
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
          <div class="card-title">${escapeHtml(title)}${recognitionScore}</div>
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
      updateFollowButton();
    } catch (e) {
      toast(`获取详情失败: ${e.message}`, "error");
    }
  }

  function renderEpisodesGrid(segments, preserveSelection) {
    if (!elements.epiChipGrid) return;
    elements.epiChipGrid.innerHTML = "";
    if (!preserveSelection) {
      state.currentSegments = Array.isArray(segments) ? segments : [];
      state.episodePage = 1;
      state.selectedEpisodes.clear();
      state.currentSegments.forEach((seg, idx) => {
        state.selectedEpisodes.add(seg.index || idx + 1);
      });
    }
    const allSegments = state.currentSegments;

    if (!allSegments.length) {
      elements.epiChipGrid.innerHTML =
        `<div class="epi-empty-hint">暂无章节/剧集列表。可尝试「下载全部」，或确认资源 ID 是否正确。</div>`;
      if (elements.epiPagination) elements.epiPagination.innerHTML = "";
      updateSelectedCountLabel();
      return;
    }

    const pageSize = 100;
    const totalPages = Math.max(1, Math.ceil(allSegments.length / pageSize));
    state.episodePage = Math.min(totalPages, Math.max(1, state.episodePage));
    const start = (state.episodePage - 1) * pageSize;
    const pageRows = allSegments.slice(start, start + pageSize);

    pageRows.forEach((seg, idx) => {
      const epIndex = seg.index || start + idx + 1;
      const label = document.createElement("label");
      label.className = "epi-chip-item";
      label.innerHTML = `
        <input type="checkbox" ${state.selectedEpisodes.has(epIndex) ? "checked" : ""} value="${epIndex}">
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

    if (elements.epiPagination) {
      elements.epiPagination.innerHTML = totalPages > 1
        ? `<button class="btn-secondary" id="btnEpisodePrev" ${state.episodePage <= 1 ? "disabled" : ""}>上一页</button>
           <span>第 ${state.episodePage} / ${totalPages} 页</span>
           <button class="btn-secondary" id="btnEpisodeNext" ${state.episodePage >= totalPages ? "disabled" : ""}>下一页</button>`
        : "";
      const prev = document.getElementById("btnEpisodePrev");
      const next = document.getElementById("btnEpisodeNext");
      if (prev) prev.addEventListener("click", () => {
        state.episodePage -= 1;
        renderEpisodesGrid(state.currentSegments, true);
      });
      if (next) next.addEventListener("click", () => {
        state.episodePage += 1;
        renderEpisodesGrid(state.currentSegments, true);
      });
    }
    updateSelectedCountLabel();
  }

  // 首页发现：按平台 tab（红果 / 番茄），各展示热榜 + 今日上新
  function readHomeFilters() {
    state.discoverFilters = {
      genre: elements.homeFilterGenre?.value || "short_play",
      sort: elements.homeFilterSort?.value || "hot_score",
      gender: elements.homeFilterGender?.value || "",
      days: elements.homeFilterDays?.value || "",
      theme: (elements.homeFilterTheme?.value || "").trim(),
      minEpisodes: Math.min(
        10000,
        Math.max(0, parseInt(elements.homeFilterMinEpisodes?.value || "0", 10) || 0)
      ),
    };
  }

  function resetHomeFilters() {
    if (elements.homeFilterGenre) elements.homeFilterGenre.value = "short_play";
    if (elements.homeFilterSort) elements.homeFilterSort.value = "hot_score";
    if (elements.homeFilterGender) elements.homeFilterGender.value = "";
    if (elements.homeFilterDays) elements.homeFilterDays.value = "";
    if (elements.homeFilterTheme) elements.homeFilterTheme.value = "";
    if (elements.homeFilterMinEpisodes) elements.homeFilterMinEpisodes.value = "0";
    readHomeFilters();
  }

  function discoverUrl(kinds, limit) {
    const params = new URLSearchParams({
      platform: state.discoverPlatform || "hongguo",
      kinds,
      limit: String(limit || 24),
    });
    if ((state.discoverPlatform || "hongguo") === "hongguo") {
      const filters = state.discoverFilters || {};
      params.set("genre", filters.genre || "short_play");
      params.set("sort", filters.sort || "hot_score");
      if (filters.gender) params.set("gender", filters.gender);
      if (filters.days) params.set("days", String(filters.days));
      if (filters.theme) params.set("theme", filters.theme);
      if (filters.minEpisodes) {
        params.set("min_episode_count", String(filters.minEpisodes));
      }
    }
    return `/v1/discover?${params.toString()}`;
  }

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
    if (elements.homeAdvancedFilters) {
      elements.homeAdvancedFilters.hidden = p !== "hongguo";
    }
    if (state.discoverView === "discover") {
      loadDiscover();
    } else {
      renderHomeFeatureView(state.discoverView);
    }
  }

  function setDiscoverView(view) {
    const supported = ["discover", "ranking", "calendar", "people", "following"];
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

  function renderPeopleIndex(data) {
    const people = data.people || [];
    if (!people.length) {
      elements.homeSections.innerHTML = `
        <div class="home-error">
          <div class="home-empty-icon">♙</div>
          <div class="home-error-title">暂未读取到演职员资料</div>
          <div class="home-error-copy">上游作品需要返回实名演员资料；漫剧或 AI 短剧可能没有真人演员。</div>
        </div>`;
      return;
    }
    elements.homeSections.innerHTML = `
      <div class="home-people-view">
        ${people
          .map((person) => {
            const avatar = person.avatar
              ? `<img src="${escapeHtml(person.avatar)}" alt="${escapeHtml(person.name)}">`
              : "♙";
            const works = (person.works || [])
              .map((work) => {
                const cover = work.cover
                  ? `<img src="${escapeHtml(work.cover)}" alt="">`
                  : '<span class="person-work-placeholder">🎬</span>';
                return `
                  <button class="person-work-button" data-id="${escapeHtml(work.id)}" type="button">
                    ${cover}
                    <span class="person-work-copy">
                      <strong>${escapeHtml(work.title)}</strong>
                      <span>${escapeHtml(work.role || "参演")}${work.episode_count ? ` · ${escapeHtml(String(work.episode_count))} 集` : ""}</span>
                    </span>
                  </button>`;
              })
              .join("");
            return `
              <article class="person-card">
                <div class="person-avatar">${avatar}</div>
                <div class="person-body">
                  <div class="person-name">${escapeHtml(person.name)} · ${person.works.length} 部作品</div>
                  <div class="person-intro">${escapeHtml(person.intro || "红果作品演职员资料")}</div>
                  <div class="person-works">${works}</div>
                </div>
              </article>`;
          })
          .join("")}
      </div>`;
    elements.homeSections.querySelectorAll(".person-work-button").forEach((button) => {
      button.addEventListener("click", () => {
        const id = button.getAttribute("data-id") || "";
        state.selectedPlatform = "hongguo";
        switchPage("page-search");
        if (elements.searchRightPanel) elements.searchRightPanel.style.display = "flex";
        loadDetail(id, "hongguo");
      });
    });
  }

  async function renderHomeFeatureView(view) {
    if (!elements.homeSections) return;
    const plat = state.discoverPlatform || "hongguo";
    const meta = PLATFORM_META[plat] || PLATFORM_META.hongguo;
    if (elements.homeDiscoverNote) {
      elements.homeDiscoverNote.innerHTML = `<span class="home-note-dot"></span>正在加载${escapeHtml(meta.short)}内容`;
    }
    elements.homeSections.innerHTML = `<div class="home-loading"><div class="home-loading-card"></div><div class="home-loading-card"></div></div>`;
    try {
      if (view === "people") {
        if (plat !== "hongguo") {
          elements.homeSections.innerHTML = `
            <div class="home-error">
              <div class="home-empty-icon">♙</div>
              <div class="home-error-title">演员作品索引当前由红果提供</div>
              <div class="home-error-copy">番茄小说暂无统一演员字段，可切换红果查看真实演职员资料。</div>
              <button class="btn-primary" id="btnPeopleSwitchHongguo">切换红果</button>
            </div>`;
          const switchButton = document.getElementById("btnPeopleSwitchHongguo");
          if (switchButton) {
            switchButton.addEventListener("click", () => setDiscoverPlatform("hongguo"));
          }
          return;
        }
        const genre = state.discoverFilters?.genre || "short_play";
        const data = await apiFetch(
          `/v1/hongguo/people?genre=${encodeURIComponent(genre)}&work_limit=20`,
          { timeoutMs: 90000 }
        );
        renderPeopleIndex(data);
        if (elements.homeDiscoverNote) {
          elements.homeDiscoverNote.innerHTML =
            `<span class="home-note-dot"></span>已扫描 ${data.scanned_works || 0} 部作品 · 收录 ${(data.people || []).length} 位演员`;
        }
        return;
      }
      if (view === "following") {
        const storedItems = Array.from(state.followingItems.values()).filter(
          (item) => platformOf(item) === plat
        );
        const items = await Promise.all(
          storedItems.map(async (item) => {
            try {
              const detail = await apiFetch(
                `/v1/detail?platform=${encodeURIComponent(plat)}&id=${encodeURIComponent(item.id)}`
              );
              const count = Array.isArray(detail.segments) ? detail.segments.length : 0;
              return {
                ...item,
                ...detail,
                extra: {
                  ...(item.extra || {}),
                  ...(detail.extra || {}),
                  has_update: count > Number(item.last_seen_segments || 0),
                  current_segments: count,
                },
              };
            } catch (_) {
              return item;
            }
          })
        );
        renderDiscover({
          sections: [{
            kind: "following",
            title: "♡ 我的追更",
            available: true,
            items,
          }],
          platforms_queried: [plat],
          data_mode: "live",
        });
        if (!items.length && elements.homeDiscoverNote) {
          elements.homeDiscoverNote.innerHTML =
            `<span class="home-note-dot"></span>还没有追更的${escapeHtml(meta.kind)}，在内容卡片或详情页点击“追更”即可加入`;
        }
        return;
      }
      const kind = view === "calendar" ? "new" : "hot";
      const featureUrl =
        discoverUrl(kind, 50) + (view === "calendar" ? "&only_today=false" : "");
      const data = await apiFetch(
        featureUrl,
        { timeoutMs: 15000 }
      );
      let sections;
      if (view === "calendar") {
        const groups = new Map();
        (data.sections || []).flatMap((section) => section.items || []).forEach((item) => {
          const extra = item.extra || {};
          const key =
            String(extra.premiere || "").trim() ||
            (extra.today
              ? "今日上新"
              : extra.genre === "comic_series" || extra.genre === "ai_series"
                ? "7 天内上新"
                : "近期上新");
          if (!groups.has(key)) groups.set(key, []);
          groups.get(key).push(item);
        });
        sections = Array.from(groups.entries()).map(([date, items]) => ({
          kind: "calendar",
          title: `▦ ${date} · ${meta.short}`,
          available: true,
          items,
        }));
      } else {
        sections = (data.sections || []).map((section) => ({
          ...section,
          title: `↗ ${meta.short}热度排行榜`,
        }));
      }
      renderDiscover({ ...data, sections });
    } catch (error) {
      elements.homeSections.innerHTML = `
        <div class="home-error">
          <div class="home-error-title">加载失败</div>
          <div class="home-error-copy">${escapeHtml(error.message || "请稍后重试")}</div>
          <button class="btn-primary" id="btnHomeFeatureRetry">重新加载</button>
        </div>`;
      const retry = document.getElementById("btnHomeFeatureRetry");
      if (retry) retry.addEventListener("click", () => renderHomeFeatureView(view));
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
        discoverUrl("hot,new", 24),
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
    state.discoverData = data;

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
        : `<span class="home-note-dot"></span>${escapeHtml(meta.short)}当前未返回发现内容，可刷新或使用资源搜索`;
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
        : "暂时无法获取";
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
            const metrics = [];
            if (it.extra && it.extra.episode_count) metrics.push(`${it.extra.episode_count} 集`);
            if (it.extra && it.extra.score) metrics.push(`评分 ${it.extra.score}`);
            if (it.extra && it.extra.category) metrics.push(String(it.extra.category));
            return `
              <div class="home-card" data-id="${escapeHtml(it.id)}" data-platform="${escapeHtml(p)}">
                <div class="home-card-cover">
                  ${rank}${cover}
                  <button class="home-card-follow" type="button" title="追更 ${escapeHtml(title)}">${isFollowing(it) ? "♥" : "♡"}</button>
                  <label class="home-card-select" title="选择 ${escapeHtml(title)}">
                    <input class="home-card-checkbox" type="checkbox" aria-label="选择 ${escapeHtml(title)}">
                    <span>✓</span>
                  </label>
                </div>
                <div class="home-card-body">
                  <div class="home-card-title">${escapeHtml(title)}</div>
                  ${metrics.length ? `<div class="home-card-metrics">${escapeHtml(metrics.join(" · "))}</div>` : ""}
                  ${it.extra && it.extra.has_update ? `<div class="home-card-update">发现 ${escapeHtml(String(it.extra.current_segments || ""))} 条内容 · 有更新</div>` : ""}
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
        const followButton = card.querySelector(".home-card-follow");
        if (followButton) {
          followButton.addEventListener("click", (event) => {
            event.stopPropagation();
            const id = card.getAttribute("data-id");
            const p = card.getAttribute("data-platform") || plat;
            const item = (sec.items || []).find((candidate) => String(candidate.id) === String(id));
            if (!item) return;
            const active = toggleFollowing({ ...item, platform: p });
            followButton.textContent = active ? "♥" : "♡";
            if (state.discoverView === "following" && !active) {
              renderHomeFeatureView("following");
            }
          });
        }
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
          const item = (sec.items || []).find((candidate) => String(candidate.id) === String(id));
          if (item && isFollowing({ ...item, platform: p })) {
            const key = `${p}:${id}`;
            const stored = state.followingItems.get(key);
            if (stored && item.extra && item.extra.current_segments) {
              stored.last_seen_segments = Number(item.extra.current_segments);
              state.followingItems.set(key, stored);
              persistFollowing();
            }
          }
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
    if (state.downloadSubmitting) return;
    if (!state.currentDetail) {
      toast("请先选择要下载的资源", "warning");
      return;
    }

    // 检查是否未登录
    if (!state.licenseContext) {
      await refreshLicenseStatus();
      if (!state.licenseContext) {
        toast("请先激活 License", "warning");
        return;
      }
    }
    if (false) {
      toast("请先登录账号（商业路径）", "warning");
      openAuthModal("login");
      return;
    }

    const jobPlatform =
      platformOf(state.currentDetail && state.currentDetail.platform) ||
      state.selectedPlatform ||
      (state.platform !== "all" ? state.platform : "hongguo");
    const options = buildJobOptions();
    const idempotencyKey = `rd-${Date.now()}-${window.crypto && window.crypto.randomUUID ? window.crypto.randomUUID() : Math.random().toString(36).slice(2)}`;
    // 带上标题，任务列表展示用
    if (state.currentDetail && state.currentDetail.title) {
      options.title = state.currentDetail.title;
    }
    try {
      state.downloadSubmitting = true;
      if (elements.btnDownloadAll) elements.btnDownloadAll.disabled = true;
      if (elements.btnDownloadSelected) elements.btnDownloadSelected.disabled = true;
      const res = await apiFetch("/v1/jobs", {
        method: "POST",
        headers: { "Idempotency-Key": idempotencyKey },
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
      if (handleProtectedFailure(e, "任务创建失败")) return;
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
    } finally {
      state.downloadSubmitting = false;
      if (elements.btnDownloadAll) elements.btnDownloadAll.disabled = false;
      if (elements.btnDownloadSelected) elements.btnDownloadSelected.disabled = false;
    }
  }

  // 7. 动态任务列表与状态轮询
  async function refreshJobsPage() {
    try {
      const [summary, jobsRes, queue] = await Promise.all([
        apiFetch("/v1/jobs/summary"),
        apiFetch("/v1/jobs?page=1&page_size=50"),
        apiFetch("/v1/jobs/queue"),
      ]);
      state.queueState = queue;

      if (elements.statActiveJobs) elements.statActiveJobs.textContent = summary.active_jobs;
      if (elements.statCompletedJobs) elements.statCompletedJobs.textContent = summary.completed_jobs;
      if (elements.statTotalSpeed) elements.statTotalSpeed.textContent = summary.total_speed_human;
      if (elements.statDiskFree) elements.statDiskFree.textContent = summary.disk_free_human;
      if (elements.jobCountBadge) elements.jobCountBadge.textContent = summary.active_jobs;
      if (elements.queueStateText) {
        elements.queueStateText.textContent =
          `运行中 ${queue.running_count} · 等待 ${queue.pending_count} · 并发上限 ${queue.max_concurrent_jobs}`;
      }
      if (elements.btnQueuePause) {
        elements.btnQueuePause.textContent = queue.paused
          ? "▶ 恢复等待队列"
          : "⏸ 暂停等待队列";
      }

      const jobs = jobsRes.items || [];
      state.jobs = jobs;
      const validIds = new Set(jobs.map((job) => String(job.job_id)));
      Array.from(state.jobsSelected).forEach((jobId) => {
        if (!validIds.has(jobId)) state.jobsSelected.delete(jobId);
      });
      renderJobsList(filteredJobs());
      updateJobsBulkSelection();
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

  function filteredJobs() {
    const jobs = state.jobs || [];
    const filter = state.jobsFilter || "all";
    if (filter === "all") return jobs;
    if (filter === "active") {
      return jobs.filter((job) =>
        ["pending", "paused", "running", "cancelling"].includes(job.status)
      );
    }
    if (filter === "failed") {
      return jobs.filter((job) => ["failed", "cancelled"].includes(job.status));
    }
    return jobs.filter((job) => job.status === filter);
  }

  function updateJobsBulkSelection() {
    const count = state.jobsSelected.size;
    if (elements.jobsSelectedCount) elements.jobsSelectedCount.textContent = `已选 ${count} 项`;
    if (elements.jobsBulkButtons) {
      elements.jobsBulkButtons.forEach((button) => {
        button.disabled = count === 0;
      });
    }
    if (elements.jobsList) {
      elements.jobsList.querySelectorAll(".job-select-check").forEach((checkbox) => {
        const selected = state.jobsSelected.has(checkbox.getAttribute("data-id") || "");
        checkbox.checked = selected;
        const card = checkbox.closest(".job-item-card");
        if (card) card.classList.toggle("selected", selected);
      });
    }
  }

  async function runJobsBulkAction(action) {
    const jobIds = Array.from(state.jobsSelected);
    if (!jobIds.length) return;
    if (
      ["cancel", "archive"].includes(action) &&
      !confirm(action === "archive" ? "确认清理所选终态任务记录？已下载文件不会删除。" : "确认取消所选任务？")
    ) {
      return;
    }
    elements.jobsBulkButtons.forEach((button) => {
      button.disabled = true;
    });
    try {
      const endpoint =
        action === "retry" ? "/v1/jobs/queue/bulk/retry" : "/v1/jobs/queue/bulk";
      const body =
        action === "retry" ? { job_ids: jobIds } : { job_ids: jobIds, action };
      const response = await apiFetch(endpoint, {
        method: "POST",
        body: JSON.stringify(body),
      });
      const skipped = (response.skipped || []).length;
      toast(
        `批量${action === "pause" ? "暂停" : action === "resume" ? "继续" : action === "retry" ? "重试" : action === "cancel" ? "取消" : "清理"}完成：成功 ${response.affected || 0}，跳过 ${skipped}`,
        skipped ? "warning" : "success",
        4500
      );
      state.jobsSelected.clear();
      await refreshJobsPage();
    } catch (error) {
      if (handleProtectedFailure(error, "批量操作失败")) {
        updateJobsBulkSelection();
        return;
      }
      toast(`批量操作失败：${error.message}`, "error", 5000);
      updateJobsBulkSelection();
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
      const isRunning = job.status === "running";
      const isQueued = job.status === "pending" || job.status === "paused";
      const queuePosition = job.extra && job.extra.queue_position;
      if (job.status === "paused") card.classList.add("paused");
      if (state.jobsSelected.has(String(job.job_id))) card.classList.add("selected");

      let statusBadge = escapeHtml(jobStatusLabel(job));
      if (isSuccess) statusBadge = `✅ ${statusBadge}`;
      else if (isFailed) statusBadge = `❌ ${statusBadge}`;
      else if (isCancelled) statusBadge = `⏹️ ${statusBadge}`;

      const progressPct = Math.min(100, Math.max(0, job.progress || 0));

      card.innerHTML = `
        <input class="job-select-check" data-id="${escapeHtml(job.job_id)}" type="checkbox" aria-label="选择任务 ${escapeHtml((job.extra && job.extra.title) || job.item_id)}">
        <div class="job-item-info" style="width: 100%;">
          <div class="job-item-header">
            <span class="job-item-title">${isQueued ? `<span class="job-queue-position">#${escapeHtml(String(queuePosition || "—"))}</span>` : ""}${isHongguo ? '🔴' : '🍅'} ${escapeHtml((job.extra && job.extra.title) || job.item_id)} <span style="opacity:.65;font-weight:500">[${escapeHtml(job.platform)} · ${escapeHtml(job.item_id)}]</span></span>
            <span class="job-item-speed">${isSuccess ? '✅ 完成' : isFailed ? '❌ 失败' : isRunning ? '⚡ 进行中' : isQueued ? (job.status === "paused" ? "⏸ 已暂停" : "⏳ 排队中") : '已停止'}</span>
          </div>
          <div class="job-progress-bar-bg">
            <div class="job-progress-bar-fill" style="width: ${progressPct}%; ${isSuccess ? 'background: var(--color-success);' : isFailed ? 'background: var(--color-danger, #ef4444);' : ''}"></div>
          </div>
          <div class="job-item-footer">
            <span>${statusBadge}</span>
            <div class="job-controls">
              ${isQueued ? `<button class="btn-secondary btn-queue-up" title="上移">↑</button><button class="btn-secondary btn-queue-down" title="下移">↓</button>` : ''}
              ${isRunning || isQueued ? `<button class="btn-secondary btn-cancel-job" data-id="${job.job_id}">✕ 取消</button>` : ''}
              ${isFailed || isCancelled ? `<button class="btn-primary btn-retry-job">↻ 重试</button>` : ''}
              ${isSuccess && job.files.length > 0 ? `<button class="btn-primary btn-download-local">⬇️ 下载到本机</button>` : ''}
              ${isSuccess && job.files.length > 0 ? `<button class="btn-secondary btn-open-media">▶️ 下载并打开</button>` : ''}
              ${isSuccess && job.files.length > 0 ? `<button class="btn-secondary btn-open-job-folder">📂 本机目录</button>` : ''}
            </div>
          </div>
        </div>
      `;

      const jobCheckbox = card.querySelector(".job-select-check");
      if (jobCheckbox) {
        jobCheckbox.checked = state.jobsSelected.has(String(job.job_id));
        jobCheckbox.addEventListener("change", () => {
          const jobId = String(job.job_id);
          if (jobCheckbox.checked) state.jobsSelected.add(jobId);
          else state.jobsSelected.delete(jobId);
          updateJobsBulkSelection();
        });
      }

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

      const btnUp = card.querySelector(".btn-queue-up");
      if (btnUp) btnUp.addEventListener("click", () => moveQueueItem(job.job_id, -1));
      const btnDown = card.querySelector(".btn-queue-down");
      if (btnDown) btnDown.addEventListener("click", () => moveQueueItem(job.job_id, 1));
      const btnRetry = card.querySelector(".btn-retry-job");
      if (btnRetry) {
        btnRetry.addEventListener("click", async () => {
          try {
            await apiFetch(`/v1/jobs/${job.job_id}/retry`, { method: "POST" });
            toast("任务已重新加入队列", "success");
            refreshJobsPage();
          } catch (error) {
            if (handleProtectedFailure(error, "重试失败")) return;
            toast(`重试失败：${error.message}`, "error");
          }
        });
      }

      elements.jobsList.appendChild(card);
    });
  }

  async function moveQueueItem(jobId, direction) {
    const items = ((state.queueState && state.queueState.items) || [])
      .filter((item) => item.status === "pending" || item.status === "paused")
      .sort(
        (a, b) =>
          Number((a.extra && a.extra.queue_position) || 0) -
          Number((b.extra && b.extra.queue_position) || 0)
      );
    const index = items.findIndex((item) => item.job_id === jobId);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= items.length) return;
    [items[index], items[target]] = [items[target], items[index]];
    try {
      await apiFetch("/v1/jobs/queue/reorder", {
        method: "POST",
        body: JSON.stringify({ job_ids: items.map((item) => item.job_id) }),
      });
      await refreshJobsPage();
    } catch (error) {
      toast(`调整队列失败：${error.message}`, "error");
    }
  }

  async function toggleQueuePaused() {
    const resume = !!(state.queueState && state.queueState.paused);
    try {
      const result = await apiFetch(
        `/v1/jobs/queue/${resume ? "resume" : "pause"}`,
        { method: "POST" }
      );
      toast(
        resume
          ? `已恢复 ${result.affected || 0} 个等待任务`
          : `已暂停 ${result.affected || 0} 个等待任务`,
        "success"
      );
      await refreshJobsPage();
    } catch (error) {
      toast(`队列操作失败：${error.message}`, "error");
    }
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
          <img class="media-thumbnail-image" alt="${escapeHtml(file.title)}" hidden>
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
      loadLibraryThumbnail(file, card);
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

  async function loadLibraryThumbnail(file, card) {
    const image = card && card.querySelector(".media-thumbnail-image");
    const placeholder = card && card.querySelector(".media-placeholder");
    if (!image) return;
    try {
      const headers = {};
      if (state.accessToken) headers.Authorization = `Bearer ${state.accessToken}`;
      else if (state.apiKey) headers["X-API-Key"] = state.apiKey;
      const url =
        `${state.apiBase}/v1/files/thumbnail?file_id=${encodeURIComponent(file.file_id)}`;
      const response = await fetch(url, { headers });
      if (!response.ok) return;
      const blob = await response.blob();
      image.src = URL.createObjectURL(blob);
      image.hidden = false;
      if (placeholder) placeholder.hidden = true;
    } catch (_) {}
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
        state.clientVersion = runtime.client_version || state.clientVersion;
        state.installId = runtime.install_id || "";
        localStorage.removeItem("apiBase");
        if (elements.settingApiBase) {
          elements.settingApiBase.value = runtime.api_base;
          elements.settingApiBase.readOnly = true;
        }
      }
      if (elements.settingDeviceIdentityStatus) {
        const status = runtime && runtime.device_identity_status;
        elements.settingDeviceIdentityStatus.textContent = status === "READY"
          ? `已就绪（${runtime.device_id || "设备已建立"}）`
          : `不可用：${status || "DEVICE_IDENTITY_INVALID"}`;
        elements.settingDeviceIdentityStatus.style.color = status === "READY"
          ? "var(--color-success)"
          : "var(--color-error)";
      }
    }
    const result = await window.pywebview.api.get_download_directory();
    if (result && result.success && result.path) {
      state.prefs.outputDir = result.path;
      if (elements.settingOutputDir) elements.settingOutputDir.value = result.path;
    }
  }

  function renderHongguoMonitor(status) {
    state.hongguoMonitor = status || null;
    if (!status) return;
    if (elements.settingHgMonitorEnabled) {
      elements.settingHgMonitorEnabled.checked = !!status.enabled;
    }
    if (elements.settingHgMonitorAutoQueue) {
      elements.settingHgMonitorAutoQueue.checked = !!status.auto_enqueue;
    }
    if (elements.settingHgMonitorInterval) {
      elements.settingHgMonitorInterval.value = String(status.interval_seconds || 60);
    }
    if (elements.settingHgMonitorLimit) {
      elements.settingHgMonitorLimit.value = String(status.scan_limit || 50);
    }
    if (elements.settingHgMonitorMinEpisodes) {
      elements.settingHgMonitorMinEpisodes.value = String(status.min_episode_count || 0);
    }
    if (elements.settingHgMonitorMaxEnqueue) {
      elements.settingHgMonitorMaxEnqueue.value = String(status.max_auto_enqueue_per_scan || 20);
    }
    if (elements.settingHgMonitorInclude) {
      elements.settingHgMonitorInclude.value = (status.include_keywords || []).join(", ");
    }
    if (elements.settingHgMonitorExclude) {
      elements.settingHgMonitorExclude.value = (status.exclude_keywords || []).join(", ");
    }
    if (elements.settingHgMonitorAuthors) {
      elements.settingHgMonitorAuthors.value = (status.author_keywords || []).join(", ");
    }
    if (elements.settingHgMonitorStatus) {
      const baseline = status.baseline_initialized
        ? `已建立基线 ${status.known_count || 0} 条`
        : "尚未建立基线";
      const scan = status.last_scan_at ? `上次扫描 ${formatDate(status.last_scan_at)}` : "尚未扫描";
      const next = status.next_scan_at ? `下次 ${formatDate(status.next_scan_at)}` : "定时监控未启用";
      const result = `本次发现 ${status.last_detected_count || 0} 条，累计入队 ${status.total_enqueued_count || 0} 条`;
      elements.settingHgMonitorStatus.textContent =
        `${baseline} · ${scan} · ${next} · ${result}` +
        (status.last_error ? ` · 错误：${status.last_error}` : "");
      elements.settingHgMonitorStatus.style.color = status.last_error
        ? "var(--color-error)"
        : "var(--text-muted)";
    }
    if (elements.settingHgMonitorLogs) {
      const logs = (status.logs || []).slice().reverse();
      elements.settingHgMonitorLogs.innerHTML = logs.length
        ? logs
            .map(
              (entry) => `
                <div class="monitor-log-entry ${escapeHtml(entry.level || "info")}">
                  <span>${escapeHtml(formatDate(entry.timestamp))}</span>
                  <span class="monitor-log-level">${entry.level === "error" ? "错误" : entry.level === "warning" ? "警告" : "信息"}</span>
                  <span>${escapeHtml(entry.message || "")}</span>
                </div>`
            )
            .join("")
        : '<div class="monitor-log-empty">暂无监控日志</div>';
    }
  }

  async function loadHongguoMonitor() {
    try {
      renderHongguoMonitor(await apiFetch("/v1/automation/hongguo-new"));
    } catch (error) {
      if (elements.settingHgMonitorStatus) {
        elements.settingHgMonitorStatus.textContent = `无法读取上新策略：${error.message}`;
        elements.settingHgMonitorStatus.style.color = "var(--color-error)";
      }
    }
  }

  async function saveHongguoMonitor() {
    if (!elements.settingHgMonitorEnabled) return;
    const interval = Math.min(
      86400,
      Math.max(30, parseInt(elements.settingHgMonitorInterval.value, 10) || 60)
    );
    const limit = Math.min(
      50,
      Math.max(1, parseInt(elements.settingHgMonitorLimit.value, 10) || 50)
    );
    const parseKeywords = (element) =>
      String((element && element.value) || "")
        .split(/[,，]/)
        .map((value) => value.trim())
        .filter(Boolean)
        .slice(0, 20);
    const status = await apiFetch("/v1/automation/hongguo-new", {
      method: "PUT",
      body: JSON.stringify({
        enabled: !!elements.settingHgMonitorEnabled.checked,
        auto_enqueue: !!elements.settingHgMonitorAutoQueue.checked,
        interval_seconds: interval,
        scan_limit: limit,
        min_episode_count: Math.min(
          10000,
          Math.max(0, parseInt(elements.settingHgMonitorMinEpisodes?.value || "0", 10) || 0)
        ),
        max_auto_enqueue_per_scan: Math.min(
          50,
          Math.max(1, parseInt(elements.settingHgMonitorMaxEnqueue?.value || "20", 10) || 20)
        ),
        include_keywords: parseKeywords(elements.settingHgMonitorInclude),
        exclude_keywords: parseKeywords(elements.settingHgMonitorExclude),
        author_keywords: parseKeywords(elements.settingHgMonitorAuthors),
        quality: "1080p",
        concurrency: state.prefs.concurrency || 2,
        download_cover: !!state.prefs.downloadCover,
        download_desc: !!state.prefs.downloadDesc,
      }),
    });
    renderHongguoMonitor(status);
  }

  async function scanHongguoNewNow() {
    if (!elements.btnScanHgNewNow) return;
    elements.btnScanHgNewNow.disabled = true;
    elements.btnScanHgNewNow.textContent = "识别中…";
    try {
      await saveHongguoMonitor();
      const before = !!(state.hongguoMonitor && state.hongguoMonitor.baseline_initialized);
      const status = await apiFetch("/v1/automation/hongguo-new/scan", {
        method: "POST",
        timeoutMs: 90000,
      });
      renderHongguoMonitor(status);
      if (!before && status.baseline_initialized) {
        toast("当前红果上新已建立为基线，后续新增资源才会触发自动入队", "success", 5000);
      } else {
        toast(
          `识别完成：发现 ${status.last_detected_count || 0} 条新资源，累计入队 ${status.total_enqueued_count || 0} 条`,
          status.last_error ? "warning" : "success",
          5000
        );
      }
    } catch (error) {
      if (handleProtectedFailure(error, "红果上新识别失败")) return;
      toast(`红果上新识别失败：${error.message}`, "error", 5000);
    } finally {
      elements.btnScanHgNewNow.disabled = false;
      elements.btnScanHgNewNow.textContent = "立即识别";
    }
  }

  // 9. 检查软件版本更新 (/v1/version)
  async function checkVersion(silent) {
    try {
      const query =
        `?current_version=${encodeURIComponent(state.clientVersion || "1.0.0")}` +
        `&install_id=${encodeURIComponent(state.installId || "")}`;
      const data = await apiFetch(`/v1/version${query}`);
      if (!data.update_check_enabled || !data.has_update) {
        if (!silent) {
          toast(`当前版本 ${state.clientVersion} 已是最新版本`, "success", 3500);
        }
        return;
      }
      const prompt =
        `发现新版本 ${data.latest_version}\n\n${data.release_notes || "无更新说明"}` +
        (data.mandatory ? "\n\n该版本为必须更新。" : "\n\n是否现在下载并安装？");
      if (!window.confirm(prompt)) {
        if (data.mandatory) toast("必须完成更新后才能继续使用新版本功能", "warning", 5000);
        return;
      }
      if (
        window.pywebview &&
        window.pywebview.api &&
        window.pywebview.api.download_update &&
        window.pywebview.api.install_update
      ) {
        toast("正在下载并校验更新包…", "info", 5000);
        const result = await window.pywebview.api.download_update(
          data.download_url,
          data.sha256 || ""
        );
        if (!result || !result.success) {
          throw new Error((result && result.message) || "更新包下载失败");
        }
        const installed = await window.pywebview.api.install_update(
          result.path,
          !!data.mandatory
        );
        if (!installed || !installed.success) {
          throw new Error((installed && installed.message) || "更新安装程序启动失败");
        }
        return;
      }
      window.location.href = data.download_url;
    } catch (e) {
      if (!silent) toast(`检查版本失败: ${e.message}`, "error");
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
    const verStr = state.clientVersion || data.version || "1.0.0";
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
    // T28: activation-first UI has no ordinary account or API-key controls.
    const legacyAccountCard = elements.btnOpenAuthModal && elements.btnOpenAuthModal.closest(".vip-status-card");
    if (legacyAccountCard) legacyAccountCard.style.display = "none";
    const apiKeyGroup = elements.settingApiKey && elements.settingApiKey.closest(".form-group");
    if (apiKeyGroup) apiKeyGroup.style.display = "none";

    // 拉取当前用户登录态
    // T28: load Device Identity/License status before entering business UI.
    try {
      if (window.pywebview && window.pywebview.api && window.pywebview.api.get_runtime_info) {
        window.pywebview.api.get_runtime_info().then((runtime) => {
          const status = runtime && runtime.device_identity_status;
          if (elements.settingDeviceIdentityStatus && status) {
            elements.settingDeviceIdentityStatus.textContent = status;
          }
        });
      }
    } catch (_) {}
    if (elements.modalRedeemKey) {
      const title = elements.modalRedeemKey.querySelector(".modal-title");
      const hint = elements.modalRedeemKey.querySelector(".modal-hint");
      if (title) title.textContent = "🔑 Activate License";
      if (hint) hint.textContent = "输入 License Service 提供的 Activation Code。私钥只保存在 Windows secure storage。";
    }
    if (elements.btnModalSubmit) elements.btnModalSubmit.textContent = "Activate";
    refreshLicenseStatus().then((status) => {
      if (!status) return;
      loadDiscover();
    });
    // 默认首页发现
    // T28: discover is loaded only after an active License Context is present.

    if (elements.themeToggleBtn) {
      elements.themeToggleBtn.addEventListener("click", () => setTheme(state.theme === "dark" ? "light" : "dark"));
    }

    elements.platformTabs.forEach((tab) => {
      tab.addEventListener("click", () => setPlatform(tab.getAttribute("data-platform")));
    });

    elements.navItems.forEach((nav) => {
      nav.addEventListener("click", () => switchPage(nav.getAttribute("data-page")));
    });

    if (elements.batchInputText) {
      elements.batchInputText.addEventListener("input", updateBatchInputCount);
    }
    if (elements.batchFileInput) {
      elements.batchFileInput.addEventListener("change", async () => {
        const file = elements.batchFileInput.files && elements.batchFileInput.files[0];
        if (!file) return;
        if (file.size > 1024 * 1024) {
          toast("TXT 文件不能超过 1 MB", "warning");
          elements.batchFileInput.value = "";
          return;
        }
        try {
          const text = await file.text();
          if (elements.batchInputText) {
            const current = elements.batchInputText.value.trim();
            elements.batchInputText.value = current ? `${current}\n${text}` : text;
          }
          const count = updateBatchInputCount();
          toast(`已导入 ${file.name}，当前 ${count} 条`, "success");
        } catch (error) {
          toast(`读取 TXT 失败：${error.message}`, "error");
        } finally {
          elements.batchFileInput.value = "";
        }
      });
    }
    if (elements.btnBatchClear) {
      elements.btnBatchClear.addEventListener("click", () => {
        if (elements.batchInputText) elements.batchInputText.value = "";
        state.batchResults = [];
        state.batchSelected.clear();
        updateBatchInputCount();
        renderBatchResults();
        if (elements.batchProgress) elements.batchProgress.hidden = true;
      });
    }
    if (elements.btnBatchResolve) {
      elements.btnBatchResolve.addEventListener("click", resolveBatchInputs);
    }
    if (elements.btnBatchSelectSuccess) {
      elements.btnBatchSelectSuccess.addEventListener("click", () => {
        state.batchSelected.clear();
        state.batchResults.forEach((row, index) => {
          if (row && row.content) state.batchSelected.add(String(index));
        });
        updateBatchSelection();
      });
    }
    if (elements.btnBatchClearSelection) {
      elements.btnBatchClearSelection.addEventListener("click", () => {
        state.batchSelected.clear();
        updateBatchSelection();
      });
    }
    if (elements.btnBatchEnqueue) {
      elements.btnBatchEnqueue.addEventListener("click", enqueueBatchResults);
    }
    if (elements.imageRecognizeInput) {
      elements.imageRecognizeInput.addEventListener("change", () => {
        const file =
          elements.imageRecognizeInput.files && elements.imageRecognizeInput.files[0];
        if (!file) return;
        if (file.size > 8 * 1024 * 1024) {
          toast("图片不能超过 8 MB", "warning");
          elements.imageRecognizeInput.value = "";
          return;
        }
        const reader = new FileReader();
        reader.onload = () => {
          state.imageRecognizeData = String(reader.result || "");
          if (elements.imageRecognizePreview) {
            elements.imageRecognizePreview.src = state.imageRecognizeData;
            elements.imageRecognizePreview.hidden = false;
          }
          if (elements.imageRecognizeStatus) {
            elements.imageRecognizeStatus.textContent = `${file.name} · ${(file.size / 1024).toFixed(1)} KB，等待识别`;
          }
          if (elements.btnRecognizeImage) elements.btnRecognizeImage.disabled = false;
        };
        reader.onerror = () => toast("读取图片失败", "error");
        reader.readAsDataURL(file);
      });
    }
    if (elements.btnRecognizeImage) {
      elements.btnRecognizeImage.addEventListener("click", recognizeSelectedImage);
    }

    if (elements.btnSearch) elements.btnSearch.addEventListener("click", doSearch);
    if (elements.btnLoadMore) {
      elements.btnLoadMore.addEventListener("click", () => {
        if (state.searchHasMore) doSearch(state.searchPage + 1, true);
      });
    }
    if (elements.inputSearchQuery) {
      elements.inputSearchQuery.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          doSearch();
        }
      });
    }
    if (elements.btnToggleFollow) {
      elements.btnToggleFollow.addEventListener("click", () => {
        const active = toggleFollowing(state.currentDetail);
        toast(active ? "已加入我的追更" : "已取消追更", "success");
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
    if (elements.btnApplyHomeFilters) {
      elements.btnApplyHomeFilters.addEventListener("click", () => {
        readHomeFilters();
        state.homeSelectedItems.clear();
        updateHomeSelectionBar();
        if (state.discoverView === "discover") loadDiscover();
        else renderHomeFeatureView(state.discoverView);
      });
    }
    if (elements.btnResetHomeFilters) {
      elements.btnResetHomeFilters.addEventListener("click", () => {
        resetHomeFilters();
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
      elements.btnHomeAddQueue.addEventListener("click", async () => {
        const selected = Array.from(state.homeSelectedItems.values());
        if (!selected.length) return;
        elements.btnHomeAddQueue.disabled = true;
        elements.btnHomeAddQueue.textContent = "正在加入…";
        try {
          const result = await apiFetch("/v1/jobs/batch", {
            method: "POST",
            body: JSON.stringify({
              items: selected.map((item) => ({
                platform: platformOf(item),
                id: String(item.id),
                range: "all",
                options: { title: displayTitle(item) },
              })),
              queue_mode: "enqueue",
              duplicate_policy: "skip_completed",
            }),
          });
          const created = (result.created || []).length;
          const skipped = (result.skipped || []).length;
          const failed = (result.errors || []).length;
          toast(
            `批量任务已处理：创建 ${created}，跳过 ${skipped}，失败 ${failed}`,
            failed ? "warning" : "success",
            4500
          );
          state.homeSelectedItems.clear();
          syncHomeCardSelections();
          updateHomeSelectionBar();
          if (created) {
            switchPage("page-jobs");
            await refreshJobsPage();
          }
        } catch (error) {
          if (handleProtectedFailure(error, "加入下载队列失败")) return;
          toast(`加入下载队列失败：${error.message}`, "error", 5000);
        } finally {
          elements.btnHomeAddQueue.disabled = false;
          elements.btnHomeAddQueue.textContent = "加入下载队列";
        }
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

    if (elements.btnCheckUpdate) {
      elements.btnCheckUpdate.addEventListener("click", () => checkVersion(false));
    }
    if (elements.btnScanHgNewNow) {
      elements.btnScanHgNewNow.addEventListener("click", scanHongguoNewNow);
    }
    if (elements.btnQueuePause) {
      elements.btnQueuePause.addEventListener("click", toggleQueuePaused);
    }
    if (elements.btnRefreshJobs) {
      elements.btnRefreshJobs.addEventListener("click", refreshJobsPage);
    }
    if (elements.jobsStatusFilter) {
      elements.jobsStatusFilter.addEventListener("change", () => {
        state.jobsFilter = elements.jobsStatusFilter.value || "all";
        renderJobsList(filteredJobs());
        updateJobsBulkSelection();
      });
    }
    if (elements.btnJobsSelectVisible) {
      elements.btnJobsSelectVisible.addEventListener("click", () => {
        filteredJobs().forEach((job) => state.jobsSelected.add(String(job.job_id)));
        updateJobsBulkSelection();
      });
    }
    if (elements.btnJobsClearSelected) {
      elements.btnJobsClearSelected.addEventListener("click", () => {
        state.jobsSelected.clear();
        updateJobsBulkSelection();
      });
    }
    if (elements.jobsBulkButtons) {
      elements.jobsBulkButtons.forEach((button) => {
        button.addEventListener("click", () => {
          runJobsBulkAction(button.getAttribute("data-jobs-bulk") || "");
        });
      });
    }

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
    ["settingNameUsePrefix", "settingNameIncludeTitle", "settingNameSeparator"].forEach((id) => {
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
      elements.btnSaveSettings.addEventListener("click", async () => {
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
        if (
          window.pywebview &&
          window.pywebview.api &&
          window.pywebview.api.set_remember_download_directory
        ) {
          window.pywebview.api
            .set_remember_download_directory(!!state.prefs.rememberOutputDir)
            .catch(() => {});
        }
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
        try {
          await saveHongguoMonitor();
          toast("设置与红果上新策略已保存", "success");
        } catch (error) {
          if (handleProtectedFailure(error, "本机设置已保存，但上新策略保存失败")) return;
          toast(`本机设置已保存，但上新策略保存失败：${error.message}`, "warning", 5000);
        }
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

    if (elements.btnResetDeviceIdentity) {
      elements.btnResetDeviceIdentity.addEventListener("click", async () => {
        if (!(window.pywebview && window.pywebview.api && window.pywebview.api.reset_device_identity)) {
          toast(licenseReasonMessage("DESKTOP_DEVICE_IDENTITY_REQUIRED"), "error", 5000);
          return;
        }
        if (!confirm("重置后 License Service 会视为新设备，需要重新激活，并可能占用新的设备槽位。确定继续吗？")) {
          return;
        }
        const result = await window.pywebview.api.reset_device_identity();
        if (!result || !result.success) {
          toast(licenseReasonMessage((result && result.reason) || "DEVICE_IDENTITY_INVALID"), "error", 5000);
          return;
        }
        if (elements.settingDeviceIdentityStatus) {
          elements.settingDeviceIdentityStatus.textContent = `已重置（${result.device_id || "新设备"}）`;
          elements.settingDeviceIdentityStatus.style.color = "var(--color-warning)";
        }
        toast("设备身份已重置，请重新激活。", "warning", 6000);
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
          numberStyle: "01",
          nameSeparator: ".",
        };
        if (elements.settingHgMonitorEnabled) elements.settingHgMonitorEnabled.checked = false;
        if (elements.settingHgMonitorAutoQueue) elements.settingHgMonitorAutoQueue.checked = false;
        if (elements.settingHgMonitorInterval) elements.settingHgMonitorInterval.value = "60";
        if (elements.settingHgMonitorLimit) elements.settingHgMonitorLimit.value = "50";
        if (elements.settingHgMonitorMinEpisodes) elements.settingHgMonitorMinEpisodes.value = "0";
        if (elements.settingHgMonitorMaxEnqueue) elements.settingHgMonitorMaxEnqueue.value = "20";
        if (elements.settingHgMonitorInclude) elements.settingHgMonitorInclude.value = "";
        if (elements.settingHgMonitorExclude) elements.settingHgMonitorExclude.value = "";
        if (elements.settingHgMonitorAuthors) elements.settingHgMonitorAuthors.value = "";
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
          "pref_numberStyle",
          "pref_nameSeparator",
        ].forEach((k) => localStorage.removeItem(k));
        initSettingsForm();
        saveHongguoMonitor().catch((error) => {
          toast(`红果上新策略重置失败：${error.message}`, "warning", 4500);
        });
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
        const remember = elements.settingRememberOutputDir
          ? !!elements.settingRememberOutputDir.checked
          : true;
        const result = await window.pywebview.api.choose_download_directory(remember);
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
        if (false && !state.accessToken) {
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
          if (!(window.pywebview && window.pywebview.api && window.pywebview.api.redeem_license)) {
            throw apiError("DESKTOP_DEVICE_IDENTITY_REQUIRED");
          }
          const bridgeResult = await window.pywebview.api.redeem_license(key, state.accessToken || "");
          if (!bridgeResult || bridgeResult.ok !== true) {
            const reason = (bridgeResult && (bridgeResult.reason || bridgeResult.detail)) || "REQUEST_FAILED";
            throw apiError(reason, (bridgeResult && bridgeResult.status) || 0);
          }
          const res = bridgeResult.data;

          // 硬约束: success === true 才能关弹窗并刷新 me
          if (res && res.success === true) {
            elements.modalRedeemKey.classList.remove("active");
            elements.inputCardKey.value = "";
            await refreshLicenseStatus({ openActivation: false });
            const expiry = res.license_expires_at || res.vip_expires_at;
            const planInfo = res.max_devices ? ` · 设备上限 ${res.max_devices}` : "";
            toast(
              `${res.message || "激活成功"}${expiry ? ` · 到期 ${formatDate(expiry)}` : ""}${planInfo}`,
              "success",
              5000
            );
          } else {
            showRedeemError(licenseReasonMessage((res && res.reason) || "INVALID_KEY"));
          }
        } catch (e) {
          showRedeemError(e && e.userMessage ? e.userMessage : `卡密兑换失败: ${licenseReasonMessage(e && (e.reason || e.message))}`);
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
    syncNativeDownloadDirectory()
      .then(() => checkVersion(true))
      .catch(() => {});
  });
})();
