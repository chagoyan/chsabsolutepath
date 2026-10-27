// nav_bar.js — adds a menu bar to the top of any page that loads it.
// The links point to the pages in CHSAbsolutePath/Pages.

(function () {
  // The address this script was loaded from. We use it to build links back to the same site.
  var me = document.currentScript || document.querySelector('script[src$="nav_bar.js"]');
  var site = new URL("/", me.src).href;

  var pages = [
    ["About us", "Pages/about_us.html"],
    ["Blog", "Pages/blog.html"],
    ["FAQ", "Pages/faq.html"],
    ["News", "Pages/news.html"],
    ["Gallery", "Pages/photo_gallery.html"]
  ];

  function build() {
    var nav = document.createElement("nav");
    nav.style.cssText =
      "display:flex;align-items:center;flex-wrap:wrap;gap:4px;padding:8px 12px;margin:0 0 16px;" +
      "background:#111a2e;border:1px solid #2a3550;border-radius:12px;" +
      "font:14px ui-monospace,Menlo,Consolas,monospace";

    var icon = document.createElement("img");
    icon.src = site + "Assets/Icons/menu_icon.svg";
    icon.alt = "";
    icon.width = 22;
    icon.height = 22;
    icon.style.cssText = "display:inline-block;margin-right:6px";
    nav.appendChild(icon);

    var brand = document.createElement("strong");
    brand.textContent = "CHSAbsolutePath";
    brand.style.cssText = "color:#f59e0b;margin-right:10px";
    nav.appendChild(brand);

    pages.forEach(function (page) {
      var link = document.createElement("a");
      link.textContent = page[0];
      link.href = site + page[1];
      link.style.cssText = "color:#e6e9f2;text-decoration:none;padding:4px 10px;border-radius:8px;background:#1e293b";
      nav.appendChild(link);
    });

    document.body.insertBefore(nav, document.body.firstChild);
  }

  if (document.body) build();
  else document.addEventListener("DOMContentLoaded", build);

  console.log("nav_bar.js loaded from " + me.src);
})();
