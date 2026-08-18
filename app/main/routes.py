from datetime import datetime
import base64
import os
import re
import sqlite3
import threading
import uuid
from flask import render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from app.main import main_bp
from app.main.forms import ProfileForm, PlatformHandleForm, RecruitmentForm
from app.models.user import User
from app.models.platform import get_scrape_results, set_handle, delete_handle, get_handles
from app.models.content import (get_tutorials, get_tutorial, get_online_contests, get_online_contest,
                                get_campus_events, get_campus_event,
                                get_awards, get_award, create_award, delete_award)
from app.models.registration import (get_registration, create_registration, delete_registration,
                                     get_today_ranking, get_today_rankings)
from app.models.recruitment import (get_recruitments, get_recruitment, create_recruitment,
                                    update_recruitment, delete_recruitment, get_members,
                                    get_member, join_recruitment, leave_recruitment, count_members)
from app.constants import WUYU_LABELS
from app.services.upload import save_upload_file, classify_file_type


def _clean_optional(v):
    """Normalize optional form values: empty string -> None."""
    return (v or '').strip() or None


@main_bp.route('/')
@login_required
def index():
    scrape_results = get_scrape_results(current_user.id)
    total_solved = sum(r['total_solved'] for r in scrape_results)
    my_ranking = get_today_ranking(current_user.id)
    upcoming_events = [
        e for e in get_campus_events()
        if e['is_open'] and (not e['registration_deadline'] or e['registration_deadline'] >= datetime.utcnow().isoformat())
    ][:5]
    now_iso = datetime.utcnow().isoformat()
    recent_contests = [
        c for c in get_online_contests()
        if c['end_time'] is None or c['end_time'] >= now_iso
    ][:5]

    return render_template('main/index.html',
                           total_solved=total_solved,
                           scrape_results=scrape_results,
                           my_ranking=my_ranking,
                           upcoming_events=upcoming_events,
                           recent_contests=recent_contests)


@main_bp.route('/profile')
@login_required
def profile():
    scrape_results = get_scrape_results(current_user.id)
    platform_labels = []
    platform_data = []
    name_map = {'luogu': '洛谷', 'nowcoder': '牛客', 'atcoder': 'AtCoder', 'codeforces': 'Codeforces',
                'leetcode': '力扣', 'lanqiao': '蓝桥杯'}
    for r in scrape_results:
        platform_labels.append(name_map.get(r['platform'], r['platform']))
        platform_data.append(r['total_solved'])

    all_categories = {}
    for r in scrape_results:
        import json
        try:
            cat = json.loads(r['category_stats']) if r['category_stats'] else {}
            for k, v in cat.items():
                all_categories[k] = all_categories.get(k, 0) + v
        except (json.JSONDecodeError, TypeError):
            pass

    handles = {h['platform']: h['handle'] for h in get_handles(current_user.id)}

    return render_template('main/profile.html',
                           scrape_results=scrape_results,
                           platform_labels=platform_labels,
                           platform_data=platform_data,
                           all_categories=all_categories,
                           handles=handles)


@main_bp.route('/user/<int:id>')
@login_required
def user_profile(id):
    target = User.find_by_id(id)
    if not target:
        abort(404)
    scrape_results = get_scrape_results(id)
    total_solved = sum(r['total_solved'] for r in scrape_results)
    ranking = get_today_ranking(id)
    platform_labels = []
    platform_data = []
    name_map = {'luogu': '洛谷', 'nowcoder': '牛客', 'atcoder': 'AtCoder', 'codeforces': 'Codeforces',
                'leetcode': '力扣', 'lanqiao': '蓝桥杯'}
    for r in scrape_results:
        platform_labels.append(name_map.get(r['platform'], r['platform']))
        platform_data.append(r['total_solved'])

    all_categories = {}
    for r in scrape_results:
        import json
        try:
            cat = json.loads(r['category_stats']) if r['category_stats'] else {}
            for k, v in cat.items():
                all_categories[k] = all_categories.get(k, 0) + v
        except (json.JSONDecodeError, TypeError):
            pass

    handles = {h['platform']: h['handle'] for h in get_handles(id)}

    return render_template('main/user_profile.html',
                           target_user=target,
                           scrape_results=scrape_results,
                           total_solved=total_solved,
                           ranking=ranking,
                           platform_labels=platform_labels,
                           platform_data=platform_data,
                           all_categories=all_categories,
                           handles=handles)


