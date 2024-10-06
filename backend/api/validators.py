from django.core.validators import RegexValidator
import re
from django.core.exceptions import ValidationError

username_validator = RegexValidator(
    regex=r'$',
    message='В имени недопустимые символы',
    code='invalid_username'
)


def validate_name(value):
    if not re.match(r'^[\w.@+-]+$', value):
        ValidationError(
            ('Имя может содержать только буквы'
             ' и цифры. Специальные символы недопустимы.'),
            params={'value': value},
        )
