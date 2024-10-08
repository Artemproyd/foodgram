from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet
from django import forms
from .constants import EXTRA_FIELD
from .forms import RecipeForm
from .models import (Favorite, IngredientsInRecipe,
                     Ingredient, Recipe,
                     Tag, TagRecipe,
                     ShortLink, UserRecipe)


class TagInRecipeInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if not any(form.cleaned_data for form in self.forms if not form.cleaned_data.get('DELETE', False)):
            raise ValidationError("Поле Теги не может быть пустым.")


class TagRecipeInline(admin.TabularInline):
    model = Recipe.tags.through
    formset = TagInRecipeInlineFormSet
    extra = EXTRA_FIELD


class IngredientsInRecipeInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if not any(form.cleaned_data for form in self.forms if not form.cleaned_data.get('DELETE', False)):
            raise ValidationError("Поле Ингредиенты не может быть пустым.")


class IngredientsInRecipeInline(admin.TabularInline):
    model = Recipe.ingredients.through
    formset = IngredientsInRecipeInlineFormSet
    extra = EXTRA_FIELD


class RecipeAdmin(admin.ModelAdmin):
    form = RecipeForm
    list_display = ('name', 'author', 'get_favorite_count')
    search_fields = ('name', 'author__username')
    list_filter = ('tags',)
    inlines = [IngredientsInRecipeInline, TagRecipeInline]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        try:
            super().save_related(request, form, formsets, change)

            ingredients_formset = next(
                (formset for formset in formsets if
                 isinstance(formset, BaseInlineFormSet) and
                 formset.model == Recipe.ingredients.through),
                None
            )

            if ingredients_formset is not None:
                if not ingredients_formset.is_valid():
                    raise ValidationError("Поле Ингредиенты не может быть пустым.")

                ingredients_in_recipe = ingredients_formset.cleaned_data
                if not any(data for data in ingredients_in_recipe
                           if data and not data.get('DELETE', False)):
                    raise ValidationError("Поле Ингредиенты не может быть пустым.")

            tags_formset = next(
                (formset for formset in formsets if
                 isinstance(formset, BaseInlineFormSet) and
                 formset.model == Recipe.tags.through),
                None
            )

            if tags_formset is not None:
                if not tags_formset.is_valid():
                    raise ValidationError("Поле Теги не может быть пустым.")

                tags_in_recipe = tags_formset.cleaned_data
                if not any(data for data in tags_in_recipe
                           if data and not data.get('DELETE', False)):
                    raise ValidationError("Поле Теги не может быть пустым.")

        except ValidationError as e:
            form.add_error(None, e)
            raise

    def get_favorite_count(self, obj):
        return Favorite.objects.filter(recipe=obj).count()

    get_favorite_count.short_description = 'Количество добавлений в избранное'


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


admin.site.register(Tag)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(IngredientsInRecipe)
admin.site.register(TagRecipe)
admin.site.register(UserRecipe)
admin.site.register(Favorite)
admin.site.register(ShortLink)
