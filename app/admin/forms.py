from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, DateTimeField, DateField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, URL, Email
from app.constants import WUYU_CHOICES

STUDY_YEARS = [('', '请选择')] + [(f'{y}级', f'{y}级') for y in range(2022, 2031)] + [('研究生', '研究生')]
TSHIRT_SIZES = [('', '请选择'), ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL'), ('XXL', 'XXL'), ('XXXL', 'XXXL')]
MEMBER_TYPES = [('trial', '测试成员'), ('formal', '正式成员')]


class UserCreateForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=2, max=64)])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    real_name = StringField('真实姓名', validators=[Optional(), Length(max=64)])
    grade = SelectField('年级', choices=[
        ('', '请选择'), ('2022级', '2022级'), ('2023级', '2023级'), ('2024级', '2024级'),
        ('2025级', '2025级'), ('2026级', '2026级'), ('2027级', '2027级'), ('2028级', '2028级'), ('研究生', '研究生'),
    ])
    role = SelectField('角色', choices=[('member', '普通成员'), ('admin', '管理员')])
    member_type = SelectField('成员身份', choices=MEMBER_TYPES, default='trial')
    submit = SubmitField('创建用户')


class UserEditForm(FlaskForm):
    real_name = StringField('真实姓名', validators=[Optional(), Length(max=64)])
    grade = SelectField('年级', choices=[
        ('', '请选择'), ('2022级', '2022级'), ('2023级', '2023级'), ('2024级', '2024级'),
        ('2025级', '2025级'), ('2026级', '2026级'), ('2027级', '2027级'), ('2028级', '2028级'), ('研究生', '研究生'),
    ])
    email = StringField('邮箱', validators=[Optional(), Email(message='请输入有效的邮箱地址'), Length(max=128)])
    student_id = StringField('学号', validators=[Optional(), Length(max=32)])
    surname_zh = StringField('姓（中文）', validators=[Optional(), Length(max=32)])
    given_name_zh = StringField('名（中文）', validators=[Optional(), Length(max=32)])
    first_name = StringField('名（英文）', validators=[Optional(), Length(max=64)])
    last_name = StringField('姓（英文）', validators=[Optional(), Length(max=64)])
    gender = SelectField('性别', choices=[('', '请选择'), ('m', '男'), ('f', '女')], validators=[Optional()])
    phone = StringField('手机号', validators=[Optional(), Length(max=32)])
    enroll_year = SelectField('入学年份', choices=STUDY_YEARS, validators=[Optional()])
    department = StringField('院系', validators=[Optional(), Length(max=128)])
    major = StringField('专业', validators=[Optional(), Length(max=128)])
    grad_year = SelectField('毕业年份', choices=STUDY_YEARS, validators=[Optional()])
    tshirt_size = SelectField('T恤尺码', choices=TSHIRT_SIZES, validators=[Optional()])
    role = SelectField('角色', choices=[('member', '普通成员'), ('admin', '管理员')])
    member_type = SelectField('成员身份', choices=MEMBER_TYPES)
    submit = SubmitField('保存修改')


class TutorialForm(FlaskForm):
    title = StringField('视频标题', validators=[DataRequired(), Length(max=256)])
    description = TextAreaField('描述/简介', validators=[Optional()])
    video_url = StringField('视频链接', validators=[DataRequired(), Length(max=512)])
    submit = SubmitField('发布')


class OnlineContestForm(FlaskForm):
    title = StringField('比赛标题', validators=[DataRequired(), Length(max=256)])
    platform = SelectField('比赛平台', choices=[
        ('codeforces', 'Codeforces'),
        ('atcoder', 'AtCoder'),
        ('nowcoder', '牛客 (Nowcoder)'),
        ('luogu', '洛谷 (Luogu)'),
        ('leetcode', '力扣 (LeetCode)'),
        ('lanqiao', '蓝桥杯'),
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
    wuyu_type = SelectField('五育类型', choices=WUYU_CHOICES, validators=[DataRequired('请选择五育类型')])
    event_date = DateField('活动日期 (YYYY-MM-DD)', validators=[Optional()], format='%Y-%m-%d')
    registration_deadline = DateTimeField('报名截止时间', validators=[Optional()],
                                          format=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S'])
    is_open = BooleanField('开放报名')
    submit = SubmitField('发布')
