from datetime import datetime
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.admin import admin_bp
from app.admin.forms import UserCreateForm, UserEditForm, TutorialForm, OnlineContestForm, CampusEventForm
from app.models.user import User
from app.models.content import (get_tutorials, create_tutorial, delete_tutorial, count_tutorials,
                                get_online_contests, create_online_contest, delete_online_contest,
                                count_online_contests, get_campus_events, get_campus_event,
                                create_campus_event, update_campus_event, delete_campus_event,
                                count_campus_events)
from app.models.registration import get_registrations, count_all_registrations
from app.decorators import admin_required
from app.database import query


@admin_bp.route('/')
@login_required
@admin_required
def index():
    return render_template('admin/index.html',
                           user_count=User.count(),
                           tutorial_count=count_tutorials(),
                           contest_count=count_online_contests(),
                           event_count=count_campus_events(),
                           reg_count=count_all_registrations())


# ---- Users ----
@admin_bp.route('/users')
@login_required
@admin_required
def user_list():
    return render_template('admin/user_list.html', users=User.all())


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    form = UserCreateForm()
    if form.validate_on_submit():
        if User.find_by_username(form.username.data):
            flash('用户名已存在。', 'danger')
        else:
            User.create(form.username.data, form.password.data, form.role.data, form.real_name.data or None, form.grade.data or None)
            flash(f'用户 {form.username.data} 创建成功！', 'success')
            return redirect(url_for('admin.user_list'))
    return render_template('admin/user_form.html', form=form, edit_mode=False)


@admin_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    user = User.find_by_id(id)
    if not user:
        from flask import abort; abort(404)
    form = UserEditForm(obj=user)
    if form.validate_on_submit():
        user.update(real_name=form.real_name.data or None, grade=form.grade.data or None, role=form.role.data)
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
        create_campus_event(
            form.title.data, form.content.data or None, form.location.data or None,
            form.event_date.data, form.registration_deadline.data, form.is_open.data, current_user.id
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
    form = CampusEventForm(data=event)
    if form.validate_on_submit():
        update_campus_event(id,
                            title=form.title.data, content=form.content.data or None,
                            location=form.location.data or None, event_date=form.event_date.data,
                            registration_deadline=form.registration_deadline.data,
                            is_open=1 if form.is_open.data else 0)
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
