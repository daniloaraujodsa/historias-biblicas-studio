document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("form[data-busy]").forEach((form) => {
    form.addEventListener("submit", () => {
      const btn = form.querySelector('button[type="submit"]');
      if (btn) {
        btn.classList.add("is-busy");
        btn.disabled = true;
        btn.textContent = "Processando… aguarde";
      }
    });
  });
});
