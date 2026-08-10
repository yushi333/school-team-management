from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, DateTimeField, DateField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, URL


class UserCreateForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=2, max=64)])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    real_name = StringField('真实姓名', validators=[Optional(), Length(max=64)])
    grade = SelectField('年级', choices=[
        ('', '请选择'), ('2022级', '2022级'), ('2023级', '2023级'), ('2024级', '2024级'),
        ('2025级', '2025级'), ('2026级', '2026级'), ('2027级', '2027级'), ('2028级', '2028级'), ('研究生', '研究生'),
    ])
    role = SelectField('角色', choices=[('member', '普通成员'), ('admin', '管理员')])
    submit = SubmitField('创建用户')


class UserEditForm(FlaskForm):
    real_name = StringField('真实姓名', validators=[Optional(), Length(max=64)])
    grade = SelectField('年级', choices=[
        ('', '请选择'), ('2022级', '2022级'), ('2023级', '2023级'), ('2024级', '2024级'),
        ('2025级', '2025级'), ('2026级', '2026级'), ('2027级', '2027级'), ('2028级', '2028级'), ('研究生', '研究生'),
    ])
    role = SelectField('角色', choices=[('member', '普通成员'), ('admin', '管理员')])
    submit = SubmitField('保存修改')


class TutorialForm(FlaskForm):
    title = StringField('视频标题', validators=[DataRequired(), Length(max=256)])
    description = TextAreaField('描述/简介', validators=[Optional()])
    video_url = StringField('视频链接', validators=[DataRequired(), Length(max=512)])
    submit = SubmitField('发布')


class OnlineContestForm(FlaskForm):
    title = StringField('比赛标题', validators=[DataRequired(), Length(max=256)])
    platform = SelectField('比赛平台', choices=[
        ('luogu', '洛谷 (Luogu)'),
        ('nowcoder', '牛客 (Nowcoder)'),
        ('codeforces', 'Codeforces'),
        ('atcoder', 'AtCoder'),
        ('other', '其他'),
    ])
    contest_url = StringField('比赛链接', validators=[Optional(), URL(message='请输入有效URL'), Length(max=512)])
    start_time = DateTimeField('开始时间 (YYYY-MM-DD HH:MM)', validators=[Optional()], format='%Y-%m-%d %H:%M')
    end_time = DateTimeField('结束时间 (YYYY-MM-DD HH:MM)', validators=[Optional()], format='%Y-%m-%d %H:%M')
    description = TextAreaField('补充说明', validators=[Optional()])
    submit = SubmitField('发布')


class CampusEventForm(FlaskForm):
    title = StringField('活动标题', validators=[DataRequired(), Length(max=256)])
    content = TextAreaField('活动详情', validators=[Optional()])
    location = StringField('活动地点', validators=[Optional(), Length(max=256)])
    event_date = DateField('活动日期 (YYYY-MM-DD)', validators=[Optional()], format='%Y-%m-%d')
    registration_deadline = DateTimeField('报名截止时间 (YYYY-MM-DD HH:MM)', validators=[Optional()], format='%Y-%m-%d %H:%M')
    is_open = BooleanField('开放报名')
    submit = SubmitField('发布')
