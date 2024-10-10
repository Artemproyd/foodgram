from django.db.models import Q
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import (status,
                            viewsets)
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated, IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from .filter import RecipeFilter, IngredientFilter
from .models import (Tag, Ingredient, Recipe,
                     UserRecipe, Favorite,
                     ShortLink)
from .serializers import (AvatarSerializer,
                          TagSerializer, IngredientSerializer,
                          CreateRecipeSerializer, GetRecipeSerializer,
                          RecipeInShoppingCard, SubscribeSerializer,
                          FavoriteSerializer, ShortLinkSerializer,
                          )
from .serializers import UserSerializer
from .pagination import CustomPagination
from users.models import User, Subscription


class MyUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, ]

    @action(
        detail=False,
        url_path='me',
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        return Response(UserSerializer(request.user).data,
                        status=status.HTTP_200_OK)

    @action(
        detail=False,
        url_path='me/avatar',
        methods=['put', 'delete'],
        serializer_class=AvatarSerializer,
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request):
        if request.method == 'PUT':
            user = request.user
            serializer = AvatarSerializer(
                instance=user,
                data=request.data,
                partial=True
            )
            if serializer.is_valid() and request.data != {}:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        url_path='subscriptions',
        pagination_class=CustomPagination,
    )
    def get_subscriptions(self, *args, **kwargs):
        subscriptions_list = Subscription.objects.filter(
            user=self.request.user)
        use1r = []
        for i in subscriptions_list:
            new_user = UserSerializer(i.subscribed_to).data
            new_user['is_subscribed'] = True
            if 'recipes_limit' in self.request.GET:
                new_user['limit'] = self.request.GET['recipes_limit']
            use1r.append(new_user)
        paginator = self.paginator
        result_page = paginator.paginate_queryset(use1r, self.request)
        serializer = SubscribeSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class TagView(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def list(self, request, *args, **kwargs):
        # Ну этот метод нельзя убрать тк, там просится
        # чтобы теги вернулись в ввиде массива, а там по
        # дефолту в другом формуте возвращаются
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ShortLinkViewSet(viewsets.ModelViewSet):
    serializer_class = ShortLinkSerializer

    def get_queryset(self):
        recipe_id = self.kwargs.get('recipes_id')
        recipe = Recipe.objects.filter(id=recipe_id).first()

        if recipe is None:
            return ShortLink.objects.none()
        return ShortLink.objects.filter(recipe=recipe)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        base_url = request.build_absolute_uri('/')[:-1]
        serializer.data[0]['short-link'] = (
            f'{base_url}:8000/s/'
            f'{serializer.data[0]["short-link"]}')

        return Response({'short-link': serializer.data[0]['short-link']})


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = IngredientFilter

    def list(self, request, *args, **kwargs):
        # Ну этот метод нельзя убрать тк, там просится
        # чтобы теги вернулись в ввиде массива, а там по
        # дефолту в другом формате возвращаются
        filterset = self.filterset_class(request.GET,
                                         queryset=self.get_queryset())
        queryset = filterset.qs
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ShoppingCartViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ]

    def create(self, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['recipes_id'])
        shopping_cart_obj = UserRecipe.objects.filter(
            Q(recipe_id=recipe.id) & Q(user_id=self.request.user.id)).exists()
        if recipe is not None and not shopping_cart_obj:
            UserRecipe.objects.bulk_create([
                UserRecipe(recipe=recipe, user=self.request.user)
            ])
            serializer = RecipeInShoppingCard(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['delete'],
    )
    def delete(self, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['recipes_id'])
        recipe_user = UserRecipe.objects.filter(recipe=recipe,
                                                user=self.request.user
                                                ).first()
        if recipe_user is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        recipe_user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = RecipeInShoppingCard
    permission_classes = [IsAuthenticated, ]

    def create(self, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['recipes_id'])
        favorite_obj = Favorite.objects.filter(
            Q(recipe_id=recipe.id)
            & Q(user_id=self.request.user.id)).exists()
        if recipe is not None and not favorite_obj:
            Favorite.objects.bulk_create([
                Favorite(recipe=recipe, user=self.request.user)
            ])
            serializer = FavoriteSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['delete'],
    )
    def delete(self, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['recipes_id'])
        favorite_obj = Favorite.objects.filter(
            recipe=recipe,
            user=self.request.user).first()
        if favorite_obj is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        favorite_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscribeViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscribeSerializer
    permission_classes = [IsAuthenticated, ]

    def get_serializer(self, *args, **kwargs):
        kwargs['user'] = self.request.user
        return super(SubscribeViewSet, self).get_serializer(*args, **kwargs)

    def create(self, *args, **kwargs):
        user = get_object_or_404(User, id=kwargs['user_id'])
        subscribe_obj = Subscription.objects.filter(
            Q(subscribed_to=user)
            & Q(user=self.request.user)).exists()
        if subscribe_obj is False and user != self.request.user:
            Subscription.objects.create(
                subscribed_to=user,
                user=self.request.user
            )
            user_serializer = UserSerializer(user).data
            user_serializer['is_subscribed'] = True
            if 'recipes_limit' in self.request.GET:
                user_serializer['limit'] = self.request.GET['recipes_limit']
            serializer = SubscribeSerializer(user_serializer).data
            return Response(serializer, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['delete'],
    )
    def delete(self, *args, **kwargs):
        user = get_object_or_404(User, id=kwargs['user_id'])
        subscribe_obj = Subscription.objects.filter(subscribed_to=user,
                                                    user=self.request.user
                                                    ).first()
        if subscribe_obj is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        subscribe_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    model = Recipe
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticatedOrReadOnly, ]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_serializer_class(self, action=None):
        if (action or self.action) in ('retrieve', 'list'):
            return GetRecipeSerializer
        return CreateRecipeSerializer

    def create(self, *args, **kwargs):
        serializer = CreateRecipeSerializer(
            data=self.request.data,
            partial=True
        )
        if serializer.is_valid():
            object1 = serializer.save(author=self.request.user)
            serializer_class = self.get_serializer_class(action='retrieve')
            serializer_data = serializer_class(object1).data
            ShortLink.objects.create(
                recipe=object1,
                original_url=f'recipes/{serializer_data["id"]}',
            )
            return Response(serializer_data,
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        self.object = serializer.save(author=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance,
                                         data=request.data,
                                         partial=partial)
        serializer.is_valid(raise_exception=True)
        if str(self.request.user) == 'AnonymousUser':
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if instance.author != self.request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        self.perform_update(serializer)
        return Response(GetRecipeSerializer(instance).data)

    def destroy(self, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['pk'])
        if recipe.author != self.request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated, ]
    )
    def dowload(self, *args, **kwargs):
        shopping_card = {}
        ur_objects = UserRecipe.objects.filter(
            user=self.request.user)
        for i in ur_objects:
            ing = GetRecipeSerializer(i.recipe).data['ingredients']
            for j in ing:
                if j['id'] not in shopping_card:
                    shopping_card[j['id']] = {
                        'name': j['name'],
                        'measurement_unit': j['measurement_unit'],
                        'amount': j['amount'],
                    }
                else:
                    shopping_card[j['id']]['amount'] += j['amount']
        content = '\n'.join(f'{key}: {value}'
                            for key, value in shopping_card.items())
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="file.txt"'

        return response
