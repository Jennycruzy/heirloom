// Collapses the site menu behind a button on narrow screens.
// Without JavaScript the menu stays visible as a scrollable row.

const header = document.querySelector(".site-header");
const toggle = header?.querySelector(".menu-toggle");
const nav = header?.querySelector(".site-nav");

if (header && toggle && nav) {
  header.classList.add("site-header--menu");

  const setOpen = (open) => {
    toggle.setAttribute("aria-expanded", String(open));
    header.classList.toggle("site-header--open", open);
  };

  toggle.addEventListener("click", () => setOpen(toggle.getAttribute("aria-expanded") !== "true"));
  nav.addEventListener("click", (event) => { if (event.target.closest("a")) setOpen(false); });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
      setOpen(false);
      toggle.focus();
    }
  });
}
