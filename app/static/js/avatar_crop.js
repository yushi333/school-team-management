/* 头像裁剪上传：选择图片 -> Cropper.js 框选 -> 裁剪为 256x256 -> 提交表单 */
(function () {
    const fileInput = document.getElementById('avatar-file');
    const cropBtn = document.getElementById('avatar-crop-btn');
    const confirmBtn = document.getElementById('crop-confirm');
    const croppedData = document.getElementById('cropped-data');
    const cropImage = document.getElementById('crop-image');
    const cropModalEl = document.getElementById('cropModal');
    const avatarForm = document.getElementById('avatar-form');
    if (!fileInput || !cropBtn || !cropModalEl) return;

    const ALLOWED = ['jpg', 'jpeg', 'png', 'gif', 'webp'];
    let cropper = null;
    const modal = new bootstrap.Modal(cropModalEl);

    function destroyCropper() {
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }
    }

    cropBtn.addEventListener('click', function () {
        const file = fileInput.files && fileInput.files[0];
        if (!file) {
            alert('请先选择图片文件。');
            return;
        }
        const ext = (file.name.split('.').pop() || '').toLowerCase();
        if (!ALLOWED.includes(ext)) {
            alert('头像仅支持 jpg / png / gif / webp 格式。');
            return;
        }
        const reader = new FileReader();
        reader.onload = function (e) {
            cropImage.src = e.target.result;
            croppedData.value = '';
            modal.show();
        };
        reader.readAsDataURL(file);
    });

    cropModalEl.addEventListener('shown.bs.modal', function () {
        destroyCropper();
        cropper = new Cropper(cropImage, {
            aspectRatio: 1,
            viewMode: 1,
            autoCropArea: 1,
            dragMode: 'move',
            background: false
        });
    });

    cropModalEl.addEventListener('hidden.bs.modal', function () {
        destroyCropper();
        cropImage.src = '';
    });

    confirmBtn.addEventListener('click', function () {
        if (!cropper) return;
        const canvas = cropper.getCroppedCanvas({ width: 256, height: 256, imageSmoothingQuality: 'high' });
        croppedData.value = canvas.toDataURL('image/jpeg', 0.92);
        destroyCropper();
        modal.hide();
        avatarForm.submit();
    });
})();
