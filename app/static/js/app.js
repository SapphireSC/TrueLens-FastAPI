document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".meter-fill[data-width], .wh-auth-fill[data-width]").forEach(function (el) {
    setTimeout(function () {
      el.style.width = el.getAttribute("data-width") + "%";
    }, 120);
  });
  document.querySelectorAll(".prob-marker[data-left]").forEach(function (el) {
    setTimeout(function () {
      el.style.left = el.getAttribute("data-left") + "%";
    }, 120);
  });

  const siteHeader = document.getElementById("site-header");
  if (siteHeader) {
    window.addEventListener(
      "scroll",
      function () {
        if (window.scrollY > 16) {
          siteHeader.classList.add("is-scrolled");
        } else {
          siteHeader.classList.remove("is-scrolled");
        }
      },
      { passive: true }
    );
  }

  const revealItems = document.querySelectorAll(".reveal-on-scroll");
  if ("IntersectionObserver" in window && revealItems.length > 0) {
    const observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.08 }
    );
    revealItems.forEach(function (el) {
      observer.observe(el);
    });
  } else {
    revealItems.forEach(function (el) {
      el.classList.add("is-visible");
    });
  }

  const scanForm = document.getElementById("scan-form");
  const fileInput = document.getElementById("image-file-input");
  const dropzone = document.getElementById("upload-dropzone");
  const emptyState = document.getElementById("dropzone-empty-state");
  const previewContainer = document.getElementById("file-preview-container");
  const previewThumb = document.getElementById("file-preview-thumb");
  const previewName = document.getElementById("file-preview-name");
  const previewSize = document.getElementById("file-preview-size");
  const clearBtn = document.getElementById("clear-file-btn");
  const analyzingOverlay = document.getElementById("analyzing-overlay");
  const rightIdle = document.getElementById("right-idle-state");
  const rightLoading = document.getElementById("right-loading-state");
  const clientErrorBox = document.getElementById("client-error-box");
  const clientErrorText = document.getElementById("client-error-text");
  const submitBtn = document.getElementById("scan-submit-btn");

  if (!scanForm || !fileInput) return;

  const MAX_BYTES = 10 * 1024 * 1024;
  const VALID_EXT = [".jpg", ".jpeg", ".png", ".webp"];
  let isSubmittingAfterAnimation = false;

  function showError(msg) {
    if (clientErrorText && clientErrorBox) {
      clientErrorText.textContent = msg;
      clientErrorBox.hidden = false;
    }
    fileInput.setAttribute("aria-invalid", "true");
  }

  function clearError() {
    if (clientErrorText && clientErrorBox) {
      clientErrorText.textContent = "";
      clientErrorBox.hidden = true;
    }
    fileInput.removeAttribute("aria-invalid");
  }

  function formatSizeKB(bytes) {
    const kb = (bytes / 1024).toFixed(1).replace(".", ",");
    return kb + " KB";
  }

  function validateAndPreviewFile(file) {
    clearError();
    if (!file) {
      if (previewContainer) previewContainer.hidden = true;
      if (emptyState) emptyState.hidden = false;
      if (clearBtn) clearBtn.hidden = true;
      return false;
    }

    const lowerName = file.name.toLowerCase();
    const hasValidExt = VALID_EXT.some(function (ext) {
      return lowerName.endsWith(ext);
    });
    if (!hasValidExt) {
      showError("Format berkas harus JPG, JPEG, PNG, atau WebP.");
      return false;
    }

    if (file.size > MAX_BYTES) {
      showError("Ukuran berkas melebihi batas 10 MB.");
      return false;
    }

    if (emptyState) emptyState.hidden = true;
    if (previewContainer) previewContainer.hidden = false;
    if (clearBtn) clearBtn.hidden = false;

    if (previewName && previewSize) {
      previewName.textContent = file.name;
      previewSize.textContent = formatSizeKB(file.size);
    }

    if (previewThumb) {
      const reader = new FileReader();
      reader.onload = function (e) {
        previewThumb.src = e.target.result;
      };
      reader.readAsDataURL(file);
    }
    return true;
  }

  fileInput.addEventListener("change", function () {
    if (fileInput.files.length > 1) {
      showError("Pilih satu berkas gambar saja.");
      return;
    }
    validateAndPreviewFile(fileInput.files[0]);
  });

  if (dropzone) {
    ["dragenter", "dragover"].forEach(function (evt) {
      dropzone.addEventListener(evt, function (e) {
        e.preventDefault();
        dropzone.classList.add("is-dragover");
      });
    });

    ["dragleave", "drop"].forEach(function (evt) {
      dropzone.addEventListener(evt, function () {
        dropzone.classList.remove("is-dragover");
      });
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener("click", function () {
      fileInput.value = "";
      if (previewContainer) previewContainer.hidden = true;
      if (emptyState) emptyState.hidden = false;
      clearBtn.hidden = true;
      clearError();
    });
  }

  scanForm.addEventListener("submit", function (e) {
    if (isSubmittingAfterAnimation) return;

    if (!fileInput.files || fileInput.files.length === 0) {
      e.preventDefault();
      showError("Silakan pilih satu berkas gambar terlebih dahulu.");
      return;
    }
    const isOk = validateAndPreviewFile(fileInput.files[0]);
    if (!isOk) {
      e.preventDefault();
      return;
    }

    e.preventDefault();
    if (analyzingOverlay) analyzingOverlay.hidden = false;
    if (rightIdle) rightIdle.hidden = true;
    if (rightLoading) rightLoading.hidden = false;

    submitBtn.disabled = true;
    submitBtn.setAttribute("aria-busy", "true");
    submitBtn.innerHTML = '<span class="spinner" aria-hidden="true"></span> Menganalisis gambar Anda…';

    setTimeout(function () {
      isSubmittingAfterAnimation = true;
      scanForm.submit();
    }, 850);
  });
});
document.addEventListener("DOMContentLoaded", function () {
  const authDialog = document.getElementById("auth-dialog");

  function firstInput(container) {
    return container ? container.querySelector("input:not([type='hidden'])") : null;
  }

  function clearAlerts(view) {
    if (!view) return;
    view.querySelectorAll("[data-auth-error], [data-auth-success]").forEach(function (el) {
      el.hidden = true;
      const text = el.querySelector("[data-auth-error-text], [data-auth-success-text]");
      if (text) text.textContent = "";
    });
  }

  function showAlert(view, kind, message) {
    if (!view) return;
    const el = view.querySelector(kind === "error" ? "[data-auth-error]" : "[data-auth-success]");
    const text = el ? el.querySelector(kind === "error" ? "[data-auth-error-text]" : "[data-auth-success-text]") : null;
    if (!el || !text) return;
    clearAlerts(view);
    text.textContent = message;
    el.hidden = false;
  }

  function setView(dialog, name) {
    let active = null;
    dialog.querySelectorAll("[data-auth-view]").forEach(function (view) {
      const isActive = view.getAttribute("data-auth-view") === name;
      view.hidden = !isActive;
      if (isActive) active = view;
    });
    if (!active) return null;
    clearAlerts(active);
    const title = active.querySelector(".wh-auth-title");
    if (title && title.id) {
      dialog.setAttribute("aria-labelledby", title.id);
    }
    const input = firstInput(active);
    if (input) input.focus();
    return active;
  }

  if (authDialog) {
    document.querySelectorAll("[data-auth-open]").forEach(function (trigger) {
      trigger.addEventListener("click", function (event) {
        event.preventDefault();
        setView(authDialog, "login");
        if (!authDialog.open) authDialog.showModal();
        const active = authDialog.querySelector("[data-auth-view]:not([hidden])");
        const input = firstInput(active);
        if (input) input.focus();
      });
    });

    authDialog.querySelectorAll("[data-auth-close]").forEach(function (button) {
      button.addEventListener("click", function () {
        authDialog.close();
      });
    });

    authDialog.addEventListener("click", function (event) {
      if (event.target === authDialog) authDialog.close();
    });

    authDialog.querySelectorAll("[data-auth-switch]").forEach(function (link) {
      link.addEventListener("click", function (event) {
        event.preventDefault();
        setView(authDialog, link.getAttribute("data-auth-switch"));
      });
    });

    authDialog.querySelectorAll("form[data-auth-form]").forEach(function (form) {
      form.addEventListener("submit", async function (event) {
        event.preventDefault();
        if (form.dataset.submitting === "1") return;

        const view = form.closest("[data-auth-view]");
        const submitButton = form.querySelector("[data-auth-submit]");
        if (!view || !submitButton) return;

        form.dataset.submitting = "1";
        clearAlerts(view);
        submitButton.disabled = true;
        submitButton.setAttribute("aria-busy", "true");

        try {
          const response = await fetch(form.action, {
            method: "POST",
            headers: { Accept: "application/json" },
            body: new FormData(form),
          });
          let data = {};
          try {
            data = await response.json();
          } catch (err) {
            data = {};
          }

          if (response.ok && data.ok) {
            if (data.redirect) {
              window.location.assign(data.redirect);
              return;
            }
            if (data.mode === "login") {
              const loginView = setView(authDialog, "login");
              showAlert(loginView, "success", data.message || "Registrasi berhasil.");
            }
          } else {
            showAlert(view, "error", data.error || "Terjadi kesalahan. Silakan coba lagi.");
          }
        } catch (err) {
          showAlert(view, "error", "Tidak dapat terhubung ke server. Periksa koneksi Anda.");
        } finally {
          delete form.dataset.submitting;
          submitButton.disabled = false;
          submitButton.removeAttribute("aria-busy");
        }
      });
    });
  }

  document.querySelectorAll("[data-auth-page-dialog]").forEach(function (dialog) {
    dialog.addEventListener("click", function (event) {
      if (event.target === dialog) dialog.close();
    });

    dialog.addEventListener("close", function () {
      window.location.assign("/");
    });

    if (dialog.hasAttribute("open")) dialog.removeAttribute("open");
    dialog.showModal();

    const input = firstInput(dialog);
    if (input) input.focus();
  });
});

document.addEventListener("DOMContentLoaded", function () {
  const accountDialog = document.getElementById("account-dialog");

  if (!accountDialog) return;

  document.querySelectorAll("[data-account-open]").forEach(function (trigger) {
    trigger.addEventListener("click", function (event) {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) {
        return;
      }
      event.preventDefault();
      if (!accountDialog.open) accountDialog.showModal();
    });
  });

  accountDialog.querySelectorAll("[data-account-close]").forEach(function (button) {
    button.addEventListener("click", function () {
      accountDialog.close();
    });
  });

  accountDialog.addEventListener("click", function (event) {
    if (event.target === accountDialog) accountDialog.close();
  });

  if (accountDialog.hasAttribute("data-account-page-dialog")) {
    accountDialog.addEventListener("close", function () {
      window.location.assign("/");
    });
    accountDialog.removeAttribute("open");
    accountDialog.showModal();
  }
});
