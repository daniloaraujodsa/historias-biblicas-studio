document.addEventListener("DOMContentLoaded", () => {
  const dock = document.getElementById("job-dock");
  const projectId = document.body.dataset.projectId || dock?.dataset.projectId;
  let pollTimer = null;

  function collectScenes() {
    return [...document.querySelectorAll("#scene-editor .scene")].map((el) => ({
      index: Number(el.dataset.index),
      title: el.querySelector("[name=title]")?.value || "",
      text: el.querySelector("[name=text]")?.value || "",
      cast: el.querySelector("[name=cast]")?.value || "",
      duration_sec: el.querySelector("[name=duration_sec]")?.value || "",
    }));
  }

  async function saveScenes() {
    if (!projectId || !document.getElementById("scene-editor")) return true;
    const status = document.getElementById("scenes-save-status");
    try {
      const res = await fetch(`/api/projects/${projectId}/scenes/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ scenes: collectScenes() }),
      });
      if (!res.ok) throw new Error("Falha ao salvar cenas");
      if (status) {
        status.hidden = false;
        status.textContent = "Cenas salvas.";
      }
      return true;
    } catch (err) {
      if (status) {
        status.hidden = false;
        status.textContent = err.message || "Não foi possível salvar as cenas.";
      }
      return false;
    }
  }

  document.getElementById("save-scenes")?.addEventListener("click", () => {
    saveScenes();
  });

  function setDock({ step, progress, status, error }) {
    if (!dock) return;
    dock.classList.add("is-visible");
    dock.hidden = false;
    dock.classList.toggle("is-busy", status === "running" || status === "queued");
    dock.classList.toggle("is-error", status === "error");
    const stepEl = document.getElementById("job-step");
    const pctEl = document.getElementById("job-pct");
    const fill = document.getElementById("job-bar-fill");
    const errEl = document.getElementById("job-error");
    const pct = Math.max(0, Math.min(100, Number(progress) || 0));
    if (stepEl) stepEl.textContent = step || (status === "error" ? "Erro" : "Em andamento");
    if (pctEl) pctEl.textContent = `${pct}%`;
    if (fill) fill.style.width = `${pct}%`;
    const bar = dock.querySelector(".job-bar");
    if (bar) bar.setAttribute("aria-valuenow", String(pct));
    if (errEl) {
      if (status === "error" && error) {
        errEl.hidden = false;
        errEl.textContent = error;
      } else {
        errEl.hidden = true;
        errEl.textContent = "";
      }
    }
  }

  function setBusy(busy) {
    document.querySelectorAll("form[data-job] button").forEach((btn) => {
      btn.disabled = busy;
      btn.classList.toggle("is-busy", busy);
    });
  }

  async function pollJob(jobId) {
    try {
      const res = await fetch(`/api/jobs/${jobId}`, { headers: { Accept: "application/json" } });
      if (!res.ok) return;
      const job = await res.json();
      setDock(job);
      if (job.status === "done") {
        clearInterval(pollTimer);
        pollTimer = null;
        setBusy(false);
        window.location.reload();
      } else if (job.status === "error") {
        clearInterval(pollTimer);
        pollTimer = null;
        setBusy(false);
      }
    } catch {
      /* keep polling */
    }
  }

  function startPolling(jobId) {
    if (!jobId) return;
    setBusy(true);
    setDock({ step: "Na fila", progress: 2, status: "queued" });
    if (pollTimer) clearInterval(pollTimer);
    pollJob(jobId);
    pollTimer = setInterval(() => pollJob(jobId), 900);
  }

  document.querySelectorAll("form[data-job]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (form.hasAttribute("data-save-scenes")) {
        await saveScenes();
      }
      const btn = form.querySelector('button[type="submit"]');
      if (btn) {
        btn.classList.add("is-busy");
        btn.disabled = true;
      }
      try {
        const res = await fetch(form.action, {
          method: "POST",
          body: new FormData(form),
          headers: { Accept: "application/json" },
        });
        if (!res.ok) throw new Error("Falha ao iniciar o processamento");
        const data = await res.json();
        startPolling(data.job_id);
      } catch (err) {
        setDock({ step: "Erro ao iniciar", progress: 0, status: "error", error: String(err) });
        setBusy(false);
      }
    });
  });

  document.querySelectorAll("form[data-save-scenes]:not([data-job])").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      await saveScenes();
      form.submit();
    });
  });

  const params = new URLSearchParams(window.location.search);
  const urlJob = params.get("job");
  const initialStatus = dock?.dataset.jobStatus;
  const initialId = urlJob || dock?.dataset.jobId;
  if (initialId && (urlJob || initialStatus === "running" || initialStatus === "queued")) {
    startPolling(initialId);
  } else if (dock && (initialStatus === "error" || initialStatus === "done")) {
    if (initialStatus === "error") {
      dock.classList.add("is-visible");
      dock.hidden = false;
    }
  }
});
