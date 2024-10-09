from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

from .views import (MyUserViewSet, IngredientsViewSet,
                    RecipeViewSet, ShoppingCartViewSet,
                    FavoriteViewSet, SubscribeViewSet,
                    ShortLinkViewSet, TagView)

api_v1 = DefaultRouter()
api_v1.register('users', MyUserViewSet, basename='user')
api_v1.register('tags', TagView, basename='Tag')
api_v1.register('ingredients', IngredientsViewSet, basename='Ingredient')
api_v1.register('recipes', RecipeViewSet, basename='Ingredient')
api_v1.register(r'recipes/(?P<recipes_id>\d+)/shopping_cart',
                ShoppingCartViewSet,
                basename='ShoppingCart')
api_v1.register(r'recipes/(?P<recipes_id>\d+)/favorite',
                FavoriteViewSet,
                basename='Favorite')
api_v1.register(r'recipes/(?P<recipes_id>\d+)/get-link',
                ShortLinkViewSet,
                basename='ShortLink')
api_v1.register(r'users/(?P<user_id>\d+)/subscribe',
                SubscribeViewSet,
                basename='Subscribe')


urlpatterns = [
    path('', include(api_v1.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
