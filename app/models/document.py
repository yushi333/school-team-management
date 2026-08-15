"""Document library (admin-only) helpers: folders + files."""
from datetime import datetime
from app.database import query, execute


def get_folders(parent_id=None, order_by='id ASC'):
    """Folders whose parent is parent_id (None = root level)."""
    if parent_id is None:
        return query(f"SELECT * FROM doc_folders WHERE parent_id IS NULL ORDER BY {order_by}")
    return query(f"SELECT * FROM doc_folders WHERE parent_id=? ORDER BY {order_by}", (parent_id,))


def get_folder(fid):
    return query("SELECT * FROM doc_folders WHERE id=?", (fid,), one=True)


def create_folder(name, parent_id=None):
    return execute("INSERT INTO doc_folders (name, parent_id, created_at) VALUES (?,?,?)",
                   (name, parent_id, datetime.utcnow()))


def get_subfolder_ids(fid):
    """All descendant folder ids of fid (excluding fid itself)."""
    result = []
    queue = [fid]
    while queue:
        cur = queue.pop(0)
        for c in query("SELECT id FROM doc_folders WHERE parent_id=?", (cur,)):
            result.append(c['id'])
            queue.append(c['id'])
    return result


def get_files_in_folders(folder_ids):
    """All file rows whose folder is in folder_ids (any depth)."""
    if not folder_ids:
        return []
    q = ','.join('?' * len(folder_ids))
    return query(f"SELECT * FROM doc_files WHERE folder_id IN ({q})", folder_ids)


def get_folder_path(fid):
    """Ancestor chain from root to fid inclusive, root first."""
    path = []
    cur = get_folder(fid)
    while cur:
        path.append(cur)
        cur = get_folder(cur['parent_id']) if cur.get('parent_id') else None
    path.reverse()
    return path


def delete_folder_subtree(fid):
    """Delete fid, all descendant folders and their file rows (disk files handled by caller)."""
    ids = [fid] + get_subfolder_ids(fid)
    q = ','.join('?' * len(ids))
    execute(f"DELETE FROM doc_files WHERE folder_id IN ({q})", ids)
    execute(f"DELETE FROM doc_folders WHERE id IN ({q})", ids)


def get_files(folder_id, order_by='created_at DESC'):
    return query(f"SELECT df.*, u.real_name as uploader_name, u.username as uploader_username "
                 f"FROM doc_files df LEFT JOIN users u ON df.uploaded_by=u.id "
                 f"WHERE df.folder_id=? ORDER BY {order_by}", (folder_id,))


def get_file(fid):
    return query("SELECT * FROM doc_files WHERE id=?", (fid,), one=True)


def add_file(folder_id, original_filename, file_path, file_size, uploaded_by):
    return execute(
        "INSERT INTO doc_files (folder_id, original_filename, file_path, file_size, uploaded_by, created_at) VALUES (?,?,?,?,?,?)",
        (folder_id, original_filename, file_path, file_size, uploaded_by, datetime.utcnow()))


def delete_file(fid):
    execute("DELETE FROM doc_files WHERE id=?", (fid,))


def count_files():
    return query("SELECT COUNT(*) as c FROM doc_files", one=True)['c']
