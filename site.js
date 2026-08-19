(function () {
  "use strict";

  var ROLE_KEY = "twt-role";
  var DONE_KEY = "twt-done";
  var MODULES = ["module-1", "module-2", "module-3", "module-4", "module-5", "module-6"];
  var MODULE_LABELS = {
    "module-1": "Module I",
    "module-2": "Module II",
    "module-3": "Module III",
    "module-4": "Module IV",
    "module-5": "Module V",
    "module-6": "Module VI"
  };

  if (
    location.protocol === "http:" &&
    /(?:^|\.)mrbsocialstudies\.org$/.test(location.hostname)
  ) {
    location.replace(
      "https://" + location.host + location.pathname + location.search + location.hash
    );
    return;
  }

  function readJSON(key, fallback) {
    try {
      var raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (e) {
      return fallback;
    }
  }

  function writeJSON(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {}
  }

  function currentRole() {
    var stored = null;
    try {
      stored = localStorage.getItem(ROLE_KEY);
    } catch (e) {}
    return stored === "teacher" || stored === "parent" ? stored : "parent";
  }

  function setRole(role) {
    if (role !== "teacher" && role !== "parent") role = "parent";
    document.body.setAttribute("data-role", role);
    try {
      localStorage.setItem(ROLE_KEY, role);
    } catch (e) {}
    document.querySelectorAll(".role-pill").forEach(function (pill) {
      var on = pill.getAttribute("data-role") === role;
      pill.classList.toggle("active", on);
      pill.setAttribute("aria-selected", on ? "true" : "false");
    });
  }

  function doneList() {
    var list = readJSON(DONE_KEY, []);
    if (!Array.isArray(list)) return [];
    return list.filter(function (id) {
      return MODULES.indexOf(id) !== -1;
    });
  }

  function isDone(id) {
    return doneList().indexOf(id) !== -1;
  }

  function setDone(id, done) {
    var list = doneList().filter(function (item) {
      return item !== id;
    });
    if (done) list.push(id);
    writeJSON(DONE_KEY, list);
    paintProgress();
  }

  function buttonLabel(id, done) {
    var name = MODULE_LABELS[id] || "this module";
    return done ? name + " done — undo" : "Mark " + name + " as done";
  }

  function paintProgress() {
    MODULES.forEach(function (id) {
      var done = isDone(id);
      document.querySelectorAll('.stop[data-module="' + id + '"]').forEach(function (stop) {
        stop.classList.toggle("done", done);
      });
      document.querySelectorAll('.mark-done[data-module="' + id + '"]').forEach(function (btn) {
        btn.classList.toggle("is-done", done);
        btn.setAttribute("aria-pressed", done ? "true" : "false");
        btn.textContent = buttonLabel(id, done);
      });
    });
  }

  function onReady() {
    setRole(currentRole());
    paintProgress();

    document.querySelectorAll(".role-pill").forEach(function (pill) {
      pill.addEventListener("click", function () {
        setRole(pill.getAttribute("data-role"));
      });
    });

    document.querySelectorAll(".mark-done[data-module]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var id = btn.getAttribute("data-module");
        setDone(id, !isDone(id));
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", onReady);
  } else {
    onReady();
  }
})();
