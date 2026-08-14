"""Document library (admin-only) helpers: folders + files."""
from datetime import datetime
from app.database import query, execute


def get_folders(order_by='id ASC'):
    return query(f"SELECT * FROM doc_folders ORDER BY {order_by}")


def get_folder(fid):
    return query("SELECT * FROM doc_folders WHERE id=?", (fid,), one=True)


def create_folder(name):
    return execute("INSERT INTO doc_folders (name, created_at) VALUES (?,?)", (name, datetime.utcnow()))


def delete_folder(fid):
    execute("DELETE FROM doc_folders WHERE id=?", (fid,))


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
