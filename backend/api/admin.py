from django.contrib import admin
from models import (Favorite, IngredientsInRecipe,
                    Ingredient, Recipe,
                    Tag, TagRecipe,
                    ShortLink, UserRecipe)

admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(IngredientsInRecipe)
admin.site.register(TagRecipe)
admin.site.register(UserRecipe)
admin.site.register(Favorite)
admin.site.register(ShortLink)
