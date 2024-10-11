from django.db.models import Q
from drf_extra_fields.fields import Base64ImageField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework import serializers

from .models import (Favorite, Ingredient, IngredientsInRecipe,
                     Recipe, ShortLink, TagRecipe,
                     Tag, UserRecipe,)
from users.models import User, Subscription


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(user=request.user,
                                               subscribed_to=obj).exists()
        return False


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['avatar', ]


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = [
            'id',
            'name',
            'slug',
        ]


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = [
            'id',
            'name',
            'measurement_unit',
        ]


class IngredientsInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredients',
        queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source='ingredients.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredients.measurement_unit')

    class Meta:
        model = IngredientsInRecipe
        fields = ['id', 'name', 'measurement_unit', 'amount']


class TagsRecipe(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(source='tags',
                                            queryset=Tag.objects.all())
    name = serializers.ReadOnlyField(source='tags.slug')
    # tag = TagSerializer()

    class Meta:
        model = TagRecipe
        fields = ['id', 'name']


class FavoriteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    image = serializers.CharField()
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Favorite
        fields = ['id', 'name', 'image', 'cooking_time']


class RecipeInShoppingCard(serializers.ModelSerializer):
    id = PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    name = PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    cooking_time = PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = UserRecipe
        fields = [
            'id',
            'name',
            'cooking_time',
            'image',
        ]


class CreateRecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientsInRecipeSerializer(source='ingredients_recipes',
                                                many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True)
    image = Base64ImageField(required=False, allow_null=True)
    author = UserSerializer(default=serializers.CurrentUserDefault())
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    MANY_FIELDS = {'ingredients_recipes': 'update_ingredients',
                   'tags': 'tags_update'}

    class Meta:
        model = Recipe
        fields = [
            'id',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'is_in_shopping_cart',
            'is_favorited',
            'cooking_time',
            'author',
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(CreateRecipeSerializer, self).__init__(*args, **kwargs)

    def to_representation(self, instance):
        # Умоляю не бей. Я не придумал ничего лучше
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(instance.tags.all(),
                                               many=True).data
        return representation

    @classmethod
    def create_tags(cls, recipe_id, tags):
        TagRecipe.objects.bulk_create([
            TagRecipe(recipe_id=recipe_id, tag_id=tag.id)
            for tag in tags
        ])

    @classmethod
    def tags_update(cls, instance, data):
        old_tags_ids = set(instance.tags.values_list('id', flat=True))
        new_tags_ids = set([a.id for a in data])
        TagRecipe.objects.filter(recipe_id=instance.id,
                                 tag_id__in=old_tags_ids - new_tags_ids
                                 ).delete()
        cls.create_tags(
            instance.id,
            [tag for tag in data if tag.id in new_tags_ids - old_tags_ids])

    @classmethod
    def create_ingredients(cls, recipe_id, ingredients):
        print(ingredients)
        ingredients_dict = {ba['ingredients'].id: ba for ba in ingredients}
        IngredientsInRecipe.objects.bulk_create([
            IngredientsInRecipe(recipe_id=recipe_id, **ba)
            for ba in ingredients_dict.values()
        ])

    @classmethod
    def update_ingredients(cls, instance, new_ingredients):
        IngredientsInRecipe.objects.filter(recipe_id=instance.id).delete()
        cls.create_ingredients(instance.id, new_ingredients)

    def get_is_in_shopping_cart(self, validate_data):
        try:

            return UserRecipe.objects.filter(
                Q(recipe=validate_data) & Q(user=self.user)
            ).exists()
        except Exception:
            return False

    def get_is_favorited(self, validate_data):
        try:
            obj = Favorite.objects.filter(
                Q(recipe=validate_data)
                & Q(user=self.user)
            ).exists()
            return obj
        except Exception:
            return False

    def update_many2us(self, instance, validated_data):
        for field, updater_name in self.MANY_FIELDS.items():
            data = validated_data.pop(field, None)
            updater = getattr(self, updater_name)
            if data is not None or not self.partial:
                updater(instance, data or [])
        return instance

    def split_validated_data(self, validated_data):
        basic = {
            key: value for key, value in validated_data.items()
            if key not in self.MANY_FIELDS
        }
        many2m = {
            key: validated_data[key]
            for key in self.MANY_FIELDS if key in validated_data
        }
        field_names = list(self.fields.keys())
        field_names.remove('id')
        field_names.remove('is_in_shopping_cart')
        field_names.remove('is_favorited')
        for i in field_names:
            if not (str(i) in validated_data):
                if str(i) == 'ingredients':
                    i = 'ingredients_recipes'
                elif str(i) == 'ingredients_recipes':
                    i = 'ingredients'
                if not (str(i) in validated_data):
                    raise serializers.ValidationError(
                        f'Рецепт должен иметь {str(i)}.')
        for i in (many2m.keys()):
            if not many2m[str(i)]:
                raise serializers.ValidationError(f'Рецепт должен'
                                                  f' иметь хотя бы '
                                                  f'1 {str(i)}.')
        if validated_data['image'] is None:
            raise serializers.ValidationError('Рецепт должен '
                                              'содержать фотографию.')
        seen = set()
        bool_dublicate = any(tuple(od.items()) in seen
                             or seen.add(tuple(od.items()))
                             for od in many2m['ingredients_recipes'])
        if bool_dublicate:
            raise serializers.ValidationError('В рецепте не должно'
                                              ' быть повторяющихся'
                                              ' ингредиетов.')
        elif len(many2m['tags']) != len(set(many2m['tags'])):
            raise serializers.ValidationError('В рецепте'
                                              ' не должно быть'
                                              ' повторяющихся тегов.')
        return basic, many2m

    def create(self, validated_data):
        basic, many2us = self.split_validated_data(validated_data)
        recipe_object = self.update_many2us(
            super().create(basic),
            many2us)
        ShortLink.objects.create(
            recipe=recipe_object,
            original_url=f'recipes/{recipe_object.id}',
        )
        return recipe_object

    def update(self, instance, validated_data):
        validated_data['author'] = instance.author
        basic, many2us = self.split_validated_data(validated_data)
        return self.update_many2us(super().update(instance, basic), many2us)


class RecipeShortSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    image = Base64ImageField(required=False, allow_null=True)
    cooking_time = serializers.IntegerField()

    class Meta:
        fields = [
            'id',
            'name',
            'image',
            'cooking_time',
        ]


class SubscribeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.CharField()
    is_subscribed = serializers.BooleanField()
    avatar = serializers.CharField()
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        fields = ['id',
                  'username',
                  'first_name',
                  'last_name',
                  'email',
                  'avatar',
                  'recipes_count',
                  'recipes', ]

    def get_recipes(self, value):
        if 'limit' in value:
            items = Recipe.objects.filter(
                author_id=value['id'])[:int(value['limit'])]
        else:
            items = Recipe.objects.filter(author_id=value['id'])
        ret_list = RecipeShortSerializer(items, many=True)
        return ret_list.data

    def get_recipes_count(self, value):
        items = Recipe.objects.filter(author_id=value['id'])
        if 'limit' in value:
            return min(len(items), int(value['limit']))
        else:
            return len(items)


class FullShortLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShortLink
        fields = ['id', 'original_url', 'short_url']


class ShortLinkSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShortLink
        fields = ['short_url']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['short-link'] = representation.pop('short_url')
        return representation
