from datetime import datetime
import os
import re
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.admin import admin_bp
from app.admin.forms import UserCreateForm, UserEditForm, TutorialForm, OnlineContestForm, CampusEventForm
from app.models.user import User
from app.models.content import (get_tutorials, create_tutorial, delete_tutorial, count_tutorials,
                                get_online_contests, create_online_contest, delete_online_contest,
                                count_online_contests, get_campus_events, get_campus_event,
                                create_campus_event, update_campus_event, delete_campus_event,
                                count_campus_events, get_awards, get_award, create_award, delete_award, count_awards)
from app.models.registration import get_registrations, count_all_registrations
from app.models.recruitment import (get_recruitments, get_recruitment, update_recruitment,
                                    delete_recruitment, count_recruitments)
from app.models.document import (get_folders, get_folder, create_folder, get_subfolder_ids,
                                 get_files_in_folders, get_folder_path, delete_folder_subtree,
                                 get_files, get_file, add_file, delete_file, count_files)
from app.models.platform import get_handles, get_scrape_results
from app.decorators import admin_required
from app.database import query
from app.constants import WUYU_LABELS
from app.services.upload import save_upload_file, classify_file_type


def _clean(v):
    """Normalize optional form values: empty string -> None."""
    return (v or '').strip() or None


@admin_bp.route('/')
@login_required
@admin_required
def index():
    return render_template('admin/index.html',
                           user_count=User.count(),
                           tutorial_count=count_tutorials(),
                           contest_count=count_online_contests(),
                           event_count=count_campus_events(),
                           reg_count=count_all_registrations(),
                           award_count=count_awards(),
                           recruitment_count=count_recruitments(),
                           doc_file_count=count_files())


# ---- Users ----
@admin_bp.route('/users')
@login_required
@admin_required
def user_list():
    mtype = request.args.get('member_type')
    users = User.all()
    if mtype in ('trial', 'formal'):
        users = [u for u in users if u.member_type == mtype]
    return render_template('admin/user_list.html', users=users, member_type_filter=mtype)


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    form = UserCreateForm()
    if form.validate_on_submit():
        if User.find_by_username(form.username.data):
            flash('用户名已存在。', 'danger')
        else:
            User.create(form.username.data, form.password.data, form.role.data,
                        form.real_name.data or None, form.grade.data or None,
                        member_type=form.member_type.data or 'trial')
            flash(f'用户 {form.username.data} 创建成功！', 'success')
            return redirect(url_for('admin.user_list'))
    return render_template('admin/user_form.html', form=form, edit_mode=False)


@admin_bp.route('/users/<int:id>')
@login_required
@admin_required
def user_detail(id):
    user = User.find_by_id(id)
    if not user:
        abort(404)
    return render_template('admin/user_detail.html', target_user=user,
                           handles={h['platform']: h['handle'] for h in get_handles(id)},
                           scrape_results=get_scrape_results(id))


@admin_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    user = User.find_by_id(id)
    if not user:
        from flask import abort; abort(404)
    form = UserEditForm(obj=user)
    if form.validate_on_submit():
        user.update(real_name=form.real_name.data or None, grade=form.grade.data or None, role=form.role.data,
                    member_type=form.member_type.data or 'trial',
                    email=_clean(form.email.data), student_id=_clean(form.student_id.data),
                    surname_zh=_clean(form.surname_zh.data), given_name_zh=_clean(form.given_name_zh.data),
                    first_name=_clean(form.first_name.data), last_name=_clean(form.last_name.data),
                    gender=_clean(form.gender.data), phone=_clean(form.phone.data),
                    enroll_year=_clean(form.enroll_year.data), department=_clean(form.department.data),
                    major=_clean(form.major.data), grad_year=_clean(form.grad_year.data),
                    tshirt_size=_clean(form.tshirt_size.data))
        flash(f'用户 {user.username} 已更新。', 'success')
        return redirect(url_for('admin.user_list'))
    return render_template('admin/user_form.html', form=form, edit_mode=True, target_user=user)