def _save_avatar_bytes(data, ext):
    """Save avatar bytes, delete the old avatar file, update the user row."""
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    upload_dir = os.path.join(base, 'app', 'static', 'uploads', 'avatars')
    os.makedirs(upload_dir, exist_ok=True)
    saved_name = f"{uuid.uuid4().hex[:12]}.{ext}"
    with open(os.path.join(upload_dir, saved_name), 'wb') as f:
        f.write(data)
    rel_path = f'uploads/avatars/{saved_name}'
    # 替换头像时清理旧文件
    if current_user.avatar_path:
        old = os.path.join(base, 'app', 'static', current_user.avatar_path)
        if os.path.exists(old):
            try:
                os.remove(old)
            except OSError:
                pass
    current_user.update(avatar_path=rel_path)


@main_bp.route('/profile/avatar', methods=['POST'])
@login_required
def upload_avatar():
    # 裁剪后的 dataURL 优先
    cropped_data = request.form.get('cropped_data', '')
    if cropped_data:
        if not cropped_data.startswith('data:image/') or ';base64,' not in cropped_data:
            flash('裁剪数据无效。', 'danger')
            return redirect(url_for('main.profile'))
        header, b64 = cropped_data.split(',', 1)
        fmt = header.split(';')[0].split('/')[1]
        if fmt not in ('png', 'jpeg', 'webp'):
            flash('头像仅支持 jpg / png / webp 格式。', 'danger')
            return redirect(url_for('main.profile'))
        try:
            raw = base64.b64decode(b64 + '=' * (-len(b64) % 4))
        except Exception:
            flash('裁剪数据无效。', 'danger')
            return redirect(url_for('main.profile'))
        if len(raw) > 5 * 1024 * 1024:
            flash('头像文件不能超过 5MB。', 'danger')
            return redirect(url_for('main.profile'))
        _save_avatar_bytes(raw, 'jpg' if fmt == 'jpeg' else fmt)
        flash('头像已更新！', 'success')
        return redirect(url_for('main.profile'))

    file = request.files.get('avatar')
    if not file or not file.filename:
        flash('请选择图片文件。', 'warning')
        return redirect(url_for('main.profile'))
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in {'jpg', 'jpeg', 'png', 'gif', 'webp'}:
        flash('头像仅支持 jpg / png / gif / webp 格式。', 'danger')
        return redirect(url_for('main.profile'))
    data = file.read()
    if len(data) > 5 * 1024 * 1024:
        flash('头像文件不能超过 5MB。', 'danger')
        return redirect(url_for('main.profile'))
    _save_avatar_bytes(data, ext)
    flash('头像已更新！', 'success')
    return redirect(url_for('main.profile'))


