from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model


class User(AbstractUser):

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name',
    )

    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150,
    )

    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150,
    )

    username = models.CharField(
        verbose_name='Имя пользователя',
        unique=True,
        error_messages={
            'unique': 'Данное имя занято',
        },
        validators=[RegexValidator(regex=r'^[\w.@+-]+$', message='Ваше сообщение об ошибке')],
        max_length=150,
    )

    email = models.EmailField(
        verbose_name="Адрес электронной почты",
        unique=True,
        error_messages={
            'unique': 'Данный адрес электронной почты уже зарегистрирован',
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
    user = models.ForeignKey(User, related_name='subscriptions', on_delete=models.CASCADE)
    subscribed_to = models.ForeignKey(User, related_name='subscribers', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'subscribed_to')




