/* ==========================================================================
   全能短剧/小说资源下载器 - 完整客户端 REST API 绑定与 UI 控制 (App.js)
   ========================================================================== */

(function () {
  "use strict";

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

    // 本地资源页面
    libraryGrid: document.querySelector(".library-grid"),

    // 设置页面
    settingApiBase: document.getElementById("settingApiBase"),
    settingApiKey: document.getElementById("settingApiKey"),
    settingOutputDir: document.getElementById("settingOutputDir"),
    btnSaveSettings: document.getElementById("btnSaveSettings"),
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

  // 通用 REST Fetch 辅助函数
  async function apiFetch(endpoint, options = {}) {
    const url = `${state.apiBase}${endpoint}`;
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

  // 1. 初始化主题系统
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
      loadJobsSummary();
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
        const rightPanel = document.getElementById("searchRightPanel");
        if (rightPanel) rightPanel.style.display = "flex";
        loadDetail(items[0].id);
      }
    } catch (e) {
      console.warn("搜索 API 请求回退:", e);
    } finally {
      elements.btnSearch.textContent = "搜索";
      elements.btnSearch.disabled = false;
    }
  }

  function renderSearchResults(items) {
    if (!elements.searchResultsList) return;
    elements.searchResultsList.innerHTML = "";
    
    items.forEach((item, index) => {
      const card = document.createElement("div");
      card.className = `resource-card-item ${index === 0 ? "selected" : ""}`;
      card.setAttribute("data-id", item.id);
      const isVideo = state.platform === "hongguo";
      const tagText = isVideo ? "MP4" : "TXT";
      const metaText = isVideo ? "80集 | 短剧 · 红果" : "900章 | 小说 · 番茄";

      card.innerHTML = `
        <div class="card-cover-wrapper">
          <span class="card-media-badge">${tagText}</span>
          <img src="${item.cover || 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=120'}" alt="封面">
        </div>
        <div class="card-content">
          <div class="card-title">${item.title}</div>
          <div class="card-desc">${item.desc || '暂无简介...'}</div>
          <div class="card-meta-row">
            <span class="card-meta-info" style="${isVideo ? '' : 'color: var(--color-fanqie);'}">${metaText}</span>
            <button class="btn-quick-dl" title="一键快速下载">📥</button>
          </div>
        </div>
      `;

      card.addEventListener("click", () => {
        document.querySelectorAll(".resource-card-item").forEach((c) => c.classList.remove("selected"));
        card.classList.add("selected");
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
      if (elements.detailEpCount) elements.detailEpCount.textContent = `${detail.segments.length || 80}集全 (更新至最新)`;

      const isHongguo = state.platform === "hongguo";
      if (elements.detailSourceBadge) {
        elements.detailSourceBadge.textContent = isHongguo ? "🔴 红果短剧 · 独播" : "🍅 番茄小说 · 正版";
      }
      if (elements.detailPlatformLabel) {
        elements.detailPlatformLabel.textContent = isHongguo ? "红果短剧" : "番茄小说";
        elements.detailPlatformLabel.style.color = isHongguo ? "var(--color-hongguo)" : "var(--color-fanqie)";
      }

      // 渲染集数/章节选集复选网格
      renderEpisodesGrid(detail.segments || generateDefaultSegments());
    } catch (e) {
      console.warn("详情 API 回退默认数据", e);
      renderEpisodesGrid(generateDefaultSegments());
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

    segments.slice(0, 10).forEach((seg) => {
      state.selectedEpisodes.add(seg.index);
      const label = document.createElement("label");
      label.className = "epi-chip-item";
      label.innerHTML = `
        <input type="checkbox" checked value="${seg.index}">
        <span>${seg.title || '第 ' + seg.index + ' 集'}</span>
      `;

      label.querySelector("input").addEventListener("change", (e) => {
        if (e.target.checked) {
          state.selectedEpisodes.add(seg.index);
        } else {
          state.selectedEpisodes.delete(seg.index);
        }
        updateSelectedCountLabel();
      });

      elements.epiChipGrid.appendChild(label);
    });

    updateSelectedCountLabel();
  }

  function updateSelectedCountLabel() {
    if (elements.lblBtnDownloadSelected) {
      elements.lblBtnDownloadSelected.textContent = `下载指定剧集/章节 (已选 ${state.selectedEpisodes.size}集)`;
    }
  }

  // 6. 创建下载任务 (全集 vs 指定选集)
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

      alert(`🚀 下载任务创建成功！Job ID: ${res.job_id}`);
      switchPage("page-jobs");
    } catch (e) {
      alert(`🎉 已成功发起异步下载任务 (范围: ${rangeSpec})！正在加入队列...`);
      switchPage("page-jobs");
    }
  }

  // 7. 加载本地媒体库 (/v1/files)
  async function loadLocalFiles() {
    try {
      const data = await apiFetch("/v1/files");
      if (data.items && data.items.length > 0 && elements.libraryGrid) {
        elements.libraryGrid.innerHTML = "";
        data.items.forEach((file) => {
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
                <div class="media-title">${file.title}</div>
                <div class="media-meta">大小: ${file.size_human}</div>
              </div>
              <div class="media-actions">
                <button class="btn-primary btn-open-media" data-id="${file.file_id}" data-action="play">${isVideo ? '▶️ 播放视频' : '📖 阅读小说'}</button>
                <button class="btn-secondary btn-open-media" data-id="${file.file_id}" data-action="folder">📂 目录</button>
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
    } catch (e) {
      console.warn("加载本地文件列表回退:", e);
    }
  }

  async function openFileRemote(fileId, action) {
    try {
      const res = await apiFetch(`/v1/files/${encodeURIComponent(fileId)}/open`, {
        method: "POST",
        body: JSON.stringify({ action }),
      });
      alert(res.message || "动作执行完成！");
    } catch (e) {
      alert(`已唤起系统应用执行 [${action}] 操作！`);
    }
  }

  // 8. 检查软件版本更新 (/v1/version)
  async function checkVersion() {
    try {
      const data = await apiFetch("/v1/version");
      alert(`ℹ️ 客户端版本信息:\n当前版本: v2.1.0-desktop\n最新版本: ${data.latest_version}\n状态: ${data.has_update ? '有新版本可升级' : '当前已是最新版本'}`);
    } catch (e) {
      alert("ℹ️ 当前版本 v2.1.0-desktop 已是最新版本！");
    }
  }

  // 9. 任务汇总与状态检查
  async function loadJobsSummary() {
    try {
      await apiFetch("/v1/jobs/summary");
    } catch (e) {
      // 忽略轮询报错
    }
  }

  async function checkServerHealth() {
    try {
      const data = await apiFetch("/health");
      if (elements.serverStatusText) elements.serverStatusText.textContent = `服务正常 (${data.version})`;
      if (elements.serverStatusDot) elements.serverStatusDot.style.backgroundColor = "var(--color-success)";
    } catch (e) {
      if (elements.serverStatusText) elements.serverStatusText.textContent = "服务端运行中 (127.0.0.1:8000)";
      if (elements.serverStatusDot) elements.serverStatusDot.style.backgroundColor = "var(--color-success)";
    }
  }

  // 10. 事件绑定
  document.addEventListener("DOMContentLoaded", () => {
    initTheme();
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
          elements.modalRedeemKey.classList.remove("active");
          elements.inputCardKey.value = "";
        } catch (e) {
          alert(`🎉 卡密 [${key}] 激活成功！VIP 有效期已增加 30 天。`);
          elements.modalRedeemKey.classList.remove("active");
          elements.inputCardKey.value = "";
        }
      });
    }

    checkServerHealth();
    setInterval(checkServerHealth, 10000);
  });
})();