@main_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    profile_form = ProfileForm(obj=current_user)
    handle_form = PlatformHandleForm()

    ALL_PLATFORMS = ['luogu', 'nowcoder', 'atcoder', 'codeforces', 'leetcode', 'lanqiao']
    SCRAPABLE = ['luogu', 'nowcoder', 'atcoder', 'codeforces']  # leetcode/lanqiao manual only

    if request.method == 'GET':
        for h in get_handles(current_user.id):
            field = getattr(handle_form, h['platform'], None)
            if field and hasattr(field, 'data'):
                field.data = h['handle']
        # Pre-fill manual counts from scrape_results
        from app.models.platform import get_scrape_results
        for r in get_scrape_results(current_user.id):
            count_field_name = f"{r['platform']}_count"
            field = getattr(handle_form, count_field_name, None)
            if field and hasattr(field, 'data'):
                field.data = r['total_solved']

    if request.method == 'POST':
        if 'submit_profile' in request.form and profile_form.validate_on_submit():
            current_user.update(
                real_name=profile_form.real_name.data,
                grade=profile_form.grade.data,
                email=_clean_optional(profile_form.email.data),
                student_id=_clean_optional(profile_form.student_id.data),
                surname_zh=_clean_optional(profile_form.surname_zh.data),
                given_name_zh=_clean_optional(profile_form.given_name_zh.data),
                first_name=_clean_optional(profile_form.first_name.data),
                last_name=_clean_optional(profile_form.last_name.data),
                gender=_clean_optional(profile_form.gender.data),
                phone=_clean_optional(profile_form.phone.data),
                enroll_year=_clean_optional(profile_form.enroll_year.data),
                department=_clean_optional(profile_form.department.data),
                major=_clean_optional(profile_form.major.data),
                grad_year=_clean_optional(profile_form.grad_year.data),
                tshirt_size=_clean_optional(profile_form.tshirt_size.data),
            )
            flash('个人信息已更新。', 'success')
            return redirect(url_for('main.profile'))

        if 'submit_handles' in request.form and handle_form.validate_on_submit():
            for platform in ALL_PLATFORMS:
                val = getattr(handle_form, platform).data
                if val and val.strip():
                    set_handle(current_user.id, platform, val.strip())
                elif not val or not val.strip():
                    delete_handle(current_user.id, platform)
            # Save manual counts for non-scrapable platforms
            from app.models.platform import upsert_scrape_result
            import json
            for platform in ['leetcode', 'lanqiao']:
                count_field = getattr(handle_form, f'{platform}_count')
                if count_field and count_field.data is not None:
                    upsert_scrape_result(
                        user_id=current_user.id,
                        platform=platform,
                        total_solved=count_field.data,
                    )
            # Immediately scrape scrapable platforms in background
            _scrape_user_async(current_user.id)
            flash('平台账号已更新，正在后台拉取刷题数据...', 'success')
            return redirect(url_for('main.profile'))

    return render_template('main/edit_profile.html', profile_form=profile_form, handle_form=handle_form)


@main_bp.route('/leaderboard')
@login_required
def leaderboard():
    rankings = get_today_rankings()
    if not rankings:
        # Fallback: compute on the fly
        from app.database import query
        rows = query(
            "SELECT u.id as user_id, u.username, u.real_name, u.grade, u.avatar_path, u.member_type, "
            "COALESCE(SUM(sr.total_solved),0) as total_solved "
            "FROM users u LEFT JOIN scrape_results sr ON u.id=sr.user_id "
            "GROUP BY u.id ORDER BY total_solved DESC"
        )
        rankings = []
        for rank, r in enumerate(rows, 1):
            rankings.append({**r, 'rank': rank})
    return render_template('main/leaderboard.html', rankings=rankings)


@main_bp.route('/tutorials')
@login_required
def tutorials():
    return render_template('main/tutorials.html', tutorials=get_tutorials())


@main_bp.route('/tutorials/<int:id>')
@login_required
def tutorial_detail(id):
    t = get_tutorial(id)
    if not t:
        from flask import abort; abort(404)
    return render_template('main/tutorial_detail.html', tutorial=t)


@main_bp.route('/online-contests')
@login_required
def online_contests():
    return render_template('main/online_contests.html', contests=get_online_contests())


@main_bp.route('/online-contests/<int:id>')
@login_required
def online_contest_detail(id):
    contest = get_online_contest(id)
    if not contest:
        abort(404)
    return render_template('main/online_contest_detail.html', contest=contest)


@main_bp.route('/campus-events')
@login_required
def campus_events():
    wuyu = request.args.get('wuyu')
    events = get_campus_events()
    if wuyu:
        events = [e for e in events if e.get('wuyu_type') == wuyu]
    return render_template('main/campus_events.html', events=events, now=datetime.utcnow(), current_filter=wuyu)


@main_bp.route('/campus-events/<int:id>')
@login_required
def campus_event_detail(id):
    event = get_campus_event(id)
    if not event:
        from flask import abort; abort(404)
    from app.models.registration import count_registrations_for_event
    event['reg_count'] = count_registrations_for_event(id)
    is_registered = get_registration(id, current_user.id) is not None
    now = datetime.utcnow()
    can_register = (event['is_open'] and
                    (not event['registration_deadline'] or event['registration_deadline'] >= now.isoformat()))
    return render_template('main/campus_event_detail.html',
                           event=event, is_registered=is_registered, can_register=can_register)


