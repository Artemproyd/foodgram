from django.shortcuts import render
from djoser import views as djoser_views
from djoser.views import UserViewSet
from users.models import User
from .models import Tag, Ingredient, Recipe
from django.shortcuts import get_object_or_404
from .serializers import (UserSerializer, AvatarSerializer,
                          TagSerializer, IngredientSerializer,
                          RecipeSerializer, ReadSerializer
                          )
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly,
)
from rest_framework import generics

from rest_framework import status
from rest_framework import filters, status, viewsets
from rest_framework.response import Response
import logging
from .serializers import UserSerializer
from rest_framework.viewsets import ModelViewSet as StdModelViewSet, ViewSet, GenericViewSet
from .permissions import IsRegisteredBy, ReadOnly, OwnerOrReadOnly


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
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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


from rest_framework import viewsets, filters, mixins

from .permissions import IsAdminOnly, ReadOnly


class CRDViewSet(mixins.ListModelMixin,
                 mixins.DestroyModelMixin,
                 viewsets.GenericViewSet
                 ):
    """Миксин для вьюсетов Category и Genre."""

    permission_classes = (ReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    # lookup_field = 'slug'


class TagView(viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def get(self, request, *args, **kwargs):
        if kwargs == {}:
            tag = Tag.objects.all()
            serializer = TagSerializer(tag, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # if str(request.user) == 'AnonymousUser':
            #     return Response('Not found', status=status.HTTP_200_OK)
            tag = get_object_or_404(Tag, id=kwargs['pk'])
            serializer = TagSerializer(tag)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        return Response('Forbidden', status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response('Forbidden', status=status.HTTP_405_METHOD_NOT_ALLOWED)


class IngredientsViewSet(viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer

    def get(self, request, *args, **kwargs):
        print(request.GET)
        if kwargs != {}:
            ingredient = get_object_or_404(Ingredient, id=kwargs['pk'])
            serializer = IngredientSerializer(ingredient)
        elif 'name' in request.GET:
            ingredient = Ingredient.objects.filter(name__startswith=request.GET['name'])
            serializer = IngredientSerializer(ingredient, many=True)
        else:
            ingredient = Ingredient.objects.all()
            serializer = IngredientSerializer(ingredient, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        return Response('Forbidden', status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response('Forbidden', status=status.HTTP_405_METHOD_NOT_ALLOWED)


from rest_framework import viewsets, pagination


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


class RecipeViewSet(ModelViewSet):
    # queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticated, OwnerOrReadOnly)
    model = Recipe
    pagination_class = CustomPagination

    def get_queryset(self):
        print(self.request.GET)

        # qs = super().get_queryset().select_related('author')
        # author_id = self.kwargs.get("author_id", None)
        # if author_id is not None:
        #     qs = qs.filter(authors__id=author_id)
        # print(qs)
        # return qs
        # print(kwargs)
        # print(self.request)
        # print(args)
        print(self.kwargs)
        if 'pk' in self.kwargs:
            item = Recipe.objects.filter(id=int(self.kwargs['pk']))
        elif 'tags' in self.request.GET:
            item = Recipe.objects.filter(tags_id=self.request.GET['tags'])
        elif 'author' in self.request.GET:
            item = Recipe.objects.filter(author_id=self.request.GET['author'])
        else:
            item = Recipe.objects.all()
        print(item)
        return item

    def get_serializer_class(self, action=None):
        if (action or self.action) in ('retrieve', 'list'):
            return ReadSerializer
        # return WriteBookCreateAuthorSerializer
        return RecipeSerializer

    # def perform_create(self, serializer):
    #     self.object = serializer.save(registered_by=self.request.user)
    #
    # def create(self, request, *args, **kwargs):
    #     super().create(request, *args, **kwargs)
    #     serializer_class = self.get_serializer_class(action="retrieve")
    #     return Response(serializer_class(instance=self.object).data)
    def create(self, *args, **kwargs):
        serializer = RecipeSerializer(
            data=self.request.data,
            partial=True
        )
        if serializer.is_valid():
            self.object = serializer.save(author=self.request.user)
            serializer_class = self.get_serializer_class(action="retrieve")
            print(serializer.data)
            return Response(serializer_class(instance=self.object).data,
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        print("ggsdffsdg")
        self.object = serializer.save()

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        serializer_class = self.get_serializer_class(action="retrieve")
        print("fffff")
        return Response(serializer_class(instance=self.object).data)
    # def update(self, request, *args, **kwargs):
    #     serializer = RecipeSerializer(
    #         data=self.request.data,
    #         partial=True
    #     )
    #     if serializer.is_valid():
    #         self.object = serializer.save(author=self.request.user)
    #         serializer_class = self.get_serializer_class(action="retrieve")
    #         print(serializer.data)
    #         return Response(serializer_class(instance=self.object).data,
    #                         status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def update(self, *args, **kwargs):
    #     serializer = RecipeSerializer(
    #         data=self.request.data,
    #         partial=True
    #     )
    #     if serializer.is_valid():
    #         self.object = serializer.save(author=self.request.user)
    #         serializer_class = self.get_serializer_class(action="retrieve")
    #         print(serializer.data)
    #         return Response(serializer_class(instance=self.object).data,
    #                         status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class TagView(viewsets.ModelViewSet):
#     permission_classes = [AllowAny]
#     serializer_class = TagSerializer
#
#     @action(
#         detail=False,
#         methods=['get'],
#         serializer_class=TagSerializer,
#     )
#     def get_queryset(self, *args, **kwargs):
#         print(kwargs)
#         print(args)
#         items = Tag.objects.all()
#         print(items)
#         print(type(items))
#         serializer = TagSerializer(items, many=True)
#         print(serializer)
#         return list(serializer.data)
#
#     @action(
#         detail=True,
#         methods=['get'],
#         serializer_class=TagSerializer,
#     )
#     def get_queryset(self):
#         item = get_object_or_404(Tag, id=self.kwargs['pk'])
#         return item
