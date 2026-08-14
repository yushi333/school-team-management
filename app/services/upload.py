"""Shared file-upload helpers (awards, document library)."""
import os
import uuid

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app', 'static')

IMG_EXTS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'}
DOC_EXTS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'zip', 'rar'}


def classify_file_type(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return 'image' if ext in IMG_EXTS else 'document' if ext in DOC_EXTS else 'other'


def save_upload_file(file_storage, subdir):
    """Save to app/static/uploads/<subdir>/{uuid12}_{basename}. Returns (rel_path, original_filename, file_size)."""
    original = file_storage.filename.replace('\\', '/').split('/')[-1]  # strip client-side path
    upload_dir = os.path.join(BASE, 'uploads', subdir)
    os.makedirs(upload_dir, exist_ok=True)
    saved_name = f"{uuid.uuid4().hex[:12]}_{original}"
    save_path = os.path.join(upload_dir, saved_name)
    file_storage.save(save_path)
    return f'uploads/{subdir}/{saved_name}', original, os.path.getsize(save_path)
