document.addEventListener("DOMContentLoaded", function () {
  // 1. Animasi Lebar Bar Hasil Prediksi (di halaman /result)
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

  // 2. Efek Floating Pill Navbar Saat Scroll
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

  // 3. Animasi Scroll-Reveal Saat Menggulir Halaman
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

  // 4. Efek Gelombang Klik (Click Ripple) pada Semua Tombol
  document.querySelectorAll(".btn, .wh-btn-signup-pill, .wh-btn-choose-file").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      const rect = btn.getBoundingClientRect();
      const ripple = document.createElement("span");
      const size = Math.max(rect.width, rect.height);
      ripple.style.width = ripple.style.height = size + "px";
      ripple.style.left = e.clientX - rect.left - size / 2 + "px";
      ripple.style.top = e.clientY - rect.top - size / 2 + "px";
      ripple.className = "click-ripple";
      btn.appendChild(ripple);
      setTimeout(function () {
        ripple.remove();
      }, 600);
    });
  });

  // 5. Dropzone & Animasi "Menganalisis gambar Anda..." (Gaya WriteHuman Gambar 4)
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
  const VALID_EXT = [".jpg", ".jpeg", ".png"];
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
      showError("Format berkas harus JPG, JPEG, atau PNG.");
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

    // Tampilkan animasi overlay "Menganalisis gambar Anda..." seperti Gambar 4 WriteHuman
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