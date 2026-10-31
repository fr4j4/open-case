/* Open Case website. Draws the case cards from cases.json and fades in the trailer scenes.
   Every path is relative, so it works from a folder, from /open-case/ and from a preview. */
(function () {
  "use strict";

  var STRINGS = {
    es: {
      loading: "Cargando los casos…",
      error: "No se pudo cargar la lista de casos. Recarga la página o descarga los archivos desde el repositorio.",
      empty: "Todavía no hay casos publicados.",
      teams: "equipos", team: "equipo", minutes: "min", playersFrom: " o más personas por equipo", to: " a ",
      teamsZip: "Material de los equipos", teamsNote: "Kit, sobres, tarjetas, placas y fichas",
      directorZip: "Material del director", directorWarn: "Contiene la solución. Solo para quien dirige.",
      by: "Autoría", noCover: "Caso",
      units: ["B", "KB", "MB"], decimal: ","
    },
    en: {
      loading: "Loading the cases…",
      error: "The list of cases could not be loaded. Reload the page or download the files from the repository.",
      empty: "No cases published yet.",
      teams: "teams", team: "team", minutes: "min", playersFrom: " or more people per team", to: " to ",
      teamsZip: "Material for the teams", teamsNote: "Kit, envelopes, cards, badges and tokens",
      directorZip: "Material for the director", directorWarn: "It contains the solution. For the director only.",
      by: "Author", noCover: "Case",
      units: ["B", "KB", "MB"], decimal: "."
    }
  };

  var lang = (document.documentElement.lang || "es").slice(0, 2);
  var t = STRINGS[lang] || STRINGS.es;

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function range(pair, unit) {
    if (!pair) return "";
    var s = pair[0] === pair[1] ? String(pair[0]) : pair[0] + t.to + pair[1];
    return unit ? s + " " + unit : s;
  }

  function size(bytes) {
    if (bytes >= 1048576) return (bytes / 1048576).toFixed(1).replace(".", t.decimal) + " " + t.units[2];
    if (bytes >= 1024) return Math.round(bytes / 1024) + " " + t.units[1];
    return bytes + " " + t.units[0];
  }

  function zipLink(info, cls, title, note, warn) {
    var a = el("a", "zip " + cls);
    a.href = info.file;
    a.setAttribute("download", "");
    a.appendChild(el("span", "zip__ico", "ZIP"));
    var text = el("span", "zip__t");
    text.appendChild(el("b", null, title));
    text.appendChild(el("span", warn ? "zip__aviso" : null, warn || note));
    a.appendChild(text);
    a.appendChild(el("span", "zip__tam", size(info.bytes)));
    return a;
  }

  function card(c, index) {
    var texts = c.languages[lang] || c.languages[c.base_language];
    var article = el("article", "caso-card");
    var fig = el("figure", "caso-card__foto vineta" + (c.cover ? "" : " caso-card__foto--vacia"));
    if (c.cover) {
      var img = el("img", "duo--claro");
      img.src = c.cover;
      img.alt = texts.cover_alt || "";
      img.loading = "lazy";
      img.width = 900;
      img.height = 506;
      fig.appendChild(img);
    } else {
      fig.appendChild(el("span", "caso-card__vacia", t.noCover));
    }
    var num = el("span", "num", ("0" + (index + 1)).slice(-2));
    num.setAttribute("aria-hidden", "true");
    fig.appendChild(num);
    if (c.date) fig.appendChild(el("span", "ver", c.date));
    article.appendChild(fig);

    var body = el("div", "caso-card__cuerpo");
    body.appendChild(el("h3", null, texts.title));
    var meta = el("div", "caso-card__meta");
    var teams = c.min_teams === c.max_teams ? String(c.min_teams) : c.min_teams + t.to + c.max_teams;
    [Object.keys(c.languages).map(function (l) { return l.toUpperCase(); }).join(" · "),
     teams + " " + (c.max_teams === 1 ? t.team : t.teams),
     range(c.duration_minutes, t.minutes),
     (c.players_per_team ? c.players_per_team[0] + t.playersFrom : "")].forEach(function (m) { if (m) meta.appendChild(el("span", null, m)); });
    body.appendChild(meta);
    body.appendChild(el("p", null, texts.summary));
    var zips = el("div", "zips");
    zips.appendChild(zipLink(texts.teams_zip, "zip--equipos", t.teamsZip, t.teamsNote));
    zips.appendChild(zipLink(texts.director_zip, "zip--director", t.directorZip, "", t.directorWarn));
    body.appendChild(zips);
    body.appendChild(el("p", "caso-card__licencia", t.by + ": " + c.author + " · " + c.license));
    article.appendChild(body);
    return article;
  }

  function render(data) {
    var list = document.getElementById("lista-casos");
    var status = document.getElementById("casos-estado");
    var next = list.querySelector(".caso-card--proximo");
    if (status) status.remove();
    if (!data.cases || !data.cases.length) {
      list.insertBefore(el("p", "casos__estado", t.empty), next);
      return;
    }
    data.cases.forEach(function (c, i) { list.insertBefore(card(c, i), next); });
  }

  function loadCases() {
    var status = document.getElementById("casos-estado");
    if (!status) return;
    status.textContent = t.loading;
    fetch(document.body.getAttribute("data-cases") || "cases.json")
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(render)
      .catch(function () { status.textContent = t.error; status.classList.add("casos__estado--error"); });
  }

  function reveal() {
    var els = document.querySelectorAll(".anim");
    if (!("IntersectionObserver" in window)) {
      els.forEach(function (e) { e.classList.add("is-in"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("is-in"); io.unobserve(en.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px" });
    els.forEach(function (e) { io.observe(e); });
  }

  loadCases();
  reveal();
})();
