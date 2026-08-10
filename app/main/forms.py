from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Optional


PLATFORMS = [
    ('luogu', '洛谷 (Luogu)'),
    ('nowcoder', '牛客 (Nowcoder)'),
    ('atcoder', 'AtCoder'),
    ('codeforces', 'Codeforces'),
]

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


class ProfileForm(FlaskForm):
    real_name = StringField('真实姓名', validators=[DataRequired('请输入姓名'), Length(max=64)])
    grade = SelectField('年级', choices=GRADES, validators=[Optional()])
    submit = SubmitField('保存修改')


class PlatformHandleForm(FlaskForm):
    luogu = StringField('洛谷 UID', validators=[Optional(), Length(max=128)])
    nowcoder = StringField('牛客 UID', validators=[Optional(), Length(max=128)])
    atcoder = StringField('AtCoder 用户名', validators=[Optional(), Length(max=128)])
    codeforces = StringField('Codeforces Handle', validators=[Optional(), Length(max=128)])
    submit = SubmitField('保存平台账号')
