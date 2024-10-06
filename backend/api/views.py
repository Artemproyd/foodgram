from django.http import HttpResponse
from djoser.views import UserViewSet
from django.shortcuts import get_object_or_404
from django.db.models import Q
from models import (Tag, Ingredient, Recipe,
                    UserRecipe, TagRecipe, Favorite,
                    ShortLink)
from users.models import User, Subscription
from permissions import IsRegisteredBy, ReadOnly
from rest_framework import (pagination, status,
                            viewsets)
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated, IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet as StdModelViewSet
from serializers import (AvatarSerializer,
                         TagSerializer, IngredientSerializer,
                         RecipeSerializer, ReadSerializer,
                         RecipeInShoppingCard, SubscribeSerializer,
                         FavoriteSerializer, ShortLinkSerializer11,
                         )
from serializers import UserSerializer


class CustomPagination(pagination.PageNumberPagination):
    max_page_size = 10
    page_size = 10

    def get_page_size(self, request):
        page_size = request.query_params.get('limit', None)
        if page_size is not None:
            try:
                return min(int(page_size), self.max_page_size)
            except ValueError:
                return self.page_size
        return self.page_size


class ModelViewSet(StdModelViewSet):
    permission_classes = [IsRegisteredBy | ReadOnly]

    @classmethod
    def get_url_name(cls):
        name = getattr(cls, 'queryset', None)
        name = name.model if name else getattr(cls, 'model', None)
        if name is None:
            raise ValueError(
                "%s cannot be registered automatically, "
                "define model or queryset attribute for it." % (cls.__name__))
        return name._meta.verbose_name_plural.replace(' ', '_')

    def get_queryset(self):
        return self.model._default_manager.all()


class UserViewSet3(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

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
            else:
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            user = request.user
            user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, *args, **kwargs):
        if 'id' in kwargs:
            user = get_object_or_404(User, id=kwargs['id'])
            serializer = UserSerializer(user)
            return Response(serializer.data)
        else:
            user = request.user
            full_url = request.build_absolute_uri()
            if 'me' in str(full_url) and str(user) == 'AnonymousUser':
                return Response(status=401)

            serializer = UserSerializer(user)
            return Response(serializer.data)

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