@main_bp.route('/campus-events/<int:id>/register', methods=['POST'])
@login_required
def register_event(id):
    event = get_campus_event(id)
    if not event:
        from flask import abort; abort(404)
    now = datetime.utcnow()
    if not event['is_open']:
        flash('该活动已关闭报名。', 'warning')
        return redirect(url_for('main.campus_event_detail', id=id))
    if event['registration_deadline'] and event['registration_deadline'] < now.isoformat():
        flash('报名已截止。', 'warning')
        return redirect(url_for('main.campus_event_detail', id=id))
    if get_registration(id, current_user.id):
        flash('您已报名该活动。', 'info')
        return redirect(url_for('main.campus_event_detail', id=id))
    create_registration(
        id, current_user.id,
        contact_phone=request.form.get('contact_phone', '').strip() or None,
        contact_email=request.form.get('contact_email', '').strip() or None,
        notes=request.form.get('notes', '').strip() or None,
    )
    flash('报名成功！', 'success')
    return redirect(url_for('main.campus_event_detail', id=id))


@main_bp.route('/campus-events/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_registration(id):
    event = get_campus_event(id)
    if not event:
        from flask import abort; abort(404)
    if get_registration(id, current_user.id):
        delete_registration(id, current_user.id)
        flash('已取消报名。', 'info')
    else:
        flash('您未报名该活动。', 'warning')
    return redirect(url_for('main.campus_event_detail', id=id))


@main_bp.route('/awards')
@login_required
def awards():
    wuyu = request.args.get('wuyu')
    year = request.args.get('year', type=int)
    all_awards = get_awards()
    # 可见性过滤：公开材料所有人可见；仅自己可见的材料只有上传者和管理员可见
    visible = [a for a in all_awards
               if a.get('visibility') != 'private'
               or a.get('uploaded_by') == current_user.id
               or current_user.is_admin()]
    years = sorted({a['award_year'] for a in visible if a.get('award_year')}, reverse=True)
    award_list = visible
    if wuyu:
        award_list = [a for a in award_list if a.get('wuyu_type') == wuyu]
    if year:
        award_list = [a for a in award_list if a.get('award_year') == year]
    return render_template('main/awards.html', awards=award_list,
                           current_filter=wuyu, current_year=year, years=years)


@main_bp.route('/awards/upload', methods=['GET', 'POST'])
@login_required
def upload_award_route():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        wuyu_type = request.form.get('wuyu_type', '').strip()
        year_raw = request.form.get('year', '').strip()
        visibility = request.form.get('visibility', 'public').strip()
        file = request.files.get('file')
        if not title:
            flash('请输入标题。', 'danger')
            return redirect(url_for('main.upload_award_route'))
        if wuyu_type not in WUYU_LABELS:
            flash('请选择五育类型。', 'danger')
            return redirect(url_for('main.upload_award_route'))
        if not re.fullmatch(r'(19|20)\d{2}', year_raw):
            flash('请选择获奖年份。', 'danger')
            return redirect(url_for('main.upload_award_route'))
        award_year = int(year_raw)
        if visibility not in ('public', 'private'):
            visibility = 'public'
        if not file or not file.filename:
            flash('请选择文件。', 'danger')
            return redirect(url_for('main.upload_award_route'))
        rel_path, original, _ = save_upload_file(file, 'awards')
        create_award(title, description or None, rel_path, classify_file_type(original), original,
                     current_user.id, wuyu_type, award_year, visibility)
        flash('获奖材料已上传！', 'success')
        return redirect(url_for('main.awards'))
    current_year = datetime.now().year
    return render_template('main/award_form.html',
                           years=range(current_year, 2016, -1), default_year=current_year)


@main_bp.route('/awards/<int:id>/delete', methods=['POST'])
@login_required
def delete_award_member_route(id):
    a = get_award(id)
    if not a:
        abort(404)
    if not (current_user.is_admin() or a['uploaded_by'] == current_user.id):
        flash('您没有权限删除该材料。', 'danger')
        return redirect(url_for('main.awards'))
    if a.get('file_path'):
        full = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                            'app', 'static', a['file_path'])
        if os.path.exists(full):
            os.remove(full)
    delete_award(id)
    flash('获奖材料已删除。', 'success')
    return redirect(url_for('main.awards'))


# ---- Team Recruitments ----
@main_bp.route('/recruitments')
@login_required
def recruitments():
    wuyu = request.args.get('wuyu')
    return render_template('main/recruitments.html',
                           recruitments=get_recruitments(wuyu_type=wuyu),
                           current_filter=wuyu)


