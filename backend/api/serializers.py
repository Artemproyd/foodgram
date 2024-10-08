from django.db.models import Q
from rest_framework.relations import SlugRelatedField, PrimaryKeyRelatedField
from rest_framework.serializers import CharField
from rest_framework import serializers
from .models import (Favorite, Ingredient, IngredientsInRecipe,
                     Recipe, ShortLink, TagRecipe,
                     Tag, UserRecipe,
                     )
from users.models import User, Subscription
from drf_extra_fields.fields import Base64ImageField


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
    id = serializers.IntegerField()

    class Meta:
        model = Tag
        fields = [
            'id',
            'name',
            'slug',
        ]


class IngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    measurement_unit = serializers.CharField()

    class Meta:
        model = Ingredient
        fields = [
            'id',
            'name',
            'measurement_unit',
        ]


class IngredientsInRecipeSerializer(serializers.ModelSerializer):
    id = SlugRelatedField("id", source="ingredients",
                          queryset=Ingredient.objects.all())
    name = serializers.SlugRelatedField("name", source="ingredients",
                                        queryset=Ingredient.objects.all())
    measurement_unit = serializers.SlugRelatedField(
        'measurement_unit',
        source="ingredients",
        queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientsInRecipe
        fields = ['id', 'name', 'measurement_unit', 'amount']


class TagsRecipe(serializers.ModelSerializer):
    id = SlugRelatedField("id", source="ingredients",
                          queryset=Ingredient.objects.all())

    class Meta:
        model = TagRecipe
        fields = ['id']


class FavoriteSerializer(serializers.Serializer):
    id = PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    name = serializers.CharField()
    image = serializers.CharField()
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Favorite
        fields = ['id', 'name', 'image', 'cooking_time']


# Ну если дело было только в названии, то я переделал
# А если вопрос зачем он в целом нужен, то это для
# того, чтобы красиво рецепт выдавался. Ну если очень кратко
# то RecipeSerializer для создание, а этот для выдачи
class ReadRecipeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    tags = TagSerializer(many=True)
    author = UserSerializer(default=serializers.CurrentUserDefault)
    ingredients = IngredientsInRecipeSerializer(source='ingredients_recipes',
                                                many=True)
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    name = serializers.CharField()
    image = Base64ImageField(required=False, allow_null=True)
    text = CharField()
    cooking_time = serializers.IntegerField()

    class Meta:
        fields = [
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('context', {}).get('request', None)
        super(ReadRecipeSerializer, self).__init__(*args, **kwargs)

    def get_is_in_shopping_cart(self, validate_data):
        try:
            obj = UserRecipe.objects.filter(
                Q(recipe=validate_data)
                & Q(user=self.request.user)
            ).exists()
            return obj
        except Exception:
            return False

    def get_is_favorited(self, validate_data):
        try:
            obj = Favorite.objects.filter(
                Q(recipe=validate_data)
                & Q(user=self.request.user)
            ).exists()
            return obj
        except Exception:
            return False


class RecipeInShoppingCard(serializers.ModelSerializer):
    id = PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    name = PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    cooking_time = PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    author = UserSerializer(default=serializers.CurrentUserDefault)
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = UserRecipe
        fields = [
            'id',
            'author',
            'name',
            'cooking_time',
            'image',
        ]


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientsInRecipeSerializer(source='ingredients_recipes',
                                                many=True)
    tags = PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    image = Base64ImageField(required=False, allow_null=True)
    author = UserSerializer(default=serializers.CurrentUserDefault)

    MANY_FIELDS = {'ingredients_recipes': 'update_authors',
                   'tags': 'tags_update'}

    class Meta:
        model = Recipe
        fields = [
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'author',
        ]

    @classmethod
    def tags_update(cls, instance, data):
        old_tags_ids = set(instance.tags.values_list('id', flat=True))
        new_tags_ids = set([a.id for a in data])
        TagRecipe.objects.filter(recipe_id=instance.id,
                                 tag_id__in=old_tags_ids - new_tags_ids
                                 ).delete()
        TagRecipe.objects.bulk_create([
            TagRecipe(recipe_id=instance.id,
                      tag_id=tag_id) for tag_id in new_tags_ids - old_tags_ids
        ])

    @classmethod
    def update_authors(cls, instance, new_authors):
        old_authors_dict = {ba.ingredients_id: ba
                            for ba in instance.ingredients_recipes.all()}
        new_authors_dict = {ba['ingredients'].id: ba
                            for ba in new_authors
                            if ba['ingredients'].id not in old_authors_dict}
        updated_authors_dict = {ba['ingredients'].id: ba
                                for ba in new_authors
                                if ba['ingredients'].id in old_authors_dict}
        old_authors_set = (set(old_authors_dict.keys())
                           - set(updated_authors_dict.keys()))
        updated_authors_dict = dict(filter(
            lambda kv: kv[1]['amount'] != old_authors_dict[kv[0]].amount and (
                  kv[1]['amount'] is not None or
                  old_authors_dict[kv[0]].amount is not None),
            updated_authors_dict.items()
        ))
        IngredientsInRecipe.objects.filter(recipe_id=instance.id,
                                           ingredients_id__in=old_authors_set
                                           ).delete()
        IngredientsInRecipe.objects.bulk_create([
            IngredientsInRecipe(recipe_id=instance.id, **ba)
            for ba in new_authors_dict.values()
        ])
        IngredientsInRecipe.objects.bulk_update([
            IngredientsInRecipe(id=old_authors_dict[ba['ingredients'].id].id,
                                **ba) for ba in updated_authors_dict.values()
        ], fields=['amount'])

    def update_many2us(self, instance, validated_data):
        for field, updater_name in self.MANY_FIELDS.items():
            data = validated_data.pop(field, None)
            updater = getattr(self, updater_name)
            if data is not None or not self.partial:
                updater(instance, data or [])
        return instance

    def has_duplicates(self, ordered_dicts):
        seen = set()
        for od in ordered_dicts:
            od_tuple = tuple(od.items())
            if od_tuple in seen:
                return True
            seen.add(od_tuple)
        return False

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
        for i in field_names:
            if not (str(i) in validated_data):
                if str(i) == 'ingredients':
                    i = 'ingredients_recipes'
                elif str(i) == 'ingredients_recipes':
                    i = 'ingredients'
                if not (str(i) in validated_data):
                    raise serializers.ValidationError(
                        f"Рецепт должен иметь {str(i)}.")
        for i in (many2m.keys()):
            if not many2m[str(i)]:
                raise serializers.ValidationError(f"Рецепт должен"
                                                  f" иметь хотя бы "
                                                  f"1 {str(i)}.")
        if validated_data['image'] is None:
            raise serializers.ValidationError("Рецепт должен "
                                              "содержать фотографию.")

        if self.has_duplicates(many2m['ingredients_recipes']):
            raise serializers.ValidationError("В рецепте не должно"
                                              " быть повторяющихся"
                                              " ингредиетов.")
        elif len(many2m['tags']) != len(set(many2m['tags'])):
            raise serializers.ValidationError("В рецепте"
                                              " не должно быть"
                                              " повторяющихся тегов.")
        return basic, many2m

    def create(self, validated_data):
        basic, many2us = self.split_validated_data(validated_data)
        return self.update_many2us(super().create(basic), many2us)

    def update(self, instance, validated_data):
        basic, many2us = self.split_validated_data(validated_data)
        return self.update_many2us(super().update(instance, basic), many2us)


class RecipeShortSerializer(serializers.Serializer):
    id = PrimaryKeyRelatedField(queryset=Recipe.objects.all())
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
                  'avatar', ]

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


class ShortLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShortLink
        fields = ['id', 'original_url', 'short_url']


class ShortLinkSerializer11(serializers.ModelSerializer):
    short_url = serializers.CharField()

    class Meta:
        model = ShortLink
        fields = ['short_url']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['short-link'] = representation.pop('short_url')
        return representation
