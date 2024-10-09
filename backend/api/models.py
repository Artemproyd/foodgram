from django.core.validators import MinValueValidator
from django.db import models
import random
import string

from .constants import (MAX_LENGTH_DEFAULT,
                        MAX_LENGTH_TEN,
                        MAX_LENGTH_EIGHT,
                        MIN_VALIDATE,)
from users.models import User



class Tag(models.Model):
    name = models.CharField(max_length=MAX_LENGTH_DEFAULT)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):

    name = models.CharField(
        max_length=MAX_LENGTH_DEFAULT,
        unique=True,
        verbose_name='Название ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH_DEFAULT,
        default='г'
    )

    def __str__(self):
        return f'{self.name} {self.measurement_unit}'


class Recipe(models.Model):

    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        db_index=True,
    )

    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=MAX_LENGTH_DEFAULT,
        blank=False,
        null=False,
        unique=True,
    )

    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='RecipeTags',
        through='TagRecipe',
        blank=False,
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        related_name='recipes_ingredients',
        through='IngredientsInRecipe',
        blank=False,
    )

    cooking_time = models.IntegerField(
        verbose_name='Время приготовления',
        validators=[MinValueValidator(MIN_VALIDATE)]
    )

    text = models.TextField(
        verbose_name='Описание рецепта',
    )

    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Изображение',
        null=False,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientsInRecipe(models.Model):

    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Название рецепта',
        related_name='ingredients_recipes',
        on_delete=models.CASCADE,
    )

    ingredients = models.ForeignKey(
        Ingredient,
        verbose_name='Название',
        related_name='ingredients_recipes',
        on_delete=models.CASCADE,
    )

    amount = models.IntegerField(
        verbose_name='Единица измерения',
        validators=[MinValueValidator(1)]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredients'],
                name='unique_ingredient',
            )
        ]


class TagRecipe(models.Model):

    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Название рецепта',
        related_name='TagsRecipe',
        on_delete=models.CASCADE,
    )
    tag = models.ForeignKey(
        Tag,
        verbose_name='Название',
        related_name='TagsRecipe',
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'tag'],
                name='unique_tag',
            )
        ]

    def __str__(self):
        return f'Тег: {self.recipe.name} slug: {self.tag.name}'


class UserRecipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    in_cart = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique_user_shopping_card',
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique_favorite_recipe',
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class ShortLink(models.Model):
    recipe = models.OneToOneField(Recipe,
                                  unique=True,
                                  on_delete=models.CASCADE)
    original_url = models.URLField()
    short_url = models.CharField(max_length=MAX_LENGTH_TEN,
                                 unique=True)

    def save(self, *args, **kwargs):
        if not self.short_url:
            self.short_url = self.generate_short_url()
        super().save(*args, **kwargs)

    def generate_short_url(self):
        length = MAX_LENGTH_EIGHT
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))
