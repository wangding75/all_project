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

  // 全局应用状态 State
  const state = {
    theme: localStorage.getItem("theme") || "light",
    platform: localStorage.getItem("platform") || "hongguo",
    activePage: "page-search",
    apiBase: localStorage.getItem("apiBase") || "http://127.0.0.1:8000",
    apiKey: localStorage.getItem("apiKey") || "dev-key-change-me",
    accessToken: localStorage.getItem("accessToken") || "",
    user: null, // me 摘要 { id, username, is_active, vip_expires_at, is_vip }
    authMode: "login", // login 或 register
    currentDetail: null,
    searchResults: [],
    selectedEpisodes: new Set(),
    jobsPollTimer: null,
    libraryFilter: "all",
    librarySearch: "",
    libraryFiles: [],
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

    // 搜索页面
    inputSearchQuery: document.getElementById("inputSearchQuery"),
    btnSearch: document.getElementById("btnSearch"),
    btnLoad: document.getElementById("btnLoad"),
    searchResultsList: document.getElementById("searchResultsList"),
    btnLoadMore: document.getElementById("btnLoadMore"),

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
    settingBtnAuthModal: document.getElementById("settingBtnAuthModal"),
    settingBtnLogout: document.getElementById("settingBtnLogout"),
    settingApiBase: document.getElementById("settingApiBase"),
    settingApiKey: document.getElementById("settingApiKey"),
    settingOutputDir: document.getElementById("settingOutputDir"),
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

    // 状态栏
    serverStatusText: document.getElementById("serverStatusText"),
    serverStatusDot: document.getElementById("serverStatusDot"),
  };

  function encodeFilePath(fileId) {
    if (!fileId) return "";
    return fileId.split("/").map(encodeURIComponent).join("/");
  }

  // 通用 REST Fetch 辅助函数 (E2 统一鉴权: Bearer token 优先; 无 token 时用 X-API-Key)
  async function apiFetch(endpoint, options = {}) {
    const baseUrl = state.apiBase.replace(/\/+$/, "");
    const url = `${baseUrl}${endpoint}`;
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };

    if (state.accessToken) {
      headers["Authorization"] = `Bearer ${state.accessToken}`;
    } else if (state.apiKey) {
      headers["X-API-Key"] = state.apiKey;
    }

    const response = await fetch(url, { ...options, headers });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({ detail: response.statusText }));
      const errorDetail = errData.detail || `HTTP ${response.status}`;

      // 401: token 过期或无效
      if (response.status === 401 && state.accessToken && !endpoint.includes("/v1/auth/login")) {
        state.accessToken = "";
        localStorage.removeItem("accessToken");
        state.user = null;
        updateAuthUI();
        alert("登录凭证已失效或过期，请重新登录！");
      }
      throw new Error(errorDetail);
    }
    return response.json();
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
      if (elements.settingBtnAuthModal) elements.settingBtnAuthModal.style.display = "none";
      if (elements.settingBtnLogout) elements.settingBtnLogout.style.display = "inline-block";
    } else {
      // 未登录状态
      if (elements.vipUsername) elements.vipUsername.textContent = "未登录";
      if (elements.vipUserAvatar) elements.vipUserAvatar.textContent = "👤";
      if (elements.vipExpireDate) elements.vipExpireDate.textContent = "未登录 (商业默认路径)";

      if (elements.btnOpenAuthModal) elements.btnOpenAuthModal.style.display = "flex";
      if (elements.btnRedeemKey) elements.btnRedeemKey.style.display = "none";
      if (elements.btnLogoutBtn) elements.btnLogoutBtn.style.display = "none";

      // 设置页面
      if (elements.settingUsernameVal) elements.settingUsernameVal.textContent = "未登录";
      if (elements.settingVipExpireVal) elements.settingVipExpireVal.textContent = "未开通 VIP";
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
        alert(`✅ 登录成功！欢迎回来 ${username}`);
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

        alert("🎉 注册成功！正在为您自动登录...");
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
      alert(msg);
    }
  }

  function doLogout() {
    state.accessToken = "";
    localStorage.removeItem("accessToken");
    state.user = null;
    updateAuthUI();
    alert("已成功退出登录。");
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
      elements.themeToggleBtn.innerHTML = themeName === "dark" ? "☀️ 切换浅色主题" : "🌙 切换深色主题";
    }
  }

  function initSettingsForm() {
    if (elements.settingApiBase) elements.settingApiBase.value = state.apiBase;
    if (elements.settingApiKey) elements.settingApiKey.value = state.apiKey;
  }

  // 2. 平台选择器
  function setPlatform(platformName) {
    state.platform = platformName;
    localStorage.setItem("platform", platformName);
    elements.platformTabs.forEach((tab) => {
      tab.classList.toggle("active", tab.getAttribute("data-platform") === platformName);
    });

    if (elements.cardQualityWrapper) {
      elements.cardQualityWrapper.style.display = platformName === "fanqie" ? "none" : "block";
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

    if (pageId === "page-library") {
      loadLocalFiles();
    } else if (pageId === "page-jobs") {
      refreshJobsPage();
      startJobsPolling();
    } else {
      stopJobsPolling();
    }
  }

  // 4. 执行资源搜索
  async function doSearch() {
    const query = elements.inputSearchQuery.value.trim();
    if (!query) {
      alert("请输入要搜索的短剧/小说名称或链接！");
      return;
    }
    elements.btnSearch.textContent = "搜索中...";
    elements.btnSearch.disabled = true;

    try {
      const items = await apiFetch(`/v1/search?platform=${state.platform}&q=${encodeURIComponent(query)}`);
      state.searchResults = items;
      renderSearchResults(items);
      if (items.length > 0) {
        if (elements.searchRightPanel) elements.searchRightPanel.style.display = "flex";
        loadDetail(items[0].id);
      } else {
        alert("未搜索到相关资源，请尝试更改关键词或重新指定 ID。");
      }
    } catch (e) {
      alert(`搜索失败: ${e.message}`);
    } finally {
      elements.btnSearch.textContent = "搜索";
      elements.btnSearch.disabled = false;
    }
  }

  function renderSearchResults(items) {
    if (!elements.searchResultsList) return;
    elements.searchResultsList.innerHTML = "";

    if (items.length === 0) {
      elements.searchResultsList.innerHTML = `
        <div class="search-empty-state" style="text-align: center; padding: 60px 20px; color: var(--text-secondary);">
          <div style="font-size: 48px; margin-bottom: 12px;">🔍</div>
          <div style="font-size: 14px; font-weight: 600;">未查找到结果</div>
        </div>
      `;
      return;
    }

    items.forEach((item, index) => {
      const card = document.createElement("div");
      card.className = `resource-card-item ${index === 0 ? "selected" : ""}`;
      card.setAttribute("data-id", item.id);
      const isVideo = state.platform === "hongguo";
      const tagText = isVideo ? "MP4" : "TXT";
      const platformText = isVideo ? "短剧 · 红果" : "小说 · 番茄";

      card.innerHTML = `
        <div class="card-cover-wrapper">
          <span class="card-media-badge">${escapeHtml(tagText)}</span>
          <img src="${escapeHtml(item.cover || 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=120')}" alt="封面">
        </div>
        <div class="card-content">
          <div class="card-title">${escapeHtml(item.title)}</div>
          <div class="card-desc">${escapeHtml(item.desc || '暂无简介...')}</div>
          <div class="card-meta-row">
            <span class="card-meta-info" style="${isVideo ? '' : 'color: var(--color-fanqie);'}">${escapeHtml(platformText)}</span>
            <button class="btn-quick-dl" title="加载详情">📥</button>
          </div>
        </div>
      `;

      card.addEventListener("click", () => {
        document.querySelectorAll(".resource-card-item").forEach((c) => c.classList.remove("selected"));
        card.classList.add("selected");
        if (elements.searchRightPanel) elements.searchRightPanel.style.display = "flex";
        loadDetail(item.id);
      });

      elements.searchResultsList.appendChild(card);
    });
  }

  // 5. 加载详情信息与选集网格
  async function loadDetail(itemId) {
    try {
      const detail = await apiFetch(`/v1/detail?platform=${state.platform}&id=${encodeURIComponent(itemId)}`);
      state.currentDetail = detail;

      if (elements.detailTitle) elements.detailTitle.textContent = detail.title;
      if (elements.detailId) elements.detailId.textContent = detail.id;
      if (elements.detailSynopsis) elements.detailSynopsis.textContent = detail.desc || "【资源描述】暂无详细描述...";
      const segCount = detail.segments ? detail.segments.length : 0;
      if (elements.detailEpCount) elements.detailEpCount.textContent = `${segCount > 0 ? segCount + '条' : '全集'} (更新至最新)`;

      const isHongguo = state.platform === "hongguo";
      if (elements.detailSourceBadge) {
        elements.detailSourceBadge.textContent = isHongguo ? "🔴 红果短剧 · 独播" : "🍅 番茄小说 · 正版";
      }
      if (elements.detailPlatformLabel) {
        elements.detailPlatformLabel.textContent = isHongguo ? "红果短剧" : "番茄小说";
        elements.detailPlatformLabel.style.color = isHongguo ? "var(--color-hongguo)" : "var(--color-fanqie)";
      }

      renderEpisodesGrid(detail.segments || generateDefaultSegments());
    } catch (e) {
      alert(`获取详情失败: ${e.message}`);
    }
  }

  function generateDefaultSegments() {
    const arr = [];
    for (let i = 1; i <= 10; i++) {
      arr.push({ id: String(i), title: `第 ${i} 集`, index: i });
    }
    return arr;
  }

  function renderEpisodesGrid(segments) {
    if (!elements.epiChipGrid) return;
    elements.epiChipGrid.innerHTML = "";
    state.selectedEpisodes.clear();

    if (!segments || segments.length === 0) {
      segments = generateDefaultSegments();
    }

    segments.forEach((seg, idx) => {
      const epIndex = seg.index || (idx + 1);
      state.selectedEpisodes.add(epIndex);
      const label = document.createElement("label");
      label.className = "epi-chip-item";
      label.innerHTML = `
        <input type="checkbox" checked value="${epIndex}">
        <span>${escapeHtml(seg.title || ('第 ' + epIndex + ' 集'))}</span>
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

  function updateSelectedCountLabel() {
    if (elements.lblBtnDownloadSelected) {
      elements.lblBtnDownloadSelected.textContent = `下载指定剧集/章节 (已选 ${state.selectedEpisodes.size}项)`;
    }
  }

  // 6. 创建下载任务 (E2 VIP 403 与 429 诚实提示)
  async function createDownloadJob(rangeSpec) {
    if (!state.currentDetail) {
      alert("请先选择要下载的资源！");
      return;
    }

    // 检查是否未登录
    if (!state.accessToken && (!state.apiKey || state.apiKey === "dev-key-change-me")) {
      if (confirm("⚠️ 商业多租户模式需要登录账号并开通 VIP。是否现在登录账号？")) {
        openAuthModal("login");
      }
      return;
    }

    const quality = elements.selectQuality ? elements.selectQuality.value : "1080p";
    try {
      const res = await apiFetch("/v1/jobs", {
        method: "POST",
        body: JSON.stringify({
          platform: state.platform,
          id: state.currentDetail.id,
          range: rangeSpec,
          options: { quality: quality },
        }),
      });

      alert(`🚀 下载任务已成功建立！Job ID: ${res.job_id}`);
      switchPage("page-jobs");
    } catch (e) {
      const msg = e.message || "";
      if (msg.includes("VIP") || msg.includes("403")) {
        alert(`⚠️ VIP 权限不足或未开通: ${msg}\n\n正在为您自动打开卡密兑换窗口...`);
        if (elements.modalRedeemKey) elements.modalRedeemKey.classList.add("active");
      } else if (msg.includes("配额") || msg.includes("quota")) {
        alert(`⚠️ 今日任务创建失败: ${msg}\n(提示: 普通 VIP 每日受配额限制，Ops/Key 免配额，明日将自动重置)`);
      } else if (msg.includes("频繁") || msg.includes("上限")) {
        alert(`⚠️ 创建任务受限: ${msg}`);
      } else {
        alert(`任务创建失败: ${msg}`);
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

      renderJobsList(jobsRes.items || []);
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

      let statusBadge = `状态: ${escapeHtml(job.message || job.status)}`;
      if (isSuccess) statusBadge = `✅ 已完成 (${job.files.length} 个文件)`;
      else if (isFailed) statusBadge = `❌ 失败: ${escapeHtml(job.error || job.message)}`;
      else if (isCancelled) statusBadge = `⏹️ 已取消`;

      const progressPct = Math.min(100, Math.max(0, job.progress || 0));

      card.innerHTML = `
        <div class="job-item-info" style="width: 100%;">
          <div class="job-item-header">
            <span class="job-item-title">${isHongguo ? '🔴' : '🍅'} ID: ${escapeHtml(job.item_id)} [${escapeHtml(job.platform)}]</span>
            <span class="job-item-speed">${isSuccess ? '✅ 完成' : isFailed ? '❌ 失败' : isRunning ? '⚡ 进行中' : '已停止'}</span>
          </div>
          <div class="job-progress-bar-bg">
            <div class="job-progress-bar-fill" style="width: ${progressPct}%; ${isSuccess ? 'background: var(--color-success);' : isFailed ? 'background: var(--color-danger, #ef4444);' : ''}"></div>
          </div>
          <div class="job-item-footer">
            <span>${statusBadge}</span>
            <div class="job-controls">
              ${isRunning ? `<button class="btn-secondary btn-cancel-job" data-id="${job.job_id}">✕ 取消</button>` : ''}
              ${isSuccess && job.files.length > 0 ? `<button class="btn-primary btn-open-media" data-id="${escapeHtml(job.files[0].file_id)}" data-action="play">▶️ 打开/播放</button>` : ''}
              <button class="btn-secondary btn-open-job-folder" data-id="${job.job_id}">📂 目录</button>
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
            alert(`取消任务失败: ${err.message}`);
          }
        });
      }

      const btnOpenMedia = card.querySelector(".btn-open-media");
      if (btnOpenMedia) {
        btnOpenMedia.addEventListener("click", () => {
          openFileRemote(btnOpenMedia.getAttribute("data-id"), "play");
        });
      }

      const btnOpenFolder = card.querySelector(".btn-open-job-folder");
      if (btnOpenFolder) {
        btnOpenFolder.addEventListener("click", () => {
          if (job.files && job.files.length > 0) {
            openFileRemote(job.files[0].file_id, "folder");
          } else {
            openFileRemote(job.job_id, "folder");
          }
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
      alert(`加载本地资源失败: ${e.message}`);
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
          本地数据为空或未匹配到检索文件。
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
          <img src="${isVideo ? 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=300' : 'https://images.unsplash.com/photo-1457369804613-52c61a468e7d?w=300'}" alt="封面">
        </div>
        <div class="media-body">
          <div>
            <div class="media-title">${escapeHtml(file.title)}</div>
            <div class="media-meta">大小: ${escapeHtml(file.size_human)}</div>
          </div>
          <div class="media-actions">
            <button class="btn-primary btn-open-media" data-id="${escapeHtml(file.file_id)}" data-action="play">${isVideo ? '▶️ 播放视频' : '📖 阅读小说'}</button>
            <button class="btn-secondary btn-open-media" data-id="${escapeHtml(file.file_id)}" data-action="folder">📂 目录</button>
          </div>
        </div>
      `;

      card.querySelectorAll(".btn-open-media").forEach((btn) => {
        btn.addEventListener("click", () => {
          openFileRemote(btn.getAttribute("data-id"), btn.getAttribute("data-action"));
        });
      });

      elements.libraryGrid.appendChild(card);
    });
  }

  async function openFileRemote(fileId, action) {
    try {
      const pathEncoded = encodeFilePath(fileId);
      const res = await apiFetch(`/v1/files/${pathEncoded}/open`, {
        method: "POST",
        body: JSON.stringify({ action }),
      });
      console.log(res.message);
    } catch (e) {
      alert(`无法打开文件或目录: ${e.message}`);
    }
  }

  // 9. 检查软件版本更新 (/v1/version)
  async function checkVersion() {
    try {
      const data = await apiFetch("/v1/version");
      alert(`ℹ️ 客户端版本信息:\n服务端最新版本: ${data.latest_version}\n说明: ${data.release_notes}`);
    } catch (e) {
      alert(`检查版本失败: ${e.message}`);
    }
  }

  // 10. 检查服务端健康状态 (自动拉取并对齐 /health 版本)
  async function checkServerHealth() {
    try {
      const data = await apiFetch("/health");
      const verStr = data.version || "0.2.0";
      if (elements.titlebarVersionTag) elements.titlebarVersionTag.textContent = `v${verStr}`;
      if (elements.settingAppVersionVal) elements.settingAppVersionVal.textContent = `v${verStr}-desktop`;
      if (elements.serverStatusText) elements.serverStatusText.textContent = `服务正常 (v${verStr})`;
      if (elements.serverStatusDot) elements.serverStatusDot.style.backgroundColor = "var(--color-success)";
    } catch (e) {
      if (elements.serverStatusText) elements.serverStatusText.textContent = "服务不可达 (127.0.0.1:8000)";
      if (elements.serverStatusDot) elements.serverStatusDot.style.backgroundColor = "var(--color-danger, #ef4444)";
    }
  }

  // 11. 初始化与事件绑定
  document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initSettingsForm();
    setPlatform(state.platform);

    // 拉取当前用户登录态
    fetchMe();

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

    if (elements.btnLoad) {
      elements.btnLoad.addEventListener("click", () => {
        const query = elements.inputSearchQuery.value.trim();
        if (!query) return alert("请输入要载入的资源 ID 或 URL！");
        if (elements.searchRightPanel) elements.searchRightPanel.style.display = "flex";
        loadDetail(query);
      });
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

    // 设置页面保存与重置绑定
    if (elements.btnSaveSettings) {
      elements.btnSaveSettings.addEventListener("click", () => {
        if (elements.settingApiBase) {
          state.apiBase = elements.settingApiBase.value.trim();
          localStorage.setItem("apiBase", state.apiBase);
        }
        if (elements.settingApiKey) {
          state.apiKey = elements.settingApiKey.value.trim();
          localStorage.setItem("apiKey", state.apiKey);
        }
        alert("⚙️ 系统配置已成功保存！");
        checkServerHealth();
      });
    }

    if (elements.btnResetApiKey) {
      elements.btnResetApiKey.addEventListener("click", () => {
        state.apiKey = "dev-key-change-me";
        localStorage.removeItem("apiKey");
        if (elements.settingApiKey) elements.settingApiKey.value = "dev-key-change-me";
        alert("API Key 已重置为默认开发 Key ('dev-key-change-me')！");
      });
    }

    if (elements.btnResetSettings) {
      elements.btnResetSettings.addEventListener("click", () => {
        state.apiBase = "http://127.0.0.1:8000";
        state.apiKey = "dev-key-change-me";
        localStorage.removeItem("apiBase");
        localStorage.removeItem("apiKey");
        initSettingsForm();
        alert("系统配置已恢复为默认值！");
        checkServerHealth();
      });
    }

    if (elements.btnOpenOutputDir) {
      elements.btnOpenOutputDir.addEventListener("click", () => {
        openFileRemote(".", "folder");
      });
    }

    if (elements.btnLibraryOpenDir) {
      elements.btnLibraryOpenDir.addEventListener("click", () => {
        openFileRemote(".", "folder");
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
            alert(`🎉 ${res.message || '卡密兑换成功！VIP 有效期已重置/延长。'}`);
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
        alert(msg);
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
  });
})();
