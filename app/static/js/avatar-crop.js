/** Interactive avatar cropper: select -> position/zoom -> confirm upload. */
(function () {
    const form = document.getElementById('avatar-upload-form');
    const input = document.getElementById('avatar-file-input');
    const selectButton = document.getElementById('avatar-select-button');
    const modalElement = document.getElementById('avatarCropModal');
    const stage = document.getElementById('avatar-crop-stage');
    const canvas = document.getElementById('avatar-crop-canvas');
    const zoomInput = document.getElementById('avatar-zoom');
    const confirmButton = document.getElementById('avatar-crop-confirm');
    const reselectButton = document.getElementById('avatar-reselect');
    const errorBox = document.getElementById('avatar-crop-error');
    if (!form || !input || !modalElement || !canvas || !window.bootstrap) return;

    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
    const ctx = canvas.getContext('2d');
    const state = { image: null, baseScale: 1, zoom: 1, x: 0, y: 0, dragging: false, px: 0, py: 0 };
    const cropInset = 0.08;

    function showError(message) {
        errorBox.textContent = message;
        errorBox.classList.remove('d-none');
    }

    function clearError() {
        errorBox.textContent = '';
        errorBox.classList.add('d-none');
    }

    function dimensions() {
        const side = canvas.width;
        const cropSide = side * (1 - cropInset * 2);
        return { side, cropSide, cropStart: side * cropInset };
    }

    function clampPosition() {
        if (!state.image) return;
        const { side, cropSide } = dimensions();
        const width = state.image.naturalWidth * state.baseScale * state.zoom;
        const height = state.image.naturalHeight * state.baseScale * state.zoom;
        const margin = (side - cropSide) / 2;
        state.x = Math.min(margin, Math.max(margin + cropSide - width, state.x));
        state.y = Math.min(margin, Math.max(margin + cropSide - height, state.y));
    }

    function draw() {
        if (!state.image) return;
        clampPosition();
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        const width = state.image.naturalWidth * state.baseScale * state.zoom;
        const height = state.image.naturalHeight * state.baseScale * state.zoom;
        ctx.drawImage(state.image, state.x, state.y, width, height);
    }

    function loadFile(file) {
        clearError();
        if (!file) return;
        if (!/^image\/(jpeg|png|gif|webp)$/.test(file.type)) {
            showError('请选择 JPG、PNG、GIF 或 WebP 图片。');
            modal.show();
            return;
        }
        if (file.size > 5 * 1024 * 1024) {
            showError('头像文件不能超过 5MB。');
            modal.show();
            return;
        }
        const url = URL.createObjectURL(file);
        const image = new Image();
        image.onload = function () {
            URL.revokeObjectURL(url);
            state.image = image;
            const { side, cropSide } = dimensions();
            state.baseScale = Math.max(cropSide / image.naturalWidth, cropSide / image.naturalHeight);
            state.zoom = 1;
            zoomInput.value = '1';
            const width = image.naturalWidth * state.baseScale;
            const height = image.naturalHeight * state.baseScale;
            state.x = (side - width) / 2;
            state.y = (side - height) / 2;
            draw();
            modal.show();
        };
        image.onerror = function () {
            URL.revokeObjectURL(url);
            showError('图片读取失败，请重新选择。');
            modal.show();
        };
        image.src = url;
    }

    selectButton.addEventListener('click', function () {
        input.value = '';
        input.click();
    });
    input.addEventListener('change', function () { loadFile(input.files[0]); });
    reselectButton.addEventListener('click', function () {
        modal.hide();
        input.value = '';
        window.setTimeout(function () { input.click(); }, 180);
    });

    stage.addEventListener('pointerdown', function (event) {
        if (!state.image) return;
        state.dragging = true;
        state.px = event.clientX;
        state.py = event.clientY;
        stage.classList.add('is-dragging');
        stage.setPointerCapture(event.pointerId);
    });
    stage.addEventListener('pointermove', function (event) {
        if (!state.dragging) return;
        const factor = canvas.width / stage.clientWidth;
        state.x += (event.clientX - state.px) * factor;
        state.y += (event.clientY - state.py) * factor;
        state.px = event.clientX;
        state.py = event.clientY;
        draw();
    });
    function stopDragging() {
        state.dragging = false;
        stage.classList.remove('is-dragging');
    }
    stage.addEventListener('pointerup', stopDragging);
    stage.addEventListener('pointercancel', stopDragging);

    function setZoom(nextZoom) {
        if (!state.image) return;
        const oldZoom = state.zoom;
        const center = canvas.width / 2;
        const imagePointX = (center - state.x) / oldZoom;
        const imagePointY = (center - state.y) / oldZoom;
        state.zoom = Math.min(3, Math.max(1, nextZoom));
        state.x = center - imagePointX * state.zoom;
        state.y = center - imagePointY * state.zoom;
        zoomInput.value = String(state.zoom);
        draw();
    }
    zoomInput.addEventListener('input', function () { setZoom(Number(zoomInput.value)); });
    stage.addEventListener('wheel', function (event) {
        event.preventDefault();
        setZoom(state.zoom + (event.deltaY < 0 ? 0.08 : -0.08));
    }, { passive: false });

    confirmButton.addEventListener('click', function () {
        if (!state.image) return showError('请先选择图片。');
        clearError();
        confirmButton.disabled = true;
        confirmButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>正在上传';
        const { cropSide, cropStart } = dimensions();
        const output = document.createElement('canvas');
        output.width = 512;
        output.height = 512;
        output.getContext('2d').drawImage(canvas, cropStart, cropStart, cropSide, cropSide, 0, 0, 512, 512);
        output.toBlob(function (blob) {
            if (!blob) {
                confirmButton.disabled = false;
                confirmButton.innerHTML = '<i class="bi bi-check-lg me-1"></i>确认并上传';
                return showError('头像生成失败，请重试。');
            }
            const data = new FormData();
            data.append('csrf_token', form.querySelector('[name="csrf_token"]').value);
            data.append('avatar', blob, 'cropped-avatar.png');
            fetch(form.action, { method: 'POST', body: data, credentials: 'same-origin' })
                .then(function (response) {
                    if (!response.ok) throw new Error('上传失败，请稍后重试。');
                    window.location.assign(response.url || window.location.href);
                })
                .catch(function (error) {
                    confirmButton.disabled = false;
                    confirmButton.innerHTML = '<i class="bi bi-check-lg me-1"></i>确认并上传';
                    showError(error.message);
                });
        }, 'image/png', 0.92);
    });
})();
