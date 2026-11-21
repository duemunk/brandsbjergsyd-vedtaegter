(function () {
  const dokumenter = window.DOKUMENTER;
  const bilag = window.BILAG;
  const indhold = document.getElementById("indhold");
  const opsummering = document.getElementById("opsummering");

  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const tokens = (s) => s.match(/\n|[^\s]+/g) || [];
  const visTokens = (ts) => ts.map((t) => (t === "\n" ? "<br>" : esc(t))).join(" ").replace(/ <br> /g, "<br>");

  function diff(gammel, ny) {
    const a = tokens(gammel);
    const b = tokens(ny);
    const lcs = Array.from({ length: a.length + 1 }, () => new Uint16Array(b.length + 1));
    for (let i = a.length - 1; i >= 0; i--) {
      for (let j = b.length - 1; j >= 0; j--) {
        lcs[i][j] = a[i] === b[j] ? lcs[i + 1][j + 1] + 1 : Math.max(lcs[i + 1][j], lcs[i][j + 1]);
      }
    }
    const dele = [];
    const tilfoej = (type, ord) => {
      const sidste = dele[dele.length - 1];
      if (sidste && sidste.type === type) sidste.ord.push(ord);
      else dele.push({ type, ord: [ord] });
    };
    let i = 0;
    let j = 0;
    while (i < a.length && j < b.length) {
      if (a[i] === b[j]) { tilfoej("=", a[i]); i++; j++; }
      else if (lcs[i + 1][j] >= lcs[i][j + 1]) { tilfoej("-", a[i]); i++; }
      else { tilfoej("+", b[j]); j++; }
    }
    while (i < a.length) tilfoej("-", a[i++]);
    while (j < b.length) tilfoej("+", b[j++]);
    return dele.map((d) => {
      const tekst = visTokens(d.ord);
      if (d.type === "-") return `<del>${tekst}</del>`;
      if (d.type === "+") return `<ins>${tekst}</ins>`;
      return tekst;
    }).join(" ");
  }

  function status(stk) {
    if (!stk.nu) return "ny";
    return stk.nu.trim() === stk.tekst.trim() ? "uaendret" : "aendret";
  }

  function stkHtml(stk, nr, visAendringer) {
    const s = status(stk);
    let tekst = visTokens(tokens(stk.tekst));
    let maerke = "";
    if (visAendringer) {
      if (s === "ny") {
        tekst = `<ins>${tekst}</ins>`;
        maerke = `<span class="chip chip-ny">＋ Ny</span>`;
      } else if (s === "aendret") {
        tekst = diff(stk.nu, stk.tekst);
        maerke = `<span class="chip">Nu: ${esc(stk.ref)}</span>`;
      } else {
        maerke = `<span class="chip">＝ ${esc(stk.ref)}</span>`;
      }
    }
    const vent = stk.vent ? `<span class="vent">⏳ ${esc(stk.vent)}</span>` : "";
    return `<div class="stk"><b>Stk. ${nr}.</b><div><p>${tekst}</p>${maerke || vent ? `<div class="maerker">${maerke}${vent}</div>` : ""}</div></div>`;
  }

  function bilagHtml() {
    if (!bilag) return "";
    return `<section class="bilag" id="bilag-1">
      <h2>Bilag 1 · Foreningens område</h2>
      <p>Kortet viser foreningens område og de parceller, der hører til foreningen.</p>
      <figure class="kort">${bilag.kort}
        <figcaption class="signatur">
          <span><i class="s-parcel"></i>Parcel</span>
          <span><i class="s-sti"></i>Foreningens stier</span>
          <span><i class="s-groen"></i>Foreningens grønne område</span>
          <span><i class="s-omraade"></i>Områdets grænse</span>
          <span class="kilde">Kilde: Matriklen, Klimadatastyrelsen · Veje: © OpenStreetMap-bidragydere</span>
        </figcaption>
      </figure>
      <h3>Matrikler af Ejby By, Glostrup (${bilag.matrikler.length})</h3>
      <span class="vent">⏳ Tjekkes · 232 parceller er udstykket efter 1968 og foreslået medtaget</span>
      <div class="matrikler">${bilag.matrikler.map((m) => `<span>${esc(m)}</span>`).join("")}</div>
    </section>`;
  }

  function nuvaerendeHtml(dok) {
    const gammel = window.NUVAERENDE[dok.id];
    const afsnit = gammel.afsnit.map((a) => {
      const overskrift = a.nr
        ? `<h2><span class="nr">${esc(a.nr)}</span>${esc(a.titel)}</h2>`
        : `<p class="afsnit-intro">${esc(a.titel)}</p>`;
      const punkter = a.punkter.map((p) => {
        const liste = p.liste ? `<ul class="gammel-liste">${p.liste.map((l) => `<li>${esc(l)}</li>`).join("")}</ul>` : "";
        return a.nr
          ? `<div class="stk"><b>${esc(p.nr)}</b><div><p>${visTokens(tokens(p.tekst))}</p>${liste}</div></div>`
          : `<li>${esc(p.tekst)}</li>`;
      }).join("");
      return `<section class="paragraf">${overskrift}${a.nr ? punkter : `<ul class="pligter">${punkter}</ul>`}</section>`;
    }).join("");
    return `<h1 class="dok-titel">Nuværende ${esc(gammel.titel.toLowerCase())}</h1>
      <div class="historik">${gammel.historik.map((l) => `<p>${esc(l)}</p>`).join("")}</div>
      ${afsnit}
      <p class="note"><a href="nuvaerende-vedtaegter.pdf">Se den originale PDF</a></p>`;
  }

  function vis() {
    const [id, del] = (location.hash.slice(1) || "vedtaegter").split("-");
    const dok = dokumenter.find((d) => d.id === id) || dokumenter[0];
    const tilstand = ["aendringer", "nuvaerende"].includes(del) ? del : "forslag";
    const visAendringer = tilstand === "aendringer";
    const endelse = (t) => (t === "forslag" ? "" : "-" + t);
    document.body.classList.toggle("aendringer", visAendringer);

    document.querySelectorAll("[data-dok]").forEach((el) => el.setAttribute("aria-current", el.dataset.dok === dok.id ? "page" : "false"));
    document.querySelectorAll("[data-tilstand]").forEach((el) => {
      el.setAttribute("aria-pressed", String(el.dataset.tilstand === tilstand));
      el.href = "#" + dok.id + endelse(el.dataset.tilstand);
    });
    document.querySelectorAll("[data-dok]").forEach((el) => { el.href = "#" + el.dataset.dok + endelse(tilstand); });

    if (tilstand === "nuvaerende") {
      opsummering.innerHTML = "";
      indhold.innerHTML = nuvaerendeHtml(dok);
      document.title = `Nuværende ${dok.titel.toLowerCase()} – Brandsbjerg Syd`;
      return;
    }

    const alle = dok.paragraffer.flatMap((p) => p.stk);
    const antal = { aendret: 0, ny: 0, uaendret: 0 };
    alle.forEach((s) => antal[status(s)]++);
    opsummering.innerHTML = visAendringer
      ? `<span><del>slettet</del> <ins>tilføjet</ins></span><span>${antal.aendret} ændrede stk.</span><span>${antal.ny} nye</span><span>${dok.udgaar.length} udgår</span>`
      : "";

    const paragraffer = dok.paragraffer.map((p) => `
      <section class="paragraf" id="${dok.id}-${p.nr.replace(/\D/g, "")}">
        <h2><span class="nr">${esc(p.nr)}</span>${esc(p.titel)}</h2>
        ${p.stk.map((s, i) => stkHtml(s, i + 1, visAendringer)).join("")}
      </section>`).join("");

    const note = dok.note ? `<p class="note">${esc(dok.note)}</p>` : "";
    const udgaar = visAendringer && dok.udgaar.length
      ? `<section class="udgaar"><h2>Udgår eller flyttes</h2>${dok.udgaar.map((u) => `
          <div class="stk"><b>${esc(u.ref)}</b><div><p><del>${esc(u.nu)}</del></p><div class="maerker"><span class="chip chip-udgaar">− ${esc(u.status)}</span></div></div></div>`).join("")}</section>`
      : "";
    const afslutning = `<div class="afslutning">${dok.afslutning.map((l) => `<p>${esc(l)}</p>`).join("")}</div>`;

    indhold.innerHTML = `<h1 class="dok-titel">${esc(dok.titel)}</h1>${paragraffer}${note}${udgaar}${afslutning}${dok.bilag ? bilagHtml() : ""}`;
    document.title = `${dok.titel}${visAendringer ? " · ændringer" : ""} – Brandsbjerg Syd`;
  }

  window.addEventListener("hashchange", vis);
  vis();
})();
