document.addEventListener("DOMContentLoaded", function () {
  // Fokus otomatis pada ringkasan alert error dari server jika ada
  const serverAlert = document.querySelector('[role="alert"][data-autofocus="true"]');
  if (serverAlert) {
    serverAlert.focus();
  }

  // Tampilkan/sembunyikan password pada halaman Masuk & Daftar.
  // Diletakkan sebelum return di bawah supaya tetap jalan di halaman tanpa form pindai.
  document.querySelectorAll("[data-password-toggle]").forEach(function (btn) {
    const input = document.getElementById(btn.getAttribute("data-password-toggle"));
    if (!input) return;
    const icons = btn.querySelectorAll(".password-toggle-icon");
    btn.addEventListener("click", function () {
      const reveal = input.type === "password";
      input.type = reveal ? "text" : "password";
      btn.setAttribute("aria-pressed", reveal ? "true" : "false");
      btn.setAttribute("aria-label", reveal ? "Sembunyikan password" : "Tampilkan password");
      icons[0].classList.toggle("is-visible", reveal);
      icons[1].classList.toggle("is-visible", !reveal);
      input.focus();
    });
  });

  // Modal autentikasi: dibuka di atas halaman yang sedang dibuka, dengan latar diredupkan.
  // Tanpa JavaScript, status buka sudah ditentukan server lewat active_page, jadi
  // /login dan /register tetap tampil sebagai modal.
  let activeModal = document.querySelector(".modal-overlay.is-open");
  let modalPushed = false;
  let lastFocused = null;

  if (activeModal) {
    document.body.classList.add("has-modal");
  }

  function focusablesIn(scope) {
    return scope.querySelectorAll(
      "a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled])",
    );
  }

  function openAuthModal(name, pushUrl) {
    const overlay = document.getElementById("auth-modal-" + name);
    if (!overlay) return false;
    const prevModal = activeModal;
    const trigger = document.activeElement;
    // Pemicu disimpan hanya bila berasal dari luar dialog, bukan saat pindah antar dialog.
    if (!prevModal || !prevModal.contains(trigger)) {
      lastFocused = trigger;
    }
    if (prevModal) prevModal.classList.remove("is-open");
    activeModal = overlay;
    overlay.classList.add("is-open");
    document.body.classList.add("has-modal");
    const first = overlay.querySelector("input:not([type=hidden])") || focusablesIn(overlay)[0];
    if (first) first.focus();
    if (pushUrl && window.history && window.history.pushState) {
      window.history.pushState({ authModal: name }, "", pushUrl);
      modalPushed = true;
    }
    return true;
  }

  function closeAuthModal() {
    if (!activeModal) return;
    activeModal.classList.remove("is-open");
    activeModal = null;
    document.body.classList.remove("has-modal");
    if (lastFocused && lastFocused.focus) lastFocused.focus();
    lastFocused = null;
  }

  function dismissAuthModal() {
    if (modalPushed) {
      modalPushed = false;
      window.history.back();
      return;
    }
    // Modal dibuka lewat navigasi server (mis. /login langsung): kembali ke halaman asal.
    closeAuthModal();
    const ref = document.referrer;
    if (ref && new URL(ref, location.href).origin === location.origin) {
      location.href = ref;
    } else {
      location.href = "/";
    }
  }

  document.querySelectorAll("[data-auth-open]").forEach(function (link) {
    link.addEventListener("click", function (e) {
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
      if (openAuthModal(link.getAttribute("data-auth-open"), link.getAttribute("href"))) {
        e.preventDefault();
      }
    });
  });

  document.querySelectorAll("[data-auth-close]").forEach(function (btn) {
    btn.addEventListener("click", dismissAuthModal);
  });

  document.querySelectorAll(".modal-overlay").forEach(function (overlay) {
    overlay.addEventListener("mousedown", function (e) {
      if (e.target === overlay) dismissAuthModal();
    });
  });

  document.addEventListener("keydown", function (e) {
    if (!activeModal) return;
    if (e.key === "Escape") {
      e.preventDefault();
      dismissAuthModal();
      return;
    }
    if (e.key !== "Tab") return;
    const items = focusablesIn(activeModal);
    if (!items.length) return;
    const first = items[0];
    const last = items[items.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  });

  window.addEventListener("popstate", function () {
    if (!activeModal) return;
    modalPushed = false;
    closeAuthModal();
  });

  const scanForm = document.getElementById("scan-form");
  const fileInput = document.getElementById("image-file-input");
  const dropzone = document.getElementById("upload-dropzone");
  const previewContainer = document.getElementById("file-preview-container");
  const previewThumb = document.getElementById("file-preview-thumb");
  const previewName = document.getElementById("file-preview-name");
  const previewSize = document.getElementById("file-preview-size");
  const clearBtn = document.getElementById("clear-file-btn");
  const clientErrorBox = document.getElementById("client-error-box");
  const clientErrorText = document.getElementById("client-error-text");
  const submitBtn = document.getElementById("scan-submit-btn");

  if (!scanForm || !fileInput) return;

  const MAX_BYTES = 10 * 1024 * 1024;
  const VALID_EXT = [".jpg", ".jpeg", ".png"];

  function showError(msg) {
    clientErrorText.textContent = msg;
    clientErrorBox.hidden = false;
    fileInput.setAttribute("aria-invalid", "true");
  }

  function clearError() {
    clientErrorText.textContent = "";
    clientErrorBox.hidden = true;
    fileInput.removeAttribute("aria-invalid");
  }

  function formatSizeKB(bytes) {
    const kb = (bytes / 1024).toFixed(1).replace(".", ",");
    return kb + " KB";
  }

  function validateAndPreviewFile(file) {
    clearError();
    if (!file) {
      previewContainer.hidden = true;
      return false;
    }

    const lowerName = file.name.toLowerCase();
    const hasValidExt = VALID_EXT.some((ext) => lowerName.endsWith(ext));
    if (!hasValidExt) {
      showError("Format harus JPG, JPEG, atau PNG.");
      previewContainer.hidden = true;
      return false;
    }

    if (file.size > MAX_BYTES) {
      showError("Ukuran file melebihi 10 MB.");
      previewContainer.hidden = true;
      return false;
    }

    previewName.textContent = file.name;
    previewSize.textContent = formatSizeKB(file.size);
    previewContainer.hidden = false;

    const reader = new FileReader();
    reader.onload = function (e) {
      previewThumb.src = e.target.result;
    };
    reader.readAsDataURL(file);
    return true;
  }

  fileInput.addEventListener("change", function () {
    if (fileInput.files.length > 1) {
      showError("Pilih satu file gambar.");
      return;
    }
    validateAndPreviewFile(fileInput.files[0]);
  });

  if (dropzone) {
    ["dragenter", "dragover"].forEach((evt) => {
      dropzone.addEventListener(evt, function (e) {
        e.preventDefault();
        dropzone.classList.add("is-dragover");
      });
    });

    ["dragleave", "drop"].forEach((evt) => {
      dropzone.addEventListener(evt, function () {
        dropzone.classList.remove("is-dragover");
      });
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener("click", function () {
      fileInput.value = "";
      previewContainer.hidden = true;
      clearError();
      fileInput.focus();
    });
  }

  scanForm.addEventListener("submit", function (e) {
    if (!fileInput.files || fileInput.files.length === 0) {
      e.preventDefault();
      showError("Pilih satu file gambar.");
      return;
    }
    const isOk = validateAndPreviewFile(fileInput.files[0]);
    if (!isOk) {
      e.preventDefault();
      return;
    }
    submitBtn.disabled = true;
    submitBtn.setAttribute("aria-busy", "true");
    submitBtn.innerHTML = '<span class="spinner" aria-hidden="true"></span> Menganalisis…';
  });

  // Reset tombol loading jika halaman dimuat ulang (misal tombol kembali browser setelah error)
  if (submitBtn) {
    submitBtn.disabled = false;
    submitBtn.removeAttribute("aria-busy");
    submitBtn.innerHTML = 'Pindai gambar';
  }
});
