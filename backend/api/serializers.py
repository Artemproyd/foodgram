from rest_framework import serializers
from users.models import User, Subscription
from .models import Tag, Ingredient, IngredientsInRecipe, Recipe, TagRecipe
from .validators import username_validator, validate_name
from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile
import base64
from rest_framework.fields import SerializerMethodField
from rest_framework.relations import SlugRelatedField, PrimaryKeyRelatedField, StringRelatedField
from rest_framework.serializers import CharField, ModelSerializer


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)
    # avatar_url = serializers.SerializerMethodField(
    #     'get_image_url',
    #     read_only=True,
    # )

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
            # 'avatar_url'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(user=request.user, subscribed_to=obj).exists()
        return False


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['avatar',]


class TagSerializer(serializers.ModelSerializer):
    id = serializers.CharField()

    class Meta:
        model = Tag
        fields = [
            'id',
            'slug',
            'name',
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
    id = SlugRelatedField("id", source="ingredients", queryset=Ingredient.objects.all())
    # name = serializers.SlugRelatedField("name", source="ingredients", queryset=Ingredient.objects.all())
    # measurement_unit = serializers.SlugRelatedField("name", source="ingredients", queryset=Ingredient.objects.all())
    # # id = serializers.CharField()
    # amount = serializers.IntegerField()
    # id = serializers.ReadOnlyField(source="ingredient.id")

    class Meta:
        model = IngredientsInRecipe
        fields = ['id', 'amount']


class TagsRecipe(serializers.ModelSerializer):
    id = SlugRelatedField("id", source="ingredients", queryset=Ingredient.objects.all())

    class Meta:
        model = TagRecipe
        fields = ['id']


class ReadSerializer(serializers.Serializer):
    id = PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    ingredients = IngredientsInRecipeSerializer(source='ingredients_recipes', many=True)
    tags = SlugRelatedField("name", many=True, read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    text = CharField()
    author = UserSerializer(default=serializers.CurrentUserDefault)
    # ingredients = IngredientsInRecipeSerializer(many=True, source='recipe', required=False)
    # tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), required=False)
    # image = Base64ImageField(required=False, allow_null=True)
    # amount = IngredientsInRecipeSerializer(
    #     many=True, read_only=True
    # )

    # def to_representation(self, instance):
    #     # print("kkkkkkkkkkkkkkkkkkkkkkkk")
    #     # print(instance)
    #     # ingredients_ = IngredientsInRecipe.objects.filter(recipe=Recipe.objects.get(id=instance['id']))
    #     # ing = []
    #     # for i in ingredients_:
    #     #     print(i.ingredients)
    #     #     ing.append(IngredientsInRecipeSerializer(i).data)
    #     # print(ing)
    #     # instance['ingredients'] = ing
    #     # print(instance)
    #     return instance

    class Meta:
        fields = [
            'id',
            'author',
            'name',
            'ingredients',
            'tags',
            'image',
            'text',
            'cooking_time',
        ]


class RecipeSerializer(serializers.ModelSerializer):

    ingredients = IngredientsInRecipeSerializer(source='ingredients_recipes', many=True)
    tags = PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    image = Base64ImageField(required=False, allow_null=True)
    author = UserSerializer(default=serializers.CurrentUserDefault)

    MANY_FIELDS = {'ingredients_recipes': 'update_authors',
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
            'cooking_time',
            'author',
        ]


    @classmethod
    def tags_update(cls, instance, data):
        old_tags_ids = set(instance.tags.values_list('id', flat=True))
        new_tags_ids = set([a.id for a in data])
        TagRecipe.objects.filter(recipe_id=instance.id, tag_id__in=old_tags_ids - new_tags_ids).delete()
        TagRecipe.objects.bulk_create([
            TagRecipe(recipe_id=instance.id, tag_id=tag_id) for tag_id in new_tags_ids - old_tags_ids
        ])

    @classmethod
    def update_authors(cls, instance, new_authors):
        print("kkkkkkkkkkkkkkkk")
        old_authors_dict = {ba.ingredients_id: ba for ba in instance.ingredients_recipes.all()}
        new_authors_dict = {ba['ingredients'].id: ba for ba in new_authors if ba['ingredients'].id not in old_authors_dict}
        updated_authors_dict = {ba['ingredients'].id: ba for ba in new_authors if ba['ingredients'].id in old_authors_dict}
        old_authors_set = set(old_authors_dict.keys()) - set(updated_authors_dict.keys())
        updated_authors_dict = dict(filter(
            lambda kv: kv[1]['amount'] != old_authors_dict[kv[0]].amount
                       and (kv[1]['amount'] is not None or old_authors_dict[kv[0]].amount is not None),
            updated_authors_dict.items()
        ))
        IngredientsInRecipe.objects.filter(recipe_id=instance.id, ingredients_id__in=old_authors_set).delete()
        IngredientsInRecipe.objects.bulk_create([
            IngredientsInRecipe(recipe_id=instance.id, **ba) for ba in new_authors_dict.values()
        ])
        IngredientsInRecipe.objects.bulk_update([
            IngredientsInRecipe(id=old_authors_dict[ba['ingredients'].id].id, **ba) for ba in updated_authors_dict.values()
        ], fields=['amount'])
        print("ppppppppppppppppppppppp")

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
            key: validated_data[key] for key in self.MANY_FIELDS if key in validated_data
        }
        field_names = list(self.fields.keys())
        for i in field_names:
            if not (str(i) in validated_data):
                raise serializers.ValidationError(f"Рецепт должен иметь {str(i)}.")

        for i in (many2m.keys()):
            if not many2m[str(i)]:
                raise serializers.ValidationError(f"Рецепт должен иметь хотя бы 1 {str(i)}.")

        if self.has_duplicates(many2m['ingredients_recipes']):
            raise serializers.ValidationError("В рецепте не должно быть повторяющихся ингредиетов.")
        elif len(many2m['tags']) != len(set(many2m['tags'])):
            raise serializers.ValidationError("В рецепте не должно быть повторяющихся тегов.")
        return basic, many2m

    def create(self, validated_data):
        print(validated_data)
        basic, many2us = self.split_validated_data(validated_data)
        return self.update_many2us(super().create(basic), many2us)

    def update(self, instance, validated_data):
        basic, many2us = self.split_validated_data(validated_data)
        return self.update_many2us(super().update(instance, basic), many2us)

    # def create(self, validate_data):
    #     print("yyyyyyyyyyyyyy")
    #     print(validate_data)
    #     ingredients = validate_data.pop('ingredients')
    #     print(validate_data)
    #     # tags = validate_data.pop('tags')
    #     recipe_objects = Recipe.objects.create(**validate_data)
    #     # recipe_objects.tags.set(tags)
    #     # a = []
    #     for i in ingredients:
    #         print(i.get('id'))
    #         # a.append(i.get('ingredient').get('id'))
    #     a = IngredientsInRecipe.objects.bulk_create(
    #         IngredientsInRecipe(
    #             recipe=recipe_objects,
    #             ingredients=i.get('id'),
    #             amount=i.get('amount'),
    #         ) for i in ingredients
    #     )
    #     b = []
    #     for i in a:
    #         b.append(i.id)
    #     recipe_objects.tags.set(b)
    #     print(recipe_objects.ingredients)
    #     print("xxxxxxxxxxxxxxxxxxx")
    #     return recipe_objects
    #
    # def update(self, instance, validated_data):
    #     for attr in validated_data:
    #         setattr(instance, attr, validated_data[attr])
    #     instance.save()
    #     return instance

    # def to_representation(self, instance):
    #     print(type(instance))
    #     read_serializer = ReadSerializer(instance, context=self.context)
    #     if read_serializer.is_valid():
    #         return read_serializer.to_representation(instance)
    #     return super().to_representation(instance)

    #
    # def _create_ingredients(self, recipe, ingredients_data):
    #     print("oooooooooooooooooooo")
    #     print(recipe)
    #     print(self)
    #     print(ingredients_data)
    #     print("oooooooooooooooooooo")
