document.addEventListener("DOMContentLoaded", () => {
  const accountLinks = document.querySelector(".admin-sidebar__account-links");
  if (!accountLinks) return;

  accountLinks.replaceChildren();

  [
    ["admin-icon-lock", "Change password"],
    ["admin-icon-2fa-settings", "2FA settings"],
  ].forEach(([iconName, labelText]) => {
    const link = document.createElement("a");
    link.href = "#";

    const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    icon.setAttribute("aria-hidden", "true");
    if (iconName === "admin-icon-2fa-settings") icon.classList.add("admin-sidebar__2fa-icon");

    const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
    use.setAttribute("href", `#${iconName}`);
    icon.append(use);

    const label = document.createElement("span");
    label.textContent = labelText;
    link.append(icon, label);
    accountLinks.append(link);
  });

  const logoutLabel = document.querySelector(".admin-sidebar__logout-section button span");
  if (logoutLabel) logoutLabel.textContent = "Log out";
});
