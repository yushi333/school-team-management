from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, Email
from app.constants import WUYU_CHOICES


PLATFORMS = [
    ('luogu', '洛谷 (Luogu)'),
    ('nowcoder', '牛客 (Nowcoder)'),
    ('atcoder', 'AtCoder'),
    ('codeforces', 'Codeforces'),
    ('leetcode', '力扣 (LeetCode)'),
    ('lanqiao', '蓝桥杯'),
]

# Platforms that can't be auto-scraped — manual count entry
MANUAL_PLATFORMS = ['leetcode', 'lanqiao']

GRADES = [
    ('', '请选择年级'),
    ('2022级', '2022级'),
    ('2023级', '2023级'),
    ('2024级', '2024级'),
    ('2025级', '2025级'),
    ('2026级', '2026级'),
    ('2027级', '2027级'),
    ('2028级', '2028级'),
    ('研究生', '研究生'),
]

STUDY_YEARS = [('', '请选择')] + [(f'{y}级', f'{y}级') for y in range(2022, 2031)] + [('研究生', '研究生')]
TSHIRT_SIZES = [('', '请选择'), ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL'), ('XXL', 'XXL'), ('XXXL', 'XXXL')]


class ProfileForm(FlaskForm):
    real_name = StringField('真实姓名', validators=[DataRequired('请输入姓名'), Length(max=64)])
    grade = SelectField('年级', choices=GRADES, validators=[Optional()])
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
    submit = SubmitField('保存修改')


class PlatformHandleForm(FlaskForm):
    luogu = StringField('洛谷 UID', validators=[Optional(), Length(max=128)])
    nowcoder = StringField('牛客 UID', validators=[Optional(), Length(max=128)])
    atcoder = StringField('AtCoder 用户名', validators=[Optional(), Length(max=128)])
    codeforces = StringField('Codeforces Handle', validators=[Optional(), Length(max=128)])
    leetcode = StringField('力扣 用户名', validators=[Optional(), Length(max=128)])
    lanqiao = StringField('蓝桥杯 账号', validators=[Optional(), Length(max=128)])
    # Manual counts for non-scrapable platforms
    leetcode_count = IntegerField('力扣 手动题量', validators=[Optional(), NumberRange(min=0)])
    lanqiao_count = IntegerField('蓝桥杯 手动题量', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('保存平台账号')


class RecruitmentForm(FlaskForm):
    title = StringField('招募标题', validators=[DataRequired('请输入标题'), Length(max=256)])
    competition_type = StringField('比赛类型', validators=[DataRequired('请输入比赛类型'), Length(max=128)])
    recruit_count = IntegerField('招募人数', validators=[DataRequired('请输入招募人数'), NumberRange(min=1, max=1000, message='招募人数需在1-1000之间')])
    wuyu_type = SelectField('五育类型', choices=WUYU_CHOICES, validators=[DataRequired('请选择五育类型')])
    requirement = TextAreaField('招募要求', validators=[DataRequired('请填写招募要求')])
    description = TextAreaField('补充说明', validators=[Optional()])
    submit = SubmitField('发布招募')
