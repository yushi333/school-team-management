"""Shared constants."""

# 五育分类：德育 / 智育 / 体育 / 劳育 / 美育
WUYU_TYPES = [
    ('deyu', '德育'),
    ('zhiyu', '智育'),
    ('tiyu', '体育'),
    ('laoyu', '劳育'),
    ('meiyu', '美育'),
]

WUYU_LABELS = dict(WUYU_TYPES)

# Same list but with an empty placeholder first — for required SelectFields
WUYU_CHOICES = [('', '请选择五育类型')] + WUYU_TYPES
