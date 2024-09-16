from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from users.models import User


class Tag(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):

    name = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Название ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=150,
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
        max_length=150,
        blank=False,
        null=False,
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
        validators=[MinValueValidator(1)]
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
        related_name="ingredients_recipes",
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

    def __str__(self):
        return f'Тег: {self.recipe.name} slug: {self.tag.name}'
