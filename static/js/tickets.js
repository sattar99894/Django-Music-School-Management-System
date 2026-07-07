/* ============================================================
   Tickets — AJAX (Fetch API) for create + reply.
   Reads the CSRF token from the `csrftoken` cookie (Django convention)
   and POSTs JSON. All user input is escaped before injection.
   ============================================================ */

(function () {
  "use strict";

  // ---------- helpers ----------
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
  function setFieldError(name, msg) {
    const el = document.querySelector('[data-error="' + name + '"]');
    if (!el) return;
    if (msg) {
      el.textContent = msg;
      el.classList.remove("hidden");
    } else {
      el.classList.add("hidden");
    }
  }

  // ---------- priority badge colours ----------
  const PRIORITY_CLASS = {
    LOW: "bg-stone-100 text-stone-600",
    NORMAL: "bg-stone-100 text-stone-600",
    HIGH: "bg-red-50 text-red-600",
    URGENT: "bg-red-50 text-red-600",
  };
  const STATUS_CLASS = {
    OPEN: "bg-amber-100 text-amber-700",
    ANSWERED: "bg-green-100 text-green-700",
    CLOSED: "bg-stone-100 text-stone-500",
  };

  // ---------- create ticket ----------
  const form = document.getElementById("ticket-form");
  if (form) {
    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      const btn = document.getElementById("ticket-submit");
      const data = {
        title: form.title.value.trim(),
        priority: form.priority.value,
        category: form.category.value,
        description: form.description.value.trim(),
      };
      setFieldError("title", "");
      setFieldError("description", "");

      btn.disabled = true;
      btn.textContent = "در حال ثبت...";
      try {
        const res = await fetch(window.API.createTicket, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: JSON.stringify(data),
        });
        const json = await res.json();
        if (json.ok) {
          prependTicket(json.ticket);
          form.reset();
          showToast("تیکت با موفقیت ثبت شد.", true);
        } else {
          Object.entries(json.errors || {}).forEach(([k, v]) => setFieldError(k, v));
          if (json.errors && json.errors.__all__) showToast(json.errors.__all__, false);
        }
      } catch (err) {
        showToast("خطای شبکه — دوباره تلاش کنید.", false);
      } finally {
        btn.disabled = false;
        btn.textContent = "ثبت تیکت";
      }
    });

    function prependTicket(t) {
      const empty = document.getElementById("ticket-empty");
      if (empty) empty.remove();
      const list = document.getElementById("ticket-list");
      const card = document.createElement("a");
      card.href = t.url;
      card.className =
        "block rounded-xl border border-stone-200 bg-white p-4 transition hover:border-brand-300 hover:shadow-sm";
      card.innerHTML =
        '<div class="flex items-start justify-between gap-3">' +
          '<div class="min-w-0">' +
            '<div class="font-semibold text-stone-900">' + escapeHtml(t.title) + '</div>' +
            '<div class="mt-1 line-clamp-1 text-sm text-stone-500">' + escapeHtml(t.description) + '</div>' +
          '</div>' +
          '<div class="flex shrink-0 flex-col items-end gap-1">' +
            '<span class="rounded-full px-2 py-0.5 text-xs ' + (STATUS_CLASS[t.status] || "bg-stone-100") + '">' +
              escapeHtml(t.status_label) +
            '</span>' +
            '<span class="text-xs text-stone-400">' + escapeHtml(t.created_at_persian) + '</span>' +
          '</div>' +
        '</div>' +
        '<div class="mt-3 flex flex-wrap gap-2">' +
          '<span class="rounded-md bg-stone-100 px-2 py-0.5 text-xs text-stone-600">' + escapeHtml(t.category_label) + '</span>' +
          '<span class="rounded-md px-2 py-0.5 text-xs ' + (PRIORITY_CLASS[t.priority] || "bg-stone-100") + '">اولویت: ' + escapeHtml(t.priority_label) + '</span>' +
        '</div>';
      list.prepend(card);
    }
  }

  // ---------- reply ----------
  const replyForm = document.getElementById("reply-form");
  if (replyForm) {
    replyForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const input = document.getElementById("reply-input");
      const btn = document.getElementById("reply-submit");
      const msg = input.value.trim();
      if (msg.length < 2) {
        setFieldError("message", "پیام نمی‌تواند خالی باشد.");
        return;
      }
      setFieldError("message", "");
      btn.disabled = true;
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
          showToast("پیام ارسال شد.", true);
        } else {
          Object.entries(json.errors || {}).forEach(([k, v]) => setFieldError(k, v));
        }
      } catch (err) {
        showToast("خطای شبکه — دوباره تلاش کنید.", false);
      } finally {
        btn.disabled = false;
      }
    });

    function appendMessage(m) {
      const list = document.getElementById("msg-list");
      // remove empty-state if present
      const empty = list.querySelector("p");
      if (empty) empty.remove();
      const wrap = document.createElement("div");
      const isMe = m.is_me !== false; // server sets is_me=true for student replies
      wrap.className = "flex " + (isMe ? "justify-start" : "justify-end");
      wrap.innerHTML =
        '<div class="max-w-[80%] rounded-2xl px-4 py-3 text-sm ' +
          (isMe ? "brand-gradient text-white" : "bg-stone-100 text-stone-800") + '">' +
          '<div class="whitespace-pre-line leading-6">' + escapeHtml(m.body) + '</div>' +
          '<div class="mt-1 text-[10px] ' + (isMe ? "text-white/70" : "text-stone-400") + '">' +
            escapeHtml(m.created_at_persian) +
          '</div>' +
        '</div>';
      list.appendChild(wrap);
      list.scrollTop = list.scrollHeight;
    }
  }
})();
