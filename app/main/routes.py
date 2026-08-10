from datetime import datetime
import threading
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.main import main_bp
from app.main.forms import ProfileForm, PlatformHandleForm
from app.models.user import User
from app.models.platform import get_scrape_results, set_handle, delete_handle, get_handles
from app.models.content import (get_tutorials, get_tutorial, get_online_contests, get_campus_events,
                                get_campus_event, get_awards)
from app.models.registration import (get_registration, create_registration, delete_registration,
                                     get_today_ranking, get_today_rankings)


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
    name_map = {'luogu': '洛谷', 'nowcoder': '牛客', 'atcoder': 'AtCoder', 'codeforces': 'Codeforces'}
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


@main_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    profile_form = ProfileForm(obj=current_user)
    handle_form = PlatformHandleForm()

    if request.method == 'GET':
        for h in get_handles(current_user.id):
            if h['platform'] in ['luogu', 'nowcoder', 'atcoder', 'codeforces']:
                setattr(handle_form, h['platform'], h['handle'])

    if request.method == 'POST':
        if 'submit_profile' in request.form and profile_form.validate_on_submit():
            current_user.update(
                real_name=profile_form.real_name.data,
                grade=profile_form.grade.data
            )
            flash('个人信息已更新。', 'success')
            return redirect(url_for('main.profile'))

        if 'submit_handles' in request.form and handle_form.validate_on_submit():
            for platform in ['luogu', 'nowcoder', 'atcoder', 'codeforces']:
                val = getattr(handle_form, platform).data
                if val and val.strip():
                    set_handle(current_user.id, platform, val.strip())
                elif not val or not val.strip():
                    delete_handle(current_user.id, platform)
            # Immediately scrape in background thread
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
            "SELECT u.id as user_id, u.username, u.real_name, u.grade, COALESCE(SUM(sr.total_solved),0) as total_solved "
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


@main_bp.route('/campus-events')
@login_required
def campus_events():
    events = get_campus_events()
    return render_template('main/campus_events.html', events=events, now=datetime.utcnow())


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
    return render_template('main/awards.html', awards=get_awards())


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
