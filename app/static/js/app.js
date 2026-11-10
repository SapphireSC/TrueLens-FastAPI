document.addEventListener("DOMContentLoaded", function () {
  // Fokus otomatis pada ringkasan alert error dari server jika ada
  const serverAlert = document.querySelector('[role="alert"][data-autofocus="true"]');
  if (serverAlert) {
    serverAlert.focus();
  }

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
});
