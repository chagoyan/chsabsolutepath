// app.js — says hello when your page loads it, then sends the rover for a drive.

(function () {
  // The address this script was loaded from. We use it to find the rover picture on the same site.
  var me = document.currentScript || document.querySelector('script[src$="app.js"]');
  var site = new URL("/", me.src).href;

  function launch() {
    var toast = document.createElement("div");
    toast.textContent = "🚀 app.js loaded";
    toast.style.cssText =
      "position:fixed;right:12px;bottom:12px;z-index:9999;padding:8px 14px;border-radius:999px;" +
      "background:#f59e0b;color:#1a1a1a;font:600 13px ui-monospace,Menlo,Consolas,monospace;" +
      "box-shadow:0 4px 14px rgba(0,0,0,.3)";
    document.body.appendChild(toast);

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    var rover = document.createElement("img");
    rover.src = site + "Assets/Icons/rover.svg";
    rover.alt = "";
    rover.style.cssText =
      "position:fixed;left:-90px;bottom:52px;width:72px;z-index:9998;pointer-events:none;" +
      "transition:transform 4s linear";
    document.body.appendChild(rover);
    void rover.offsetWidth;
    rover.style.transform = "translateX(" + (window.innerWidth + 180) + "px)";
    setTimeout(function () { rover.remove(); }, 4300);
  }

  if (document.body) launch();
  else document.addEventListener("DOMContentLoaded", launch);

  console.log("app.js loaded from " + me.src);
})();
