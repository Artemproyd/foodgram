from rest_framework.routers import DefaultRouter
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import UserViewSet3, TagView, IngredientsViewSet, RecipeViewSet
api_v1 = DefaultRouter()
api_v1.register('users', UserViewSet3, basename='user')
api_v1.register('tags', TagView, basename='Tag')
api_v1.register('ingredients', IngredientsViewSet, basename='Ingredient')
api_v1.register('recipes', RecipeViewSet, basename='Ingredient')


urlpatterns = [
    # path('users/me/avatar/', Ima.as_view(), name='f'),
    path('', include(api_v1.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

    # path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    # path('users/', UserViewSet3.as_view({'get': 'list'}), name='user-list'),