(function () {
  const storageKey = "statusAppearance";
  const allowedThemes = new Set(["system", "light", "dark"]);
  const root = document.documentElement;
  const control = document.querySelector("[data-status-appearance-toggle]");
  const languageSwitchers = document.querySelectorAll(".language-switcher");
  const copyAddressButtons = document.querySelectorAll("[data-copy-address]");
  const cryptoAddressValues = document.querySelectorAll(".crypto-address code");
  const header = document.querySelector(".site-header");
  const headerNav = header ? header.querySelector(".site-nav") : null;
  const siteFooter = document.querySelector(".site-footer");
  const pageTopLink = document.querySelector("[data-page-top-link]");
  const compactHeaderMedia = window.matchMedia("(max-width: 934px)");
  let activeLightbox = null;
  let activeLightboxTrigger = null;
  const featureLightboxes = Array.from(document.querySelectorAll(".feature-lightbox"));

  function showLightbox(lightbox) {
    if (activeLightbox) {
      activeLightbox.classList.remove("is-open");
    }
    activeLightbox = lightbox;
    activeLightbox.classList.add("is-open");
    const closeButton = lightbox.querySelector(".lightbox__close");
    if (closeButton) {
      closeButton.focus({ preventScroll: true });
    }
  }

  function browseFeatureLightboxes(direction) {
    if (!activeLightbox || !featureLightboxes.includes(activeLightbox)) {
      return;
    }

    const currentIndex = featureLightboxes.indexOf(activeLightbox);
    const nextIndex = (currentIndex + direction + featureLightboxes.length) % featureLightboxes.length;
    showLightbox(featureLightboxes[nextIndex]);
  }

  function closeLightbox() {
    if (!activeLightbox) {
      return;
    }

    activeLightbox.classList.remove("is-open");
    activeLightbox = null;
    if (activeLightboxTrigger) {
      activeLightboxTrigger.focus({ preventScroll: true });
      activeLightboxTrigger = null;
    }
  }

  document.querySelectorAll("[data-lightbox-trigger]").forEach(function (trigger) {
    trigger.addEventListener("click", function (event) {
      event.preventDefault();
      closeLightbox();
      const lightbox = document.querySelector(trigger.getAttribute("href"));
      if (!lightbox) {
        return;
      }

      activeLightboxTrigger = trigger;
      showLightbox(lightbox);
    });
  });

  document.querySelectorAll("[data-lightbox-close]").forEach(function (control) {
    control.addEventListener("click", function (event) {
      event.preventDefault();
      closeLightbox();
    });
  });

  document.querySelectorAll("[data-lightbox-previous]").forEach(function (control) {
    control.addEventListener("click", function () {
      browseFeatureLightboxes(-1);
    });
  });

  document.querySelectorAll("[data-lightbox-next]").forEach(function (control) {
    control.addEventListener("click", function () {
      browseFeatureLightboxes(1);
    });
  });

  function getStoredTheme() {
    try {
      return window.localStorage.getItem(storageKey);
    } catch (error) {
      return null;
    }
  }

  function storeTheme(theme) {
    try {
      window.localStorage.setItem(storageKey, theme);
    } catch (error) {
      return;
    }
  }

  function applyTheme(theme) {
    const selectedTheme = allowedThemes.has(theme) ? theme : "system";
    if (selectedTheme === "system") {
      root.removeAttribute("data-status-theme");
    } else {
      root.setAttribute("data-status-theme", selectedTheme);
    }
    if (control) {
      const input = control.querySelector(`input[value="${selectedTheme}"]`);
      if (input) {
        input.checked = true;
      }
    }
  }

  applyTheme(getStoredTheme() || "system");

  if (control) {
    control.addEventListener("change", function (event) {
      if (!event.target.matches("input[name='status-appearance']")) {
        return;
      }
      applyTheme(event.target.value);
      storeTheme(event.target.value);
    });
  }

  function syncLanguageSwitcherState(details) {
    const summary = details.querySelector("summary");
    if (summary) {
      summary.setAttribute("aria-expanded", details.open ? "true" : "false");
    }
  }

  languageSwitchers.forEach(function (details) {
    syncLanguageSwitcherState(details);
    details.addEventListener("toggle", function () {
      syncLanguageSwitcherState(details);
    });
  });

  document.addEventListener("click", function (event) {
    languageSwitchers.forEach(function (details) {
      if (details.open && !details.contains(event.target)) {
        details.open = false;
        syncLanguageSwitcherState(details);
      }
    });
  });

  document.addEventListener("keydown", function (event) {
    if (activeLightbox && event.key === "Tab") {
      const focusable = Array.from(activeLightbox.querySelectorAll("a[href], button:not([disabled])"));
      if (focusable.length) {
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
      return;
    }
    if (activeLightbox && event.key === "ArrowLeft") {
      event.preventDefault();
      browseFeatureLightboxes(-1);
      return;
    }
    if (activeLightbox && event.key === "ArrowRight") {
      event.preventDefault();
      browseFeatureLightboxes(1);
      return;
    }
    if (event.key !== "Escape") {
      return;
    }
    languageSwitchers.forEach(function (details) {
      if (details.open) {
        details.open = false;
        syncLanguageSwitcherState(details);
      }
    });
    closeLightbox();
  });

  function copyText(value) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(value);
    }

    const textarea = document.createElement("textarea");
    textarea.value = value;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.top = "0";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();

    try {
      document.execCommand("copy");
      return Promise.resolve();
    } catch (error) {
      return Promise.reject(error);
    } finally {
      document.body.removeChild(textarea);
    }
  }

  function truncateMiddle(value, visibleCharacters) {
    if (value.length <= visibleCharacters) {
      return value;
    }

    const edgeCharacters = Math.max(4, Math.floor((visibleCharacters - 4) / 2));
    return `${value.slice(0, edgeCharacters)}....${value.slice(-edgeCharacters)}`;
  }

  function updateCryptoAddressLabels() {
    cryptoAddressValues.forEach(function (code) {
      const row = code.closest(".crypto-address");
      const button = row ? row.querySelector("[data-copy-address]") : null;
      const fullAddress = button ? button.dataset.copyAddress : code.textContent;
      const availableCharacters = Math.max(12, Math.floor(code.clientWidth / 8.5));

      code.textContent = truncateMiddle(fullAddress, availableCharacters);
      code.setAttribute("title", fullAddress);
    });
  }

  updateCryptoAddressLabels();
  window.addEventListener("resize", updateCryptoAddressLabels);

  copyAddressButtons.forEach(function (button) {
    const defaultLabel = button.getAttribute("aria-label");
    let resetTimer = null;

    button.addEventListener("click", function () {
      copyText(button.dataset.copyAddress).then(function () {
        button.classList.add("is-copied");
        button.setAttribute("aria-label", "Wallet address copied");
        window.clearTimeout(resetTimer);
        resetTimer = window.setTimeout(function () {
          button.classList.remove("is-copied");
          button.setAttribute("aria-label", defaultLabel);
        }, 1800);
      }).catch(function () {
        button.classList.remove("is-copied");
        button.setAttribute("aria-label", "Copy failed");
        window.clearTimeout(resetTimer);
        resetTimer = window.setTimeout(function () {
          button.setAttribute("aria-label", defaultLabel);
        }, 1800);
      });
    });
  });

  if (header && headerNav) {
    let lastScrollY = window.scrollY;
    let scrollDirection = null;
    let directionStartY = lastScrollY;
    let expandedHeaderHeight = header.getBoundingClientRect().height;
    let ticking = false;
    const expandAtTopThreshold = 12;
    const compactOnDownDistance = 24;
    const expandOnUpDistance = 40;

    function setCompactHeader(isCompact) {
      header.classList.toggle("site-header--compact", isCompact);
    }

    function updateCompactHeader() {
      const currentScrollY = Math.max(window.scrollY, 0);
      const delta = currentScrollY - lastScrollY;

      if (!header.classList.contains("site-header--compact")) {
        expandedHeaderHeight = header.getBoundingClientRect().height;
      }

      if (!compactHeaderMedia.matches || currentScrollY <= expandAtTopThreshold) {
        setCompactHeader(false);
        scrollDirection = null;
        directionStartY = currentScrollY;
        lastScrollY = currentScrollY;
        ticking = false;
        return;
      }

      if (Math.abs(delta) < 2) {
        lastScrollY = currentScrollY;
        ticking = false;
        return;
      }

      const nextDirection = delta > 0 ? "down" : "up";
      if (nextDirection !== scrollDirection) {
        scrollDirection = nextDirection;
        directionStartY = currentScrollY;
      }

      const directionDistance = Math.abs(currentScrollY - directionStartY);
      if (
        scrollDirection === "down" &&
        currentScrollY > expandedHeaderHeight &&
        directionDistance >= compactOnDownDistance
      ) {
        setCompactHeader(true);
      } else if (scrollDirection === "up" && directionDistance >= expandOnUpDistance) {
        setCompactHeader(false);
      }

      lastScrollY = currentScrollY;
      ticking = false;
    }

    function requestCompactHeaderUpdate() {
      if (ticking) {
        return;
      }
      ticking = true;
      window.requestAnimationFrame(updateCompactHeader);
    }

    window.addEventListener("scroll", requestCompactHeaderUpdate, { passive: true });
    compactHeaderMedia.addEventListener("change", requestCompactHeaderUpdate);
  }

  if (pageTopLink) {
    let topLinkTicking = false;
    let isReturningToTop = false;
    const showTopLinkAfter = 420;
    const defaultTopLinkBottom = 24;
    const topLinkFooterGap = 12;
    const reduceMotionMedia = window.matchMedia("(prefers-reduced-motion: reduce)");

    function updatePageTopLink() {
      let bottomOffset = defaultTopLinkBottom;

      if (siteFooter) {
        const footerTop = siteFooter.getBoundingClientRect().top;
        if (footerTop < window.innerHeight) {
          bottomOffset = Math.max(defaultTopLinkBottom, window.innerHeight - footerTop + topLinkFooterGap);
        }
      }

      pageTopLink.style.setProperty("--page-top-link-bottom", `${bottomOffset}px`);
      if (isReturningToTop && window.scrollY <= 4) {
        isReturningToTop = false;
      }
      pageTopLink.classList.toggle("is-visible", isReturningToTop || window.scrollY > showTopLinkAfter);
      topLinkTicking = false;
    }

    function requestPageTopLinkUpdate() {
      if (topLinkTicking) {
        return;
      }
      topLinkTicking = true;
      window.requestAnimationFrame(updatePageTopLink);
    }

    updatePageTopLink();
    pageTopLink.addEventListener("click", function (event) {
      event.preventDefault();
      isReturningToTop = true;
      pageTopLink.classList.add("is-visible");
      window.scrollTo({
        top: 0,
        behavior: reduceMotionMedia.matches ? "auto" : "smooth",
      });
      requestPageTopLinkUpdate();
    });
    window.addEventListener("scroll", requestPageTopLinkUpdate, { passive: true });
    window.addEventListener("resize", requestPageTopLinkUpdate);
  }

  const messageDemo = document.querySelector("[data-message-demo]");
  if (messageDemo) {
    const overlay = messageDemo.querySelector("[data-message-overlay]");
    const messages = {
      success: "Changes saved successfully.",
      warning: "This action needs your attention.",
      error: "Something went wrong. Please try again.",
    };
    let dismissTimer = null;

    function dismissMessage() {
      window.clearTimeout(dismissTimer);
      if (overlay) {
        overlay.replaceChildren();
      }
    }

    function showMessage(type) {
      if (!overlay) return;
      dismissMessage();
      const message = document.createElement("div");
      message.className = `message-demo__message message-demo__message--${type}`;
      message.textContent = messages[type];
      const dismiss = document.createElement("button");
      dismiss.type = "button";
      dismiss.className = "message-demo__dismiss";
      dismiss.setAttribute("aria-label", "Dismiss message");
      dismiss.textContent = "×";
      dismiss.addEventListener("click", dismissMessage);
      message.appendChild(dismiss);
      message.addEventListener("mouseenter", () => {
        window.clearTimeout(dismissTimer);
        message.classList.add("is-paused");
      });
      message.addEventListener("mouseleave", () => {
        message.classList.remove("is-paused");
        dismissTimer = window.setTimeout(dismissMessage, 1800);
      });
      overlay.appendChild(message);
      dismissTimer = window.setTimeout(dismissMessage, 4000);
    }

    messageDemo.querySelectorAll("[data-message-type]").forEach((button) => {
      button.addEventListener("click", () => {
        messageDemo.querySelectorAll("[data-message-type]").forEach((messageButton) => {
          const isSelected = messageButton === button;
          messageButton.setAttribute("aria-pressed", String(isSelected));
        });
        showMessage(button.dataset.messageType);
      });
    });
  }
})();
