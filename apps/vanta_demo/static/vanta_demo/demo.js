document.addEventListener("DOMContentLoaded", () => {
  let activeLightbox = null;
  let activeLightboxTrigger = null;

  function closeLightbox() {
    if (!activeLightbox) return;

    activeLightbox.classList.remove("is-open");
    activeLightbox = null;
    if (activeLightboxTrigger) {
      activeLightboxTrigger.focus({ preventScroll: true });
      activeLightboxTrigger = null;
    }
  }

  document.querySelectorAll("[data-demo-lightbox-trigger]").forEach((trigger) => {
    trigger.addEventListener("click", (event) => {
      event.preventDefault();
      const lightbox = document.querySelector(trigger.getAttribute("href"));
      if (!lightbox) return;

      closeLightbox();
      activeLightbox = lightbox;
      activeLightboxTrigger = trigger;
      activeLightbox.classList.add("is-open");
      lightbox.querySelector(".demo-lightbox__close")?.focus({ preventScroll: true });
    });
  });

  document.querySelectorAll("[data-demo-lightbox-close]").forEach((control) => {
    control.addEventListener("click", (event) => {
      event.preventDefault();
      closeLightbox();
    });
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeLightbox();
  });

  document.querySelectorAll("[data-demo-form]").forEach((form) => {
    form.addEventListener("submit", () => {
      const button = form.querySelector("[data-demo-submit]");
      if (!button || button.disabled) return;
      button.disabled = true;
      button.setAttribute("aria-busy", "true");
      const label = button.querySelector(".button__label");
      if (label && button.dataset.busyLabel) label.textContent = button.dataset.busyLabel;
    });
  });
});
