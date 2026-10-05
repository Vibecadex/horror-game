(function () {
  const main = document.querySelector("main");
  const nav = document.querySelector("nav");
  const storeKey = "teddy-brief-checks-v1";

  const sections = [
    ["answer", "Answer"],
    ["camera", "Camera"],
    ["models", "Models"],
    ["air", "Atmosphere"],
    ["play", "Gameplay"],
    ["proof", "Proof"],
    ["sources", "Sources"],
    ["build", "Build list"]
  ];

  nav.innerHTML = sections.map(([id, label]) => `<a href="#${id}">${label}</a>`).join("");

  function tag(state) {
    return `<span class="tag ${state}">${state}</span>`;
  }

  function steps(list) {
    return `<ol class="steps">${list.map((item) => `<li>${item}</li>`).join("")}</ol>`;
  }

  function pictureRow() {
    return `<div class="pics">${BRIEF.pictures.map((pic) =>
      `<figure><img src="${pic.src}" alt=""> <figcaption>${pic.cap}</figcaption></figure>`
    ).join("")}</div>`;
  }

  main.innerHTML = `
    <section id="answer">
      <p class="lede">${BRIEF.hero.lede}</p>
      <div class="routes">
        ${BRIEF.routes.map((route) => `<article class="card"><h3>${route.label}</h3><p>${route.text}</p><p><a href="#${route.id}">Open ${route.label}</a></p></article>`).join("")}
      </div>
      <h3>Pictures the brief is allowed to use</h3>
      ${pictureRow()}
      <p class="readout">The phone recording is a reference, not a measurement. Social-video chrome, captions, and the low-angle PDF camera stay out of the game. Coordinates on this site are centimetres. +X is the far wall. +Z is up.</p>
    </section>

    <section id="camera">
      <h2>Camera angles</h2>
      <p>The inspirational shot is an elevated three-quarter view. Floor and contact shadow stay in frame. There is no horizon and no cut. This project holds that as one combat camera.</p>
      <div class="pose-bar" id="pose-bar"></div>
      <div class="grid-2">
        <div>
          <svg class="map" id="map" viewBox="-2000 -2000 4000 4000" role="img" aria-label="Top-down arena with the selected camera pose"></svg>
          <p class="legend"><span><i class="swatch cam"></i>Camera</span><span><i class="swatch player"></i>Player</span><span><i class="swatch boss"></i>Boss</span><span>Dashed box is the combat floor. +X is far, +Y is up.</span></p>
        </div>
        <div>
          <p class="readout" id="pose-note"></p>
          <h3>How to build it</h3>
          ${steps(BRIEF.steps.camera)}
        </div>
      </div>
      <h3>Retired cameras</h3>
      <div class="cards" id="retired-cam"></div>
    </section>

    <section id="models">
      <h2>3D models</h2>
      <p>The video creature was replaced by the preserved teddy. The room is built by repeating a small kit, not by inventing a second architecture.</p>
      <div class="tools" id="model-filters"></div>
      <div id="model-list"></div>
      <h3>How to build it</h3>
      ${steps(BRIEF.steps.models)}
      <h3>Lanes the meshes must leave open</h3>
      <table><thead><tr><th>Lane</th><th>Extent</th><th>Width</th></tr></thead><tbody>
        ${BRIEF.lanes.map((lane) => `<tr><td>${lane.name}</td><td>${lane.box}</td><td>${lane.width}</td></tr>`).join("")}
      </tbody></table>
    </section>

    <section id="air">
      <h2>Atmospherics</h2>
      <p>Match <a href="../visuals/direction-close-best.jpg">direction-close-best.jpg</a>: a cool centre, black corners, a warm teddy, and a floor that is damp in places and dry in others. Parity with that still is not accepted.</p>
      <div class="cards">
        ${BRIEF.lights.map((light) => `<article class="fact"><span class="tag hold">hold</span> <strong>${light.name}</strong> — ${light.value}<p>${light.detail}</p><p class="readout">${light.source}</p></article>`).join("")}
      </div>
      <h3>Materials</h3>
      <table><thead><tr><th>Surface</th><th>Hold</th></tr></thead><tbody>
        <tr><td>Charcoal concrete</td><td>Mean sRGB about 44, 42, 39. Roughness 0.82–0.95.</td></tr>
        <tr><td>Worn green-grey steel</td><td>About 27, 30, 29. Roughness 0.55–0.80.</td></tr>
        <tr><td>Muted oxide</td><td>About 54, 31, 24. Roughness 0.65–0.88. Pipe color, not a teal wash.</td></tr>
        <tr><td>Near-black recess</td><td>About 12, 13, 14. Roughness 0.84–0.92.</td></tr>
        <tr><td>Floor</td><td>Damp roughness 0.40–0.65. Dry 0.75–0.95. Not a mirror and not cyan paint.</td></tr>
        <tr><td>Cloth</td><td>Cloth shading model. Amount 0.32 goes through the ClearCoat pin. Fuzz Color is unwired.</td></tr>
      </tbody></table>
      <h3>How to build it</h3>
      ${steps(BRIEF.steps.air)}
    </section>

    <section id="play">
      <h2>Gameplay</h2>
      <p>The player circles, aims independently, and fires the existing rifle. The teddy chases, warns, and slams. The three stitchlings crawl and die with the boss. That is the whole fight.</p>
      <div class="time-bar" id="time-bar"></div>
      <p class="readout" id="beat-note"></p>
      <h3>Numbers</h3>
      <table><thead><tr><th>Quantity</th><th>Hold</th><th>Where</th></tr></thead><tbody>
        ${BRIEF.numbers.map((row) => `<tr><td>${row[0]}</td><td>${row[1]}</td><td>${row[2]}</td></tr>`).join("")}
      </tbody></table>
      <h3>Animation</h3>
      <p>Shipped at 30 fps: ${BRIEF.clips.shipped.join(", ")}. The live death binding is A_Teddy_DefeatGrounded. ${BRIEF.clips.channel}</p>
      <p>On disk, not assigned: ${BRIEF.clips.extra.join(", ")}.</p>
      <h3>Audio</h3>
      <div class="cards">
        ${BRIEF.audio.map((sound) => `<article class="fact"><span class="tag open">unauditioned</span> <strong>${sound.name}</strong> ${sound.seconds}s<p>${sound.use}</p></article>`).join("")}
      </div>
      <h3>How to build it</h3>
      ${steps(BRIEF.steps.play)}
    </section>

    <section id="proof">
      <h2>What is proven, and what is open</h2>
      <div class="cards">
        ${BRIEF.proof.map((item) => `<article class="fact"><span class="tag hold">${item.result}</span> <strong>${item.name}</strong><p>${item.note}</p></article>`).join("")}
      </div>
      <h3>Still open</h3>
      <ol class="steps">${BRIEF.open.map((item) => `<li>${item}</li>`).join("")}</ol>
      <h3>Do not bring these back</h3>
      <div class="tools">
        <input id="search" type="search" placeholder="Search holds, bans, sources" aria-label="Search the brief">
      </div>
      <div class="cards" id="retired"></div>
      <h3>Conflicts the desks settled</h3>
      <div id="conflicts"></div>
    </section>

    <section id="sources">
      <h2>References and citations</h2>
      <p>Local files decide the numbers. These pages decide the technique. Clothing simulation, a new creature, and a public deploy of this brief are outside the work.</p>
      <div class="cite-list" id="cites"></div>
      <h3>Project files</h3>
      <p>REFERENCE_BRIEF.md, MASTER_PROMPT.md, WORK_STATUS.md (09:30 UTC), ENCOUNTER.md, study/PARITY_ART_DIRECTION.md, study/PARITY_ASSET_MANIFEST.md, study/parity-combined-settings.json, study/parity-atmosphere-settings.json, study/preprod/LEVEL_DESIGN.md, LIGHTING.md, ANIMATION.md, VFX_AUDIO.md, FULL_ASSET_LIST.md, and the READMEs under Assets/Adapted.</p>
    </section>

    <section id="build">
      <h2>Build list</h2>
      <p>Tick these on this machine. The ticks stay in this browser only. They do not change the level.</p>
      <div class="progress" aria-hidden="true"><span id="bar"></span></div>
      <p class="readout" id="count"></p>
      <div id="checks"></div>
    </section>
    <footer>Draft site for the study. Open this folder’s index.html. Nothing here was imported, and the level was not opened.</footer>
  `;

  const retiredCam = BRIEF.retired.filter((item) => /camera|FOV|hero/i.test(item.name));
  document.querySelector("#retired-cam").innerHTML = retiredCam.map(retiredCard).join("");

  function retiredCard(item) {
    return `<article class="fact retired-card"><span class="tag retired">retired</span> <strong>${item.name}</strong><p>${item.why}</p></article>`;
  }
  const retiredBox = document.querySelector("#retired");
  retiredBox.innerHTML = BRIEF.retired.map(retiredCard).join("");

  document.querySelector("#conflicts").innerHTML = BRIEF.contradictions.map((item) =>
    `<article class="fact"><strong>${item.conflict}</strong><p>${item.winner}</p></article>`
  ).join("");

  document.querySelector("#cites").innerHTML = BRIEF.citations.map((item) =>
    `<article class="cite"><a href="${item.url}">${item.title}</a><p>${item.claim}</p></article>`
  ).join("");

  const families = ["All", ...new Set(BRIEF.models.map((item) => item.family))];
  const filterBar = document.querySelector("#model-filters");
  filterBar.innerHTML = families.map((name, index) =>
    `<button class="chip ${index === 0 ? "on" : ""}" data-family="${name}">${name}</button>`
  ).join("");
  const modelList = document.querySelector("#model-list");
  function drawModels(family) {
    const rows = BRIEF.models.filter((item) => family === "All" || item.family === family);
    modelList.innerHTML = `<table><thead><tr><th>Family</th><th>Piece</th><th>State</th><th>Note</th></tr></thead><tbody>
      ${rows.map((item) => `<tr><td>${item.family}</td><td>${item.name}</td><td>${tag(item.state)}</td><td>${item.detail}</td></tr>`).join("")}
    </tbody></table>`;
  }
  drawModels("All");
  filterBar.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    filterBar.querySelectorAll(".chip").forEach((chip) => chip.classList.remove("on"));
    button.classList.add("on");
    drawModels(button.dataset.family);
  });

  const poseBar = document.querySelector("#pose-bar");
  poseBar.innerHTML = BRIEF.poses.map((pose, index) =>
    `<button class="chip ${index === 0 ? "on" : ""}" data-pose="${pose.id}">${pose.name}</button>`
  ).join("");

  function fmt(point) {
    if (!point) return "not written";
    return `(${point[0]}, ${point[1]}, ${point[2]})`;
  }

  function drawPose(id) {
    const pose = BRIEF.poses.find((item) => item.id === id);
    const map = document.querySelector("#map");
    const sx = (x) => x;
    const sy = (y) => -y;
    const pts = [pose.camera, pose.player, pose.boss, pose.look, [-1600, -1700], [1800, 1700]].filter(Boolean);
    const xs = pts.map((point) => point[0]);
    const ys = pts.map((point) => point[1]);
    const minX = Math.min(...xs) - 280;
    const maxX = Math.max(...xs) + 280;
    const minY = Math.min(...ys) - 280;
    const maxY = Math.max(...ys) + 280;
    const width = maxX - minX;
    const height = maxY - minY;
    map.setAttribute("viewBox", `${minX} ${-maxY} ${width} ${height}`);
    const font = Math.round(Math.max(width, height) / 28);
    const radius = Math.round(Math.max(width, height) / 55);
    const dots = [
      pose.player ? `<circle cx="${sx(pose.player[0])}" cy="${sy(pose.player[1])}" r="${radius}" fill="#f4f1ea"/>` : "",
      pose.boss ? `<circle cx="${sx(pose.boss[0])}" cy="${sy(pose.boss[1])}" r="${Math.round(radius * 1.35)}" fill="#d4836a"/>` : "",
      `<circle cx="${sx(pose.camera[0])}" cy="${sy(pose.camera[1])}" r="${radius}" fill="#8fd0c8"/>`
    ].join("");
    const look = pose.look
      ? `<line x1="${sx(pose.camera[0])}" y1="${sy(pose.camera[1])}" x2="${sx(pose.look[0])}" y2="${sy(pose.look[1])}" stroke="#8fd0c8" stroke-width="${Math.max(4, font / 8)}" stroke-dasharray="${font} ${font}"/>`
      : "";
    map.innerHTML = `
      <rect x="-1400" y="${sy(1500)}" width="2880" height="3000" fill="none" stroke="#8fd0c8" stroke-width="${Math.max(4, font / 10)}" stroke-dasharray="${font} ${Math.round(font * 0.7)}"/>
      ${look}${dots}
      <text x="${minX + font}" y="${-maxY + font * 1.6}" font-size="${font}" fill="#c9c3b6">near</text>
      <text x="${maxX - font * 3}" y="${-maxY + font * 1.6}" font-size="${font}" fill="#c9c3b6">far</text>`;
    document.querySelector("#pose-note").textContent =
      `${pose.name}. Camera ${fmt(pose.camera)}. Look ${fmt(pose.look)}. Player ${fmt(pose.player)}. Boss ${fmt(pose.boss)}. ${pose.note}`;
  }
  drawPose("start");
  poseBar.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    poseBar.querySelectorAll(".chip").forEach((chip) => chip.classList.remove("on"));
    button.classList.add("on");
    drawPose(button.dataset.pose);
  });

  const timeBar = document.querySelector("#time-bar");
  timeBar.innerHTML = BRIEF.beats.map((beat, index) =>
    `<button class="chip ${index === 0 ? "on" : ""}" data-beat="${index}">${beat.t} ${beat.title}</button>`
  ).join("");
  const beatNote = document.querySelector("#beat-note");
  function showBeat(index) {
    const beat = BRIEF.beats[index];
    beatNote.textContent = `${beat.t} ${beat.title}. ${beat.text}`;
  }
  showBeat(0);
  timeBar.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    timeBar.querySelectorAll(".chip").forEach((chip) => chip.classList.remove("on"));
    button.classList.add("on");
    showBeat(Number(button.dataset.beat));
  });

  const search = document.querySelector("#search");
  search.addEventListener("input", () => {
    const query = search.value.trim().toLowerCase();
    document.querySelectorAll(".retired-card, #conflicts .fact, .cite").forEach((node) => {
      const hit = !query || node.textContent.toLowerCase().includes(query);
      node.classList.toggle("hidden", !hit);
    });
  });

  let savedIds = [];
  try { savedIds = JSON.parse(localStorage.getItem(storeKey) || "[]"); } catch (error) { savedIds = []; }
  const saved = new Set(savedIds);
  const checks = document.querySelector("#checks");
  checks.innerHTML = BRIEF.checks.map((item) =>
    `<label class="check"><input type="checkbox" data-id="${item.id}" ${saved.has(item.id) ? "checked" : ""}> <span><span class="tag">${item.desk}</span> ${item.text}</span></label>`
  ).join("");
  function paintProgress() {
    const boxes = [...checks.querySelectorAll("input")];
    const done = boxes.filter((box) => box.checked).length;
    document.querySelector("#bar").style.width = `${(done / boxes.length) * 100}%`;
    document.querySelector("#count").textContent = `${done} of ${boxes.length} build checks ticked in this browser.`;
  }
  checks.addEventListener("change", () => {
    const ids = [...checks.querySelectorAll("input:checked")].map((box) => box.dataset.id);
    try { localStorage.setItem(storeKey, JSON.stringify(ids)); } catch (error) { /* private file view */ }
    paintProgress();
  });
  paintProgress();

  const links = [...nav.querySelectorAll("a")];
  const observed = sections.map(([id]) => document.getElementById(id));
  const spy = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      links.forEach((link) => link.classList.toggle("active", link.getAttribute("href") === `#${entry.target.id}`));
    });
  }, { rootMargin: "-20% 0px -70% 0px" });
  observed.forEach((section) => spy.observe(section));
})();
