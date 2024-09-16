from django.core.validators import RegexValidator

username_validator = RegexValidator(
    regex=r'$',
    message='В имени недопустимые символы',
    code='invalid_username'
)

import re
from django.core.exceptions import ValidationError


def validate_name(value):
    if not re.match(r'^[\w.@+-]+$', value):
         ValidationError(
            ('Имя может содержать только буквы и цифры. Специальные символы недопустимы.'),
            params={'value': value},
        )