@admin_bp.route('/users/<int:id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_password(id):
    user = User.find_by_id(id)
    if not user:
        from flask import abort; abort(404)
    new_pwd = request.form.get('new_password', '').strip()
    if len(new_pwd) < 6:
        flash('密码至少6位。', 'danger')
        return redirect(url_for('admin.edit_user', id=id))
    user.set_password(new_pwd)
    flash(f'用户 {user.username} 的密码已重置。', 'success')
    return redirect(url_for('admin.user_list'))


@admin_bp.route('/users/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    if id == current_user.id:
        flash('不能删除自己的账号。', 'danger')
        return redirect(url_for('admin.user_list'))
    user = User.find_by_id(id)
    if user:
        user.delete()
        flash(f'用户 {user.username} 已删除。', 'success')
    return redirect(url_for('admin.user_list'))


# ---- Tutorials ----
@admin_bp.route('/tutorials')
@login_required
@admin_required
def tutorial_list():
    return render_template('admin/tutorial_list.html', tutorials=get_tutorials())


@admin_bp.route('/tutorials/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_tutorial():
    form = TutorialForm()
    if form.validate_on_submit():
        create_tutorial(form.title.data, form.description.data or None, form.video_url.data, current_user.id)
        flash('教学视频已发布！', 'success')
        return redirect(url_for('admin.tutorial_list'))
    return render_template('admin/tutorial_form.html', form=form)


@admin_bp.route('/tutorials/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_tutorial_route(id):
    delete_tutorial(id)
    flash('教学视频已删除。', 'success')
    return redirect(url_for('admin.tutorial_list'))


# ---- Online Contests ----
@admin_bp.route('/online-contests')
@login_required
@admin_required
def online_contest_list():
    return render_template('admin/online_contest_list.html', contests=get_online_contests())


@admin_bp.route('/online-contests/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_online_contest():
    form = OnlineContestForm()
    if form.validate_on_submit():
        create_online_contest(
            form.title.data, form.platform.data, form.contest_url.data or None,
            form.start_time.data, form.end_time.data, form.description.data or None, current_user.id
        )
        flash('线上比赛资讯已发布！', 'success')
        return redirect(url_for('admin.online_contest_list'))
    return render_template('admin/online_contest_form.html', form=form)


@admin_bp.route('/online-contests/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_online_contest_route(id):
    delete_online_contest(id)
    flash('线上比赛资讯已删除。', 'success')
    return redirect(url_for('admin.online_contest_list'))


# ---- Campus Events ----
@admin_bp.route('/campus-events')
@login_required
@admin_required
def campus_event_list():
    events = get_campus_events()
    from app.models.registration import count_registrations_for_event
    for e in events:
        e['reg_count'] = count_registrations_for_event(e['id'])
    return render_template('admin/campus_event_list.html', events=events)


@admin_bp.route('/campus-events/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_campus_event():
    form = CampusEventForm()
    if form.validate_on_submit():
        deadline = form.registration_deadline.data
        create_campus_event(
            form.title.data, form.content.data or None, form.location.data or None,
            form.event_date.data,
            deadline.strftime('%Y-%m-%dT%H:%M') if deadline else None,
            form.is_open.data, current_user.id,
            form.wuyu_type.data
        )
        flash('校内活动已发布！', 'success')
        return redirect(url_for('admin.campus_event_list'))
    return render_template('admin/campus_event_form.html', form=form, edit_mode=False)


@admin_bp.route('/campus-events/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_campus_event(id):
    event = get_campus_event(id)
    if not event:
        from flask import abort; abort(404)
    # 数据库存的是字符串，转为 date/datetime 对象供表单渲染（兼容旧格式）
    if event.get('event_date'):
        try:
            event['event_date'] = datetime.strptime(event['event_date'], '%Y-%m-%d').date()
        except ValueError:
            event['event_date'] = None
    if event.get('registration_deadline'):
        deadline_dt = None
        for fmt in ('%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S'):
            try:
                deadline_dt = datetime.strptime(event['registration_deadline'], fmt)
                break
            except ValueError:
                pass
        event['registration_deadline'] = deadline_dt
    form = CampusEventForm(data=event)
    if form.validate_on_submit():
        deadline = form.registration_deadline.data
        update_campus_event(id,
                            title=form.title.data, content=form.content.data or None,
                            location=form.location.data or None, event_date=form.event_date.data,
                            registration_deadline=deadline.strftime('%Y-%m-%dT%H:%M') if deadline else None,
                            is_open=1 if form.is_open.data else 0,
                            wuyu_type=form.wuyu_type.data)
        flash('校内活动已更新！', 'success')
        return redirect(url_for('admin.campus_event_list'))
    return render_template('admin/campus_event_form.html', form=form, edit_mode=True, event=event)


@admin_bp.route('/campus-events/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_campus_event_route(id):
    delete_campus_event(id)
    flash('校内活动已删除。', 'success')
    return redirect(url_for('admin.campus_event_list'))


@admin_bp.route('/campus-events/<int:id>/registrations')
@login_required
@admin_required
def view_registrations(id):
    event = get_campus_event(id)
    if not event:
        from flask import abort; abort(404)
    return render_template('admin/registrations.html', event=event, registrations=get_registrations(id))


@admin_bp.route('/campus-events/<int:id>/export')
@login_required
@admin_required
def export_registrations(id):
    event = get_campus_event(id)
    if not event:
        from flask import abort; abort(404)
    from app.services.export import export_excel
    return export_excel(event)


# ---- Awards ----
@admin_bp.route('/awards')
@login_required
@admin_required
def award_list():
    return render_template('admin/award_list.html', awards=get_awards())


@admin_bp.route('/awards/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_award():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        wuyu_type = request.form.get('wuyu_type', '').strip()
        year_raw = request.form.get('year', '').strip()
        file = request.files.get('file')
        if not title:
            flash('请输入标题。', 'danger')
            return redirect(url_for('admin.add_award'))
        if wuyu_type not in WUYU_LABELS:
            flash('请选择五育类型。', 'danger')
            return redirect(url_for('admin.add_award'))
        award_year = None
        if year_raw:
            if not re.fullmatch(r'(19|20)\d{2}', year_raw):
                flash('请选择有效的年份。', 'danger')
                return redirect(url_for('admin.add_award'))
            award_year = int(year_raw)
        if not file or not file.filename:
            flash('请选择文件。', 'danger')
            return redirect(url_for('admin.add_award'))
        rel_path, original, _ = save_upload_file(file, 'awards')
        create_award(title, description or None, rel_path, classify_file_type(original), original,
                     current_user.id, wuyu_type, award_year)
        flash('获奖材料已上传！', 'success')
        return redirect(url_for('admin.award_list'))
    current_year = datetime.now().year
    return render_template('admin/award_form.html',
                           years=range(current_year, 2016, -1), default_year=current_year)


@admin_bp.route('/awards/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_award_route(id):
    award_data = get_award(id)
    if award_data and award_data.get('file_path'):
        import os
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        full_path = os.path.join(base, 'app', 'static', award_data['file_path'])
        if os.path.exists(full_path):
            os.remove(full_path)
    delete_award(id)
    flash('获奖材料已删除。', 'success')
    return redirect(url_for('admin.award_list'))


# ---- Document Library (admin-only) ----
@admin_bp.route('/documents')
@login_required
@admin_required
def documents():
    folder_id = request.args.get('folder', type=int)
    current_folder = get_folder(folder_id) if folder_id else None
    # 子文件夹列表：当前文件夹（或根目录）下的下一层
    folders = get_folders(current_folder['id'] if current_folder else None)
    breadcrumbs = get_folder_path(current_folder['id']) if current_folder else []
    files = get_files(current_folder['id']) if current_folder else []
    return render_template('admin/documents.html', folders=folders,
                           current_folder=current_folder, files=files,
                           breadcrumbs=breadcrumbs)


@admin_bp.route('/documents/folders/create', methods=['POST'])
@login_required
@admin_required
def create_folder_route():
    name = request.form.get('name', '').strip()
    parent_id = request.form.get('parent_id', type=int)
    if parent_id and not get_folder(parent_id):
        parent_id = None  # 父文件夹不存在则落到根目录
    if not name or len(name) > 64:
        flash('请输入有效的文件夹名称。', 'danger')
    else:
        create_folder(name, parent_id)
        flash('文件夹已创建。', 'success')
    return redirect(url_for('admin.documents', folder=parent_id) if parent_id
                    else url_for('admin.documents'))


@admin_bp.route('/documents/folders/<int:fid>/delete', methods=['POST'])
@login_required
@admin_required
def delete_folder_route(fid):
    folder = get_folder(fid)
    if not folder:
        abort(404)
    ids = [fid] + get_subfolder_ids(fid)  # 先删整棵子树的磁盘文件
    for f in get_files_in_folders(ids):
        full = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                            'app', 'static', f['file_path'])
        if os.path.exists(full):
            os.remove(full)
    delete_folder_subtree(fid)
    flash('文件夹及其内容已删除。', 'success')
    parent_id = folder.get('parent_id')
    return redirect(url_for('admin.documents', folder=parent_id) if parent_id
                    else url_for('admin.documents'))


@admin_bp.route('/documents/upload', methods=['POST'])
@login_required
@admin_required
def upload_document():
    folder_id = request.form.get('folder_id', type=int)
    folder = get_folder(folder_id) if folder_id else None
    file = request.files.get('file')
    if not folder:
        flash('请选择文件夹。', 'danger')
        return redirect(url_for('admin.documents'))
    if not file or not file.filename:
        flash('请选择文件。', 'danger')
        return redirect(url_for('admin.documents', folder=folder_id))
    rel_path, original, size = save_upload_file(file, 'documents')
    add_file(folder_id, original, rel_path, size, current_user.id)
    flash('文件已上传。', 'success')
    return redirect(url_for('admin.documents', folder=folder_id))


@admin_bp.route('/documents/files/<int:fid>/delete', methods=['POST'])
@login_required
@admin_required
def delete_document_route(fid):
    f = get_file(fid)
    if not f:
        abort(404)
    full = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        'app', 'static', f['file_path'])
    if os.path.exists(full):
        os.remove(full)
    delete_file(fid)
    flash('文件已删除。', 'success')
    return redirect(url_for('admin.documents', folder=f['folder_id']))


# ---- Team Recruitments ----
@admin_bp.route('/recruitments')
@login_required
@admin_required
def recruitment_list():
    return render_template('admin/recruitment_list.html', recruitments=get_recruitments())


@admin_bp.route('/recruitments/<int:id>/close', methods=['POST'])
@login_required
@admin_required
def admin_toggle_recruitment(id):
    recruit = get_recruitment(id)
    if not recruit:
        from flask import abort; abort(404)
    new_open = 0 if recruit['is_open'] else 1
    update_recruitment(id, is_open=new_open)
    flash('招募已关闭。' if not new_open else '招募已重新开放。', 'success')
    return redirect(url_for('admin.recruitment_list'))


@admin_bp.route('/recruitments/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_recruitment(id):
    delete_recruitment(id)
    flash('招募已删除。', 'success')
    return redirect(url_for('admin.recruitment_list'))
