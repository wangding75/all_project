/* ==========================================================================
   全能短剧/小说资源下载器 - 客户端 REST API 绑定与 UI 控制 (App.js)
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

  // 全局应用状态 State
  const state = {
    theme: localStorage.getItem("theme") || "light",
    platform: localStorage.getItem("platform") || "hongguo",
    activePage: "page-search",
    apiBase: localStorage.getItem("apiBase") || "http://127.0.0.1:8000",
    apiKey: localStorage.getItem("apiKey") || "dev-key-change-me",
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
    themeToggleBtn: document.getElementById("themeToggleBtn"),
    platformTabs: document.querySelectorAll(".platform-tab"),
    navItems: document.querySelectorAll(".nav-item"),
    subpages: document.querySelectorAll(".subpage"),

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

    // 设置页面
    settingApiBase: document.getElementById("settingApiBase"),
    settingApiKey: document.getElementById("settingApiKey"),
    settingOutputDir: document.getElementById("settingOutputDir"),
    btnSaveSettings: document.getElementById("btnSaveSettings"),
    btnResetSettings: document.getElementById("btnResetSettings"),
    btnCheckUpdate: document.getElementById("btnCheckUpdate"),

    // 卡密弹窗
    btnRedeemKey: document.getElementById("btnRedeemKey"),
    modalRedeemKey: document.getElementById("modalRedeemKey"),
    btnModalClose: document.getElementById("btnModalClose"),
    btnModalSubmit: document.getElementById("btnModalSubmit"),
    inputCardKey: document.getElementById("inputCardKey"),

    // 状态栏
    serverStatusText: document.getElementById("serverStatusText"),
    serverStatusDot: document.getElementById("serverStatusDot"),
  };

  function encodeFilePath(fileId) {
    if (!fileId) return "";
    return fileId.split("/").map(encodeURIComponent).join("/");
  }


  // 通用 REST Fetch 辅助函数
  async function apiFetch(endpoint, options = {}) {
    const baseUrl = state.apiBase.replace(/\/+$/, "");
    const url = `${baseUrl}${endpoint}`;
    const headers = {
      "Content-Type": "application/json",
      "X-API-Key": state.apiKey,
      ...(options.headers || {}),
    };
    const response = await fetch(url, { ...options, headers });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errData.detail || `HTTP ${response.status}`);
    }
    return response.json();
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

  // 6. 创建下载任务
  async function createDownloadJob(rangeSpec) {
    if (!state.currentDetail) {
      alert("请先选择要下载的资源！");
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

      alert(`🚀 下载任务已建立！Job ID: ${res.job_id}`);
      switchPage("page-jobs");
    } catch (e) {
      alert(`任务创建失败: ${e.message}`);
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
      alert(`ℹ️ 客户端版本信息:\n当前版本: v2.1.0-desktop\n最新版本: ${data.latest_version}\n说明: ${data.release_notes}`);
    } catch (e) {
      alert(`检查版本失败: ${e.message}`);
    }
  }

  // 10. 检查服务端健康状态
  async function checkServerHealth() {
    try {
      const data = await apiFetch("/health");
      if (elements.serverStatusText) elements.serverStatusText.textContent = `服务正常 (${data.version})`;
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

    // 设置页面绑定
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

    // 卡密兑换弹窗
    if (elements.btnRedeemKey) {
      elements.btnRedeemKey.addEventListener("click", () => elements.modalRedeemKey.classList.add("active"));
    }
    if (elements.btnModalClose) {
      elements.btnModalClose.addEventListener("click", () => elements.modalRedeemKey.classList.remove("active"));
    }
    if (elements.btnModalSubmit) {
      elements.btnModalSubmit.addEventListener("click", async () => {
        const key = elements.inputCardKey.value.trim();
        if (!key) return alert("请输入有效的卡密序列号！");
        try {
          const res = await apiFetch("/v1/auth/redeem", {
            method: "POST",
            body: JSON.stringify({ card_code: key }),
          });
          alert(res.message);
          if (res.success) {
            elements.modalRedeemKey.classList.remove("active");
            elements.inputCardKey.value = "";
          }
        } catch (e) {
          alert(`卡密兑换失败: ${e.message}`);
        }
      });
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
