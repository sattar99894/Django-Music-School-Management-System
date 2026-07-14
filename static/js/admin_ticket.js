/* ============================================================
   Admin ticket — AJAX reply + close.
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

  const STATUS_CLASS = {
    OPEN: "bg-amber-100 text-amber-700",
    ANSWERED: "bg-green-100 text-green-700",
    CLOSED: "bg-stone-100 text-stone-500",
  };

  // ---------- Reply ----------
  const replyForm = document.getElementById("reply-form");
  if (replyForm) {
    replyForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const input = document.getElementById("reply-input");
      const btn = document.getElementById("reply-submit");
      const msg = input.value.trim();
      const errEl = document.querySelector('[data-error="message"]');

      if (msg.length < 2) {
        if (errEl) {
          errEl.textContent = "پیام نمی‌تواند خالی باشد.";
          errEl.classList.remove("hidden");
        }
        return;
      }
      if (errEl) errEl.classList.add("hidden");

      btn.disabled = true;
      btn.innerHTML =
        '<svg class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path></svg> در حال ارسال...';

      try {
        const res = await fetch(window.API.reply, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: JSON.stringify({ message: msg }),
        });
        const json = await res.json();
        if (json.ok) {
          appendMessage(json.message);
          input.value = "";
          showToast("پاسخ ارسال شد.", true);
          // Update ticket status badge
          updateStatusBadge(json.ticket_status, json.ticket_status_label);
        } else {
          if (json.errors && json.errors.message && errEl) {
            errEl.textContent = json.errors.message;
            errEl.classList.remove("hidden");
          } else {
            showToast("خطا در ارسال پاسخ", false);
          }
        }
      } catch (err) {
        showToast("خطای شبکه", false);
      } finally {
        btn.disabled = false;
        btn.innerHTML =
          '<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/></svg> ارسال پاسخ';
      }
    });

    function appendMessage(m) {
      const list = document.getElementById("msg-list");
      const empty = list.querySelector("p");
      if (empty) empty.remove();
      const wrap = document.createElement("div");
      wrap.className = "flex justify-end"; // admin messages on the right
      wrap.innerHTML =
        '<div class="max-w-[75%] rounded-2xl bg-stone-800 px-4 py-3 text-sm text-white">' +
        '<div class="mb-1 text-xs font-semibold opacity-80">' + escapeHtml(m.sender_name) + " · مدیریت</div>" +
        '<div class="whitespace-pre-line leading-6">' + escapeHtml(m.body) + "</div>" +
        '<div class="mt-1 text-[10px] text-white/60">' + escapeHtml(m.created_at_persian) + "</div>" +
        "</div>";
      list.appendChild(wrap);
      list.scrollTop = list.scrollHeight;
    }

    function updateStatusBadge(status, label) {
      const badge = document.getElementById("ticket-status-badge");
      if (!badge) return;
      badge.textContent = label;
      badge.className =
        "rounded-full px-3 py-1 text-xs font-medium " +
        (STATUS_CLASS[status] || "bg-stone-100 text-stone-500");
    }
  }

  // ---------- Close ticket ----------
  const closeBtn = document.getElementById("close-ticket-btn");
  if (closeBtn) {
    closeBtn.addEventListener("click", async function () {
      if (!confirm("آیا از بستن این تیکت مطمئن هستید؟")) return;
      closeBtn.disabled = true;
      closeBtn.textContent = "...";
      try {
        const res = await fetch(closeBtn.dataset.url, {
          method: "POST",
          headers: { "X-CSRFToken": getCookie("csrftoken") },
        });
        const json = await res.json();
        if (json.ok) {
          // Update badge + remove close button
          const badge = document.getElementById("ticket-status-badge");
          if (badge) {
            badge.textContent = json.ticket_status_label;
            badge.className =
              "rounded-full px-3 py-1 text-xs font-medium " +
              (STATUS_CLASS[json.ticket_status] || "bg-stone-100 text-stone-500");
          }
          closeBtn.remove();
          showToast("تیکت بسته شد.", true);
        } else {
          showToast("خطا در بستن تیکت", false);
          closeBtn.disabled = false;
          closeBtn.textContent = "بستن تیکت";
        }
      } catch (err) {
        showToast("خطای شبکه", false);
        closeBtn.disabled = false;
        closeBtn.textContent = "بستن تیکت";
      }
    });
  }
})();
