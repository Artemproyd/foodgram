from django.core.validators import RegexValidator
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re
from django.core.exceptions import ValidationError
from .constants import REGEX

username_validator = RegexValidator(
    regex=r'$',
    message='В имени недопустимые символы',
    code='invalid_username'
)


def validate_name(value):
    if not re.match(REGEX, value):  # Разрешаем только буквы, цифры и пробелы
        raise ValidationError(
            _('Имя не должно содержать специальных символов.'),
            params={'value': value},
        )