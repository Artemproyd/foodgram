from django.contrib import admin
from .models import (Tag, Ingredient, Recipe,
                     IngredientsInRecipe, TagRecipe,
                     UserRecipe, Favorite, ShortLink)

admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(IngredientsInRecipe)
admin.site.register(TagRecipe)
admin.site.register(UserRecipe)
admin.site.register(Favorite)
admin.site.register(ShortLink)
