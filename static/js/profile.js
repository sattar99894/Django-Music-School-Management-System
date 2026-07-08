/* ============================================================
   Profile — AJAX add/remove instruments & experiences.
   Uses Fetch API + CSRF cookie. All user input is escaped.
   ============================================================ */
(function () {
  "use strict";

  function getCookie(name) {
    const m = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return m ? m.pop() : "";
  }
  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }
  function showToast(msg, ok) {
    const t = document.getElementById("toast");
    if (!t) return;
    const inner = t.querySelector("div");
    inner.textContent = msg;
    inner.style.background = ok ? "#15803d" : "#b91c1c";
    t.classList.remove("hidden");
    clearTimeout(t._timer);
    t._timer = setTimeout(() => t.classList.add("hidden"), 2500);
  }

  // ============================================================
  // Instruments
  // ============================================================
  const addInstBtn = document.getElementById("add-instrument-btn");
  if (addInstBtn) {
    addInstBtn.addEventListener("click", async function () {
      const data = {
        instrument: document.getElementById("inst-instrument").value,
        skill_level: document.getElementById("inst-skill").value,
        started_year: document.getElementById("inst-year").value || null,
        is_primary: document.getElementById("inst-primary").checked,
      };
      const errEl = document.getElementById("inst-error");
      errEl.classList.add("hidden");

      if (!data.instrument) {
        errEl.textContent = "لطفاً یک ساز انتخاب کنید.";
        errEl.classList.remove("hidden");
        return;
      }

      addInstBtn.disabled = true;
      addInstBtn.textContent = "در حال افزودن...";
      try {
        const res = await fetch(window.API.addInstrument, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: JSON.stringify(data),
        });
        const json = await res.json();
        if (json.ok) {
          appendInstrument(json.instrument_profile);
          // reset form
          document.getElementById("inst-instrument").value = "";
          document.getElementById("inst-year").value = "";
          document.getElementById("inst-primary").checked = false;
          showToast("ساز با موفقیت افزوده شد.", true);
        } else {
          if (json.errors) {
            errEl.textContent = Object.values(json.errors).join(" / ");
          } else {
            errEl.textContent = json.error || "خطا در افزودن.";
          }
          errEl.classList.remove("hidden");
        }
      } catch (err) {
        showToast("خطای شبکه", false);
      } finally {
        addInstBtn.disabled = false;
        addInstBtn.textContent = "افزودن ساز";
      }
    });

    function appendInstrument(ip) {
      const list = document.getElementById("instruments-list");
      const empty = list.querySelector("p");
      if (empty) empty.remove();

      // If this is marked primary, remove primary star from others in UI.
      if (ip.is_primary) {
        list.querySelectorAll("[data-instrument-id]").forEach((el) => {
          const star = el.querySelector(".text-amber-500");
          if (star) star.remove();
        });
      }

      const div = document.createElement("div");
      div.dataset.instrumentId = ip.id;
      div.className = "flex items-center justify-between rounded-xl border border-stone-200 p-3";
      div.innerHTML =
        '<div class="flex items-center gap-3">' +
          '<span class="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-600">' +
            '<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 19V6l12-3v13M9 19c0 1.657-1.343 3-3 3s-3-1.343-3-3 1.343-3 3-3 3 1.343 3 3zm12-3c0 1.657-1.343 3-3 3s-3-1.343-3-3 1.343-3 3-3 3 1.343 3 3z"/></svg>' +
          "</span>" +
          '<div><div class="flex items-center gap-1.5">' +
            '<span class="font-semibold text-stone-900">' + escapeHtml(ip.instrument_label) + "</span>" +
            (ip.is_primary ? '<span class="text-amber-500" title="ساز اصلی">★</span>' : "") +
          "</div>" +
          '<div class="text-xs text-stone-500">سطح: ' + escapeHtml(ip.skill_level_label) +
            (ip.started_year ? " · از سال " + escapeHtml(ip.started_year) : "") +
          "</div></div></div>" +
        '<button type="button" class="remove-instrument-btn rounded-md border border-red-300 px-2.5 py-1 text-xs text-red-600 hover:bg-red-50" data-url="' +
          window.API.addInstrument.replace("/add/", "/" + ip.id + "/remove/") +
        '">حذف</button>';
      list.appendChild(div);
    }

    // Remove instrument (event delegation)
    document.getElementById("instruments-list").addEventListener("click", async function (e) {
      const btn = e.target.closest(".remove-instrument-btn");
      if (!btn) return;
      if (!confirm("حذف این ساز از پروفایل؟")) return;
      const row = btn.closest("[data-instrument-id]");
      btn.disabled = true;
      try {
        const res = await fetch(btn.dataset.url, {
          method: "POST",
          headers: { "X-CSRFToken": getCookie("csrftoken") },
        });
        const json = await res.json();
        if (json.ok) {
          row.remove();
          showToast("ساز حذف شد.", true);
        } else {
          showToast("خطا در حذف", false);
          btn.disabled = false;
        }
      } catch (err) {
        showToast("خطای شبکه", false);
        btn.disabled = false;
      }
    });
  }

  // ============================================================
  // Experiences
  // ============================================================
  const addExpBtn = document.getElementById("add-experience-btn");
  if (addExpBtn) {
    addExpBtn.addEventListener("click", async function () {
      const data = {
        title: document.getElementById("exp-title").value.trim(),
        experience_type: document.getElementById("exp-type").value,
        description: document.getElementById("exp-description").value.trim(),
        event_date: document.getElementById("exp-date").value || null,
        location: document.getElementById("exp-location").value.trim(),
      };
      const errEl = document.getElementById("exp-error");
      errEl.classList.add("hidden");

      addExpBtn.disabled = true;
      addExpBtn.textContent = "در حال افزودن...";
      try {
        const res = await fetch(window.API.addExperience, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: JSON.stringify(data),
        });
        const json = await res.json();
        if (json.ok) {
          appendExperience(json.experience);
          document.getElementById("exp-title").value = "";
          document.getElementById("exp-description").value = "";
          document.getElementById("exp-date").value = "";
          document.getElementById("exp-location").value = "";
          showToast("سابقه با موفقیت افزوده شد.", true);
        } else {
          if (json.errors) {
            errEl.textContent = Object.values(json.errors).join(" / ");
          } else {
            errEl.textContent = json.error || "خطا در افزودن.";
          }
          errEl.classList.remove("hidden");
        }
      } catch (err) {
        showToast("خطای شبکه", false);
      } finally {
        addExpBtn.disabled = false;
        addExpBtn.textContent = "افزودن سابقه";
      }
    });

    function appendExperience(exp) {
      const list = document.getElementById("experiences-list");
      const empty = list.querySelector("p");
      if (empty) empty.remove();

      const div = document.createElement("div");
      div.dataset.experienceId = exp.id;
      div.className = "rounded-xl border border-stone-200 p-3";
      const removeUrl = window.API.addExperience.replace("/add/", "/" + exp.id + "/remove/");
      div.innerHTML =
        '<div class="flex items-start justify-between gap-2">' +
          '<div class="min-w-0"><div class="flex items-center gap-2">' +
            '<span class="font-semibold text-stone-900">' + escapeHtml(exp.title) + "</span>" +
            '<span class="rounded-full bg-brand-50 px-2 py-0.5 text-xs text-brand-600">' + escapeHtml(exp.experience_type_label) + "</span>" +
          "</div>" +
          (exp.event_date_persian || exp.location
            ? '<div class="mt-1 text-xs text-stone-500">' +
                escapeHtml(exp.event_date_persian || "") +
                (exp.event_date_persian && exp.location ? " · " : "") +
                escapeHtml(exp.location || "") +
              "</div>"
            : "") +
          (exp.description
            ? '<p class="mt-1 text-sm text-stone-600">' + escapeHtml(exp.description) + "</p>"
            : "") +
          "</div>" +
          '<button type="button" class="remove-experience-btn shrink-0 rounded-md border border-red-300 px-2.5 py-1 text-xs text-red-600 hover:bg-red-50" data-url="' +
            removeUrl + '">حذف</button>' +
        "</div>";
      list.appendChild(div);
    }

    // Remove experience (event delegation)
    document.getElementById("experiences-list").addEventListener("click", async function (e) {
      const btn = e.target.closest(".remove-experience-btn");
      if (!btn) return;
      if (!confirm("حذف این سابقه؟")) return;
      const row = btn.closest("[data-experience-id]");
      btn.disabled = true;
      try {
        const res = await fetch(btn.dataset.url, {
          method: "POST",
          headers: { "X-CSRFToken": getCookie("csrftoken") },
        });
        const json = await res.json();
        if (json.ok) {
          row.remove();
          showToast("سابقه حذف شد.", true);
        } else {
          showToast("خطا در حذف", false);
          btn.disabled = false;
        }
      } catch (err) {
        showToast("خطای شبکه", false);
        btn.disabled = false;
      }
    });
  }
})();