class TagView(viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def get(self, request, *args, **kwargs):
        if kwargs == {}:
            tag = Tag.objects.all()
            serializer = TagSerializer(tag, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            tag = get_object_or_404(Tag, id=kwargs['pk'])
            serializer = TagSerializer(tag)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        return Response('Forbidden',
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response('Forbidden',
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)


class ShortLinkViewSet(viewsets.ModelViewSet):
    serializer_class = ShortLinkSerializer11

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
        serializer.data[0]['short-link'] = \
            f'{base_url}:8000/s/{serializer.data[0]["short-link"]}'
        return Response({"short-link": serializer.data[0]['short-link']})


class IngredientsViewSet(viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer

    def get(self, request, *args, **kwargs):
        print(request.GET)
        if kwargs != {}:
            ingredient = get_object_or_404(Ingredient, id=kwargs['pk'])
            serializer = IngredientSerializer(ingredient)
        elif 'name' in request.GET:
            ingredient = Ingredient.objects.filter(
                name__startswith=request.GET['name'])
            serializer = IngredientSerializer(ingredient, many=True)
        else:
            ingredient = Ingredient.objects.all()
            serializer = IngredientSerializer(ingredient, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        return Response('Forbidden',
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response('Forbidden',
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)


class ShoppingCartViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeInShoppingCard
    permission_classes = [IsAuthenticated, ]

    def create(self, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['recipes_id'])
        obj = UserRecipe.objects.filter(
            Q(recipe_id=recipe.id) & Q(user_id=self.request.user.id)).exists()
        if recipe is not None and not obj:
            UserRecipe.objects.bulk_create([
                UserRecipe(recipe=recipe, user=self.request.user)
            ])
            serializer = FavoriteSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
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
        else:
            recipe_user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteViewSet(ModelViewSet):
    serializer_class = RecipeInShoppingCard
    permission_classes = [IsAuthenticated, ]

    def create(self, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['recipes_id'])
        obj = Favorite.objects.filter(
            Q(recipe_id=recipe.id) &
            Q(user_id=self.request.user.id)).exists()
        if recipe is not None and not obj:
            Favorite.objects.bulk_create([
                Favorite(recipe=recipe, user=self.request.user)
            ])
            serializer = FavoriteSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['delete'],
    )
    def delete(self, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['recipes_id'])
        favorite_obj = Favorite.objects.filter(recipe=recipe,
                                               user=
                                               self.request.user).first()
        if favorite_obj is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            favorite_obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class SubscribeViewSet(ModelViewSet):
    serializer_class = SubscribeSerializer
    permission_classes = [IsAuthenticated, ]

    def get_serializer(self, *args, **kwargs):
        kwargs['user'] = self.request.user
        return super(SubscribeViewSet, self).get_serializer(*args, **kwargs)

    def create(self, *args, **kwargs):
        user = get_object_or_404(User, id=kwargs['user_id'])
        obj = Subscription.objects.filter(
            Q(subscribed_to=user)
            & Q(user=self.request.user)).exists()
        if user is not None and obj is False and user != self.request.user:
            Subscription.objects.create(
                subscribed_to=user,
                user=self.request.user
            )
            user_serializer = UserSerializer(user).data
            user_serializer['is_subscribed'] = True
            serializer = SubscribeSerializer(user_serializer).data
            return Response(serializer, status=status.HTTP_201_CREATED)
        else:
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
        else:
            subscribe_obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(ModelViewSet):
    model = Recipe
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticatedOrReadOnly, ]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        item = []
        if 'pk' in self.kwargs:
            item = Recipe.objects.filter(id=int(self.kwargs['pk']))
        elif 'tags' in self.request.GET:
            tags_name = self.request.GET.getlist('tags')
            tags_id = []
            for tag in tags_name:
                tags_id.append(Tag.objects.filter(slug=str(tag)).first())
            print(tags_id)
            query = Q()
            for tag in tags_id:
                query |= Q(tag=tag)

            queryset = TagRecipe.objects.filter(query)
            queryset1 = []
            for j in queryset:
                queryset1.append(j.recipe)
            item = list(set(queryset1))
        elif 'author' in self.request.GET:
            item = Recipe.objects.filter(author_id=self.request.GET['author'])
        elif 'is_in_shopping_cart' in self.request.GET:
            if str(self.request.user) != 'AnonymousUser':
                queryset = UserRecipe.objects.filter(user=self.request.user)
                for i in queryset:
                    item.append(i.recipe)
        elif 'is_favorited' in self.request.GET:
            if str(self.request.user) != 'AnonymousUser':
                queryset = UserRecipe.objects.filter(user=self.request.user)
                for i in queryset:
                    item.append(i.recipe)
        else:
            item = Recipe.objects.all()
        return item

    def get_serializer_class(self, action=None):
        if (action or self.action) in ('retrieve', 'list'):
            return ReadSerializer
        return RecipeSerializer

    def create(self, *args, **kwargs):
        serializer = RecipeSerializer(
            data=self.request.data,
            partial=True
        )
        if serializer.is_valid():
            object1 = serializer.save(author=self.request.user)
            serializer_class = self.get_serializer_class(action="retrieve")
            serializer_data = serializer_class(object1).data
            ShortLink.objects.create(
                recipe=object1,
                original_url=f'recipes/{serializer_data["id"]}',
            )
            return Response(serializer_data,
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
        return Response(ReadSerializer(instance).data)

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
        ur_objects = UserRecipe.objects.filter(user=
                                               self.request.user)
        for i in ur_objects:
            ing = ReadSerializer(i.recipe).data['ingredients']
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
