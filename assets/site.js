(function () {
  "use strict";

  const STORAGE_KEY = "ambient-core-site-lang";
  const DEFAULT_LANG = "en";

  const bannerEl = document.getElementById("commercial-banner-text");
  const bannerLink = document.getElementById("commercial-banner-link");
  const langPicker = document.querySelector(".lang-picker");
  const langSummaryEndonym = document.getElementById("lang-summary-endonym");
  const langPanel = document.getElementById("lang-panel");
  const startBtn = document.getElementById("hero-start");
  const skipBtn = document.querySelector(".skip-link");

  function langMeta(code) {
    return LANG_LIST.find((entry) => entry.code === code) || LANG_LIST[0];
  }

  function storedLang() {
    try {
      const value = localStorage.getItem(STORAGE_KEY);
      if (value && I18N_DATA[value]) {
        return value;
      }
    } catch (_err) {
      /* ignore storage errors */
    }
    return DEFAULT_LANG;
  }

  function persistLang(code) {
    try {
      localStorage.setItem(STORAGE_KEY, code);
    } catch (_err) {
      /* ignore storage errors */
    }
  }

  function applyDir(scope, dir) {
    scope.querySelectorAll("[data-i18n]").forEach((node) => {
      if (dir === "rtl") {
        node.setAttribute("dir", "rtl");
      } else {
        node.removeAttribute("dir");
      }
    });
  }

  function applyBanner(locale, dir) {
    if (!bannerEl || !bannerLink) {
      return;
    }
    const messages = I18N_DATA[locale];
    const template = messages["banner.text"];
    const linkLabel = messages["banner.link"];
    const parts = template.split("{name}");
    bannerEl.replaceChildren();
    if (parts[0]) {
      bannerEl.append(document.createTextNode(parts[0]));
    }
    bannerLink.textContent = linkLabel;
    if (dir === "rtl") {
      bannerLink.setAttribute("dir", "rtl");
    } else {
      bannerLink.removeAttribute("dir");
    }
    bannerEl.append(bannerLink);
    if (parts[1]) {
      bannerEl.append(document.createTextNode(parts[1]));
    }
  }

  function applyLocale(code) {
    const locale = I18N_DATA[code] ? code : DEFAULT_LANG;
    const meta = langMeta(locale);
    document.documentElement.lang = locale;

    document.querySelectorAll("[data-i18n]").forEach((node) => {
      const key = node.getAttribute("data-i18n");
      if (!key || key === "banner.link") {
        return;
      }
      const value = I18N_DATA[locale][key];
      if (value !== undefined) {
        node.textContent = value;
      }
      if (meta.dir === "rtl") {
        node.setAttribute("dir", meta.dir);
      } else {
        node.removeAttribute("dir");
      }
    });

    applyBanner(locale, meta.dir);

    if (langSummaryEndonym) {
      langSummaryEndonym.textContent = meta.endonym;
      langSummaryEndonym.setAttribute("lang", locale);
    }

    if (langPanel) {
      langPanel.querySelectorAll(".lang-picker__item").forEach((btn) => {
        const isCurrent = btn.dataset.langCode === locale;
        btn.setAttribute("aria-current", isCurrent ? "true" : "false");
      });
    }

    persistLang(locale);
  }

  function closeLangPicker(returnFocus) {
    if (!langPicker || !langPicker.open) {
      return;
    }
    langPicker.open = false;
    if (returnFocus) {
      const summary = langPicker.querySelector(".lang-picker__summary");
      summary?.focus();
    }
  }

  function buildLangPanel() {
    if (!langPanel) {
      return;
    }
    langPanel.replaceChildren();
    LANG_LIST.forEach((entry) => {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "lang-picker__item";
      btn.dataset.langCode = entry.code;
      btn.setAttribute("aria-current", "false");
      const bdi = document.createElement("bdi");
      bdi.lang = entry.code;
      bdi.dir = entry.dir;
      bdi.textContent = entry.endonym;
      btn.append(bdi);
      btn.addEventListener("click", () => {
        applyLocale(entry.code);
        closeLangPicker(true);
      });
      li.append(btn);
      langPanel.append(li);
    });
  }

  document.addEventListener("click", (event) => {
    if (!langPicker?.open) {
      return;
    }
    const target = event.target;
    if (target instanceof Node && langPicker.contains(target)) {
      return;
    }
    closeLangPicker(true);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeLangPicker(true);
    }
  });

  if (startBtn) {
    startBtn.addEventListener("click", () => {
      const target = document.getElementById("start");
      target?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  if (skipBtn) {
    skipBtn.addEventListener("click", () => {
      const main = document.getElementById("main-content");
      if (!main) {
        return;
      }
      main.focus({ preventScroll: false });
    });
  }

  buildLangPanel();
  applyLocale(storedLang());
})();
