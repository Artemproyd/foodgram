from django.db import models
from django.contrib.auth.models import AbstractUser

from api.validators import validate_name
from api.constants import MAX_LENGTH_DEFAULT


class User(AbstractUser):

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name',
    )

    first_name = models.CharField(
        verbose_name='Имя',
        max_length=MAX_LENGTH_DEFAULT,
    )

    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=MAX_LENGTH_DEFAULT,
    )

    username = models.CharField(
        verbose_name='Имя пользователя',
        unique=True,
        error_messages={
            'unique': 'Данное имя занято',
        },
        validators=[validate_name],
        max_length=MAX_LENGTH_DEFAULT,
    )

    email = models.EmailField(
        verbose_name="Адрес электронной почты",
        unique=True,
        error_messages={
            'unique': 'Данный адрес электронной'
                      ' почты уже зарегистрирован',
        },
    )

    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(User,
                             related_name='subscriptions',
                             on_delete=models.CASCADE)
    subscribed_to = models.ForeignKey(User,
                                      related_name='subscribers',
                                      on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'subscribed_to'],
                name='unique_subscription',
            )
        ]
