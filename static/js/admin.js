/* ============================================================
   Admin panel — AJAX for directory search/filter/sort
   and class add/remove student modal.

   All user input rendered via escapeHtml to prevent XSS.
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
  // DIRECTORY — debounced AJAX search/filter/sort
  // ============================================================
  const dirForm = document.getElementById("dir-form");
  if (dirForm) {
    const tbody = document.getElementById("dir-tbody");
    const resultCount = document.getElementById("result-count");
    const statusDot = document.getElementById("status-dot");
    const statusText = document.getElementById("status-text");
    const roleInput = document.getElementById("f-role");
    let timer = null;

    function collectParams() {
      const params = new URLSearchParams();
      params.set("q", document.getElementById("f-q").value.trim());
      params.set("skill_level", document.getElementById("f-skill").value);
      params.set("instrument", document.getElementById("f-instrument").value);
      params.set("sort", document.getElementById("f-sort").value);
      params.set("date_from", document.getElementById("f-date-from").value);
      params.set("date_to", document.getElementById("f-date-to").value);
      params.set("role", roleInput.value);
      params.set("ajax", "1");
      return params;
    }

    function setLoading(on) {
      if (statusDot) {
        statusDot.className =
          "inline-block h-2 w-2 rounded-full " +
          (on ? "bg-amber-400 animate-pulse" : "bg-green-400");
      }
      if (statusText) statusText.textContent = on ? "در حال جستجو..." : "به‌روز";
    }

    async function fetchResults() {
      setLoading(true);
      try {
        const res = await fetch(window.API.directory + "?" + collectParams().toString(), {
          headers: { "X-Requested-With": "XMLHttpRequest" },
        });
        const html = await res.text();
        tbody.innerHTML = html;
        // count rows (exclude the empty-state row)
        const rows = tbody.querySelectorAll("tr:not(:first-child)");
        // Actually count all <tr> that have <td> (not the colspan empty row)
        const realRows = tbody.querySelectorAll("tr").length;
        const isEmpty = tbody.querySelector("td[colspan]");
        if (resultCount)
          resultCount.textContent = isEmpty ? "0" : String(realRows);
      } catch (err) {
        showToast("خطای شبکه در جستجو", false);
      } finally {
        setLoading(false);
      }
    }

    function debouncedFetch() {
      clearTimeout(timer);
      timer = setTimeout(fetchResults, 350);
    }

    // Wire up all form controls
    ["f-q", "f-skill", "f-instrument", "f-sort", "f-date-from", "f-date-to"].forEach(
      (id) => {
        const el = document.getElementById(id);
        if (el) {
          el.addEventListener("input", debouncedFetch);
          el.addEventListener("change", debouncedFetch);
        }
      }
    );

    // Role tabs
    document.querySelectorAll(".role-tab").forEach((btn) => {
      btn.addEventListener("click", function () {
        const role = this.dataset.role;
        roleInput.value = role;
        // Update tab styles
        document.querySelectorAll(".role-tab").forEach((b) => {
          if (b.dataset.role === role) {
            b.className =
              "role-tab rounded-lg px-4 py-2 text-sm font-medium transition brand-gradient text-white";
          } else {
            b.className =
              "role-tab rounded-lg px-4 py-2 text-sm font-medium transition text-stone-600 hover:bg-stone-100";
          }
        });
        // When switching roles, skill/instrument filters are student-only;
        // the server handles it, just refetch.
        fetchResults();
      });
    });
  }

  // ============================================================
  // CLASS DETAIL — add student modal + remove student
  // ============================================================
  const addModal = document.getElementById("add-modal");
  if (addModal) {
    const searchInput = document.getElementById("student-search-input");
    const resultsDiv = document.getElementById("search-results");
    const selectedBox = document.getElementById("selected-student");
    const selectedName = document.getElementById("selected-name");
    const confirmBtn = document.getElementById("confirm-add");
    let selectedStudentId = null;
    let searchTimer = null;

    function openModal() {
      addModal.classList.remove("hidden");
      addModal.classList.add("flex");
      searchInput.value = "";
      resultsDiv.innerHTML =
        '<p class="py-4 text-center text-xs text-stone-400">برای جستجو تایپ کنید...</p>';
      selectedBox.classList.add("hidden");
      selectedStudentId = null;
      confirmBtn.disabled = true;
      setTimeout(() => searchInput.focus(), 100);
    }
    function closeModal() {
      addModal.classList.add("hidden");
      addModal.classList.remove("flex");
    }

    document.getElementById("open-add-modal").addEventListener("click", openModal);
    document.getElementById("close-add-modal").addEventListener("click", closeModal);
    document.getElementById("cancel-add").addEventListener("click", closeModal);
    addModal.addEventListener("click", function (e) {
      if (e.target === addModal) closeModal();
    });

    // Student search (debounced)
    searchInput.addEventListener("input", function () {
      clearTimeout(searchTimer);
      const q = this.value.trim();
      if (q.length < 2) {
        resultsDiv.innerHTML =
          '<p class="py-4 text-center text-xs text-stone-400">حداقل ۲ کاراکتر تایپ کنید...</p>';
        return;
      }
      searchTimer = setTimeout(async () => {
        try {
          const res = await fetch(
            window.API.search + "&q=" + encodeURIComponent(q)
          );
          const json = await res.json();
          if (json.ok && json.students.length) {
            resultsDiv.innerHTML = json.students
              .map(
                (s) =>
                  '<button type="button" class="pick-student block w-full rounded-lg border border-stone-200 p-2.5 text-right text-sm transition hover:border-brand-300 hover:bg-brand-50" data-id="' +
                  s.id +
                  '" data-name="' +
                  escapeHtml(s.full_name) +
                  '" data-phone="' +
                  escapeHtml(s.phone) +
                  '">' +
                  '<div class="font-medium text-stone-900">' +
                  escapeHtml(s.full_name) +
                  "</div>" +
                  '<div class="text-xs text-stone-500" dir="ltr">' +
                  escapeHtml(s.phone) +
                  " · " +
                  escapeHtml(s.instrument) +
                  "</div>" +
                  "</button>"
              )
              .join("");
          } else {
            resultsDiv.innerHTML =
              '<p class="py-4 text-center text-xs text-stone-400">دانشجویی یافت نشد.</p>';
          }
        } catch (err) {
          resultsDiv.innerHTML =
            '<p class="py-4 text-center text-xs text-red-500">خطای شبکه</p>';
        }
      }, 300);
    });

    // Select a student from results
    resultsDiv.addEventListener("click", function (e) {
      const btn = e.target.closest(".pick-student");
      if (!btn) return;
      selectedStudentId = btn.dataset.id;
      selectedName.textContent = btn.dataset.name;
      selectedBox.classList.remove("hidden");
      confirmBtn.disabled = false;
    });

    document.getElementById("clear-selection").addEventListener("click", function () {
      selectedStudentId = null;
      selectedBox.classList.add("hidden");
      confirmBtn.disabled = true;
    });

    // Confirm add
    confirmBtn.addEventListener("click", async function () {
      if (!selectedStudentId) return;
      confirmBtn.disabled = true;
      confirmBtn.textContent = "در حال افزودن...";
      try {
        const res = await fetch(window.API.add, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: JSON.stringify({ student_id: parseInt(selectedStudentId) }),
        });
        const json = await res.json();
        if (json.ok) {
          showToast(json.message, true);
          // Append the new row to the table
          appendEnrollmentRow(json.enrollment);
          closeModal();
        } else {
          showToast(json.error || "خطا در افزودن", false);
        }
      } catch (err) {
        showToast("خطای شبکه", false);
      } finally {
        confirmBtn.disabled = false;
        confirmBtn.textContent = "تأیید و افزودن";
      }
    });

    function appendEnrollmentRow(enr) {
      const tbody = document.getElementById("enrollments-tbody");
      // remove empty-state row if present
      const emptyRow = tbody.querySelector("td[colspan]");
      if (emptyRow) emptyRow.closest("tr").remove();

      const tr = document.createElement("tr");
      tr.dataset.enrollmentId = enr.id;
      tr.className = "transition hover:bg-stone-50";
      tr.innerHTML =
        '<td class="px-4 py-3"><a href="' +
        escapeHtml(enr.detail_url) +
        '" class="font-medium text-stone-900 hover:text-brand-600">' +
        escapeHtml(enr.student_name) +
        "</a></td>" +
        '<td class="px-4 py-3 text-stone-500" dir="ltr">' +
        escapeHtml(enr.student_phone) +
        "</td>" +
        '<td class="px-4 py-3 text-stone-500">' +
        escapeHtml(enr.term) +
        "</td>" +
        '<td class="px-4 py-3 text-center"><span class="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">' +
        escapeHtml(enr.status_label) +
        "</span></td>" +
        '<td class="px-4 py-3 text-center"><div class="flex items-center justify-center gap-1">' +
        '<a href="' +
        escapeHtml(enr.detail_url) +
        '" class="rounded-md border border-stone-300 px-2.5 py-1 text-xs hover:bg-stone-100">مشخصات</a>' +
        '<button type="button" class="remove-btn rounded-md border border-red-300 px-2.5 py-1 text-xs text-red-600 hover:bg-red-50" data-url="' +
        escapeHtml(enr.remove_url) +
        '">حذف از کلاس</button>' +
        "</div></td>";
      tbody.prepend(tr);
    }

    // Remove student (event delegation on tbody)
    const enrTbody = document.getElementById("enrollments-tbody");
    if (enrTbody) {
      enrTbody.addEventListener("click", async function (e) {
        const btn = e.target.closest(".remove-btn");
        if (!btn) return;
        if (!confirm("آیا از حذف این دانشجو از کلاس مطمئن هستید؟")) return;

        const row = btn.closest("tr");
        btn.disabled = true;
        btn.textContent = "...";
        try {
          const res = await fetch(btn.dataset.url, {
            method: "POST",
            headers: { "X-CSRFToken": getCookie("csrftoken") },
          });
          const json = await res.json();
          if (json.ok) {
            showToast(json.message, true);
            row.remove();
          } else {
            showToast(json.error || "خطا در حذف", false);
            btn.disabled = false;
            btn.textContent = "حذف از کلاس";
          }
        } catch (err) {
          showToast("خطای شبکه", false);
          btn.disabled = false;
          btn.textContent = "حذف از کلاس";
        }
      });
    }
  }
})();
