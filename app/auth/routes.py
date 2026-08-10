from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import auth_bp
from app.auth.forms import LoginForm, ChangePasswordForm
from app.models.user import User


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.find_by_username(form.username.data)
        if user and user.check_pw(form.password.data):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash('登录成功！', 'success')
            return redirect(next_page or url_for('main.index'))
        flash('用户名或密码错误。', 'danger')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('已退出登录。', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_pw(form.old_password.data):
            flash('原密码错误。', 'danger')
        else:
            current_user.set_password(form.new_password.data)
            flash('密码修改成功！', 'success')
            return redirect(url_for('main.index'))
    return render_template('auth/change_password.html', form=form)
