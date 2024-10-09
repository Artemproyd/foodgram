from django.contrib.auth.models import AnonymousUser
import django_filters

from .models import Ingredient, Recipe


class RecipeFilter(django_filters.FilterSet):
    is_favorited = django_filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart')
    author = django_filters.NumberFilter(field_name='author__id')
    tags = django_filters.CharFilter(method='filter_tags')

    class Meta:
        model = Recipe
        fields = ['is_favorited',
                  'is_in_shopping_cart',
                  'author',
                  'tags']

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value == 1 and not isinstance(user, AnonymousUser):
            return queryset.filter(userrecipe__user=user).distinct()
        return queryset.none()

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value == 1 and not isinstance(user, AnonymousUser):
            return queryset.filter(favorite__user=user).distinct()
        return queryset.none()

    def filter_tags(self, queryset, name, value):
        tags = self.request.query_params.getlist('tags')
        if tags:
            return queryset.filter(tags__slug__in=tags).distinct()
        return queryset


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ['name']
