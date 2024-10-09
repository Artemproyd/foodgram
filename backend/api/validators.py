from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
import re

from .constants import REGEX


username_validator = RegexValidator(
    regex=r'$',
    message='В имени недопустимые символы',
    code='invalid_username'
)


def validate_name(value):
    if not re.match(REGEX, value):
        raise ValidationError(
            _('Имя не должно содержать специальных символов.'),
            params={'value': value},
        )
