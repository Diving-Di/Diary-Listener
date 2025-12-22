import json
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from urllib.parse import urlparse
from .models import User, Image, Tag


def _normalize_tag_names(values):
    result = []
    if not values:
        return result
    for raw in values:
        s = ('' if raw is None else str(raw)).strip()
        if not s:
            continue
        compact = ''.join(s.split())
        if compact in ('[]', '[""]'):
            continue
        if s.startswith('[') and s.endswith(']'):
            try:
                parsed = json.loads(s)
            except Exception:
                parsed = None
            if isinstance(parsed, list):
                for x in parsed:
                    t = ('' if x is None else str(x)).strip()
                    if not t:
                        continue
                    compact_t = ''.join(t.split())
                    if compact_t in ('[]', '[""]'):
                        continue
                    if t not in result:
                        result.append(t)
                continue

        if s not in result:
            result.append(s)
    return result


class FlexibleStringListField(serializers.ListField):
    """Accepts list input, JSON array string, or comma-separated string."""

    def to_internal_value(self, data):
        if data is None:
            return []
        if isinstance(data, str):
            s = data.strip()
            if not s:
                return []
            try:
                parsed = json.loads(s)
            except Exception:
                parsed = None
            if isinstance(parsed, list):
                data = parsed
            else:
                data = [t.strip() for t in s.split(',') if t.strip()]
        return super().to_internal_value(data)

class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

    def validate_username(self, value):
        # 用户名至少 6 个字符
        if value is None:
            raise serializers.ValidationError('用户名不能为空')
        if len(str(value)) < 6:
            raise serializers.ValidationError('用户名长度需至少 6 个字符')
        return value

    def validate_password(self, value):
        # 密码至少 6 个字符
        if value is None:
            raise serializers.ValidationError('密码不能为空')
        if len(str(value)) < 6:
            raise serializers.ValidationError('密码长度需至少 6 个字符')
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

class ImageSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, write_only=True, source='tags', required=False
    )
    tag_names = FlexibleStringListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
    )
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Image
        fields = '__all__'

    def to_representation(self, instance):
        """Return relative media paths so clients (e.g. phones) don't try to load 127.0.0.1 URLs.

        When the frontend hits the API via Vite dev proxy, DRF may build absolute URLs
        like http://127.0.0.1:8000/media/... which are not reachable from mobile devices.
        Converting to relative paths lets the browser request /media/... from the same host.
        """
        rep = super().to_representation(instance)
        for key in ('image', 'thumbnail'):
            v = rep.get(key)
            if isinstance(v, str) and v.startswith(('http://', 'https://')):
                try:
                    rep[key] = urlparse(v).path or v
                except Exception:
                    pass
        return rep

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        user = getattr(request, 'user', None) if request else None
        if user and getattr(user, 'is_authenticated', False):
            # 只允许选择自己的标签，避免把别人的标签挂到自己的图片上
            try:
                self.fields['tag_ids'].queryset = Tag.objects.filter(user=user)
            except Exception:
                pass

    def create(self, validated_data):
        request = self.context.get('request')
        user = validated_data.get('user') or (getattr(request, 'user', None) if request else None)

        tag_objs = validated_data.pop('tags', [])
        tag_names = validated_data.pop('tag_names', [])

        image = Image.objects.create(**validated_data)

        if tag_objs:
            image.tags.add(*tag_objs)

        if tag_names and user and getattr(user, 'is_authenticated', False):
            cleaned = _normalize_tag_names(tag_names)

            tags_to_add = []
            for name in cleaned:
                existing = Tag.objects.filter(tag_name=name, tag_type='Custom', user=user).first()
                if existing:
                    tags_to_add.append(existing)
                else:
                    tags_to_add.append(Tag.objects.create(tag_name=name, tag_type='Custom', user=user))
            if tags_to_add:
                image.tags.add(*tags_to_add)

        return image

    def update(self, instance, validated_data):
        request = self.context.get('request')
        user = getattr(request, 'user', None) if request else None

        # tag_ids 写入到 source='tags'
        tag_objs = validated_data.pop('tags', None)
        tag_names = validated_data.pop('tag_names', None)

        instance = super().update(instance, validated_data)

        # tag_ids：仍按“增加”处理
        if tag_objs:
            instance.tags.add(*tag_objs)

        # tag_names：按“编辑自定义标签”处理，同时保留 EXIF 等非自定义标签
        if tag_names is not None and user and getattr(user, 'is_authenticated', False):
            cleaned = _normalize_tag_names(tag_names)

            desired_custom = []
            for name in cleaned:
                existing = Tag.objects.filter(tag_name=name, tag_type='Custom', user=user).first()
                if existing:
                    desired_custom.append(existing)
                else:
                    desired_custom.append(Tag.objects.create(tag_name=name, tag_type='Custom', user=user))

            keep = list(instance.tags.exclude(tag_type='Custom', user=user))
            instance.tags.set(keep + desired_custom)

        return instance
