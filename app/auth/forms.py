from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired('请输入用户名')])
    password = PasswordField('密码', validators=[DataRequired('请输入密码')])
    submit = SubmitField('登录')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('原密码', validators=[DataRequired('请输入原密码')])
    new_password = PasswordField('新密码', validators=[
        DataRequired('请输入新密码'),
        Length(min=6, message='密码至少6位'),
    ])
    confirm_password = PasswordField('确认新密码', validators=[
        DataRequired('请确认新密码'),
        EqualTo('new_password', message='两次密码不一致'),
    ])
    submit = SubmitField('修改密码')