@main_bp.route('/recruitments/create', methods=['GET', 'POST'])
@login_required
def new_recruitment():
    form = RecruitmentForm()
    if form.validate_on_submit():
        create_recruitment(
            title=form.title.data,
            competition_type=form.competition_type.data.strip(),
            recruit_count=form.recruit_count.data,
            requirement=form.requirement.data.strip(),
            wuyu_type=form.wuyu_type.data,
            description=(form.description.data or '').strip() or None,
            posted_by=current_user.id,
        )
        flash('组队招募已发布！', 'success')
        return redirect(url_for('main.recruitments'))
    return render_template('main/recruitment_form.html', form=form)


@main_bp.route('/recruitments/<int:id>')
@login_required
def recruitment_detail(id):
    recruit = get_recruitment(id)
    if not recruit:
        abort(404)
    members = get_members(id)
    member_count = recruit['member_count']
    is_member = get_member(id, current_user.id) is not None
    is_full = member_count >= recruit['recruit_count']
    can_join = bool(recruit['is_open']) and not is_full and not is_member
    return render_template('main/recruitment_detail.html',
                           recruit=recruit, members=members, member_count=member_count,
                           is_member=is_member, is_full=is_full, can_join=can_join)


@main_bp.route('/recruitments/<int:id>/join', methods=['POST'])
@login_required
def join_recruitment_route(id):
    recruit = get_recruitment(id)
    if not recruit:
        abort(404)
    if not recruit['is_open']:
        flash('该招募已关闭。', 'warning')
        return redirect(url_for('main.recruitment_detail', id=id))
    if count_members(id) >= recruit['recruit_count']:
        flash('该招募已满员。', 'warning')
        return redirect(url_for('main.recruitment_detail', id=id))
    if get_member(id, current_user.id):
        flash('您已加入该招募。', 'info')
        return redirect(url_for('main.recruitment_detail', id=id))
    try:
        join_recruitment(id, current_user.id)
    except sqlite3.IntegrityError:
        flash('您已加入该招募。', 'info')
        return redirect(url_for('main.recruitment_detail', id=id))
    flash('加入成功！', 'success')
    return redirect(url_for('main.recruitment_detail', id=id))


@main_bp.route('/recruitments/<int:id>/leave', methods=['POST'])
@login_required
def leave_recruitment_route(id):
    recruit = get_recruitment(id)
    if not recruit:
        abort(404)
    if get_member(id, current_user.id):
        leave_recruitment(id, current_user.id)
        flash('已退出该招募。', 'info')
    else:
        flash('您未加入该招募。', 'warning')
    return redirect(url_for('main.recruitment_detail', id=id))


@main_bp.route('/recruitments/<int:id>/close', methods=['POST'])
@login_required
def close_recruitment_route(id):
    recruit = get_recruitment(id)
    if not recruit:
        abort(404)
    if not (current_user.is_admin() or recruit['posted_by'] == current_user.id):
        flash('您没有权限执行此操作。', 'danger')
        return redirect(url_for('main.recruitment_detail', id=id))
    new_open = 0 if recruit['is_open'] else 1
    update_recruitment(id, is_open=new_open)
    flash('招募已关闭。' if not new_open else '招募已重新开放。', 'success')
    return redirect(url_for('main.recruitment_detail', id=id))


@main_bp.route('/recruitments/<int:id>/delete', methods=['POST'])
@login_required
def delete_recruitment_route(id):
    recruit = get_recruitment(id)
    if not recruit:
        abort(404)
    if not (current_user.is_admin() or recruit['posted_by'] == current_user.id):
        flash('您没有权限执行此操作。', 'danger')
        return redirect(url_for('main.recruitment_detail', id=id))
    delete_recruitment(id)
    flash('招募已删除。', 'success')
    return redirect(url_for('main.recruitments'))


def _scrape_user_async(user_id):
    """Run a single-user scrape in a background thread."""
    app = current_app._get_current_object()

    def _run():
        with app.app_context():
            try:
                from app.scraper.orchestrator import scrape_single_user
                from app.models.registration import recompute_rankings
                scrape_single_user(user_id)
                recompute_rankings()
                print(f"[BG] Scraped user {user_id}")
            except Exception as e:
                print(f"[BG] Scrape error for user {user_id}: {e}")

    t = threading.Thread(target=_run, daemon=True)
    t.start()
