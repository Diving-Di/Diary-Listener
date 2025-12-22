import json
from django.db import transaction

from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from .models import Image, Tag, User
from .serializers import ImageSerializer, TagSerializer, UserSerializer
from .ai import generate_ai_tags

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        # 使用事务确保注册过程原子性
        # 如果在创建用户后发生任何异常，数据库将自动回滚，
        # 从而避免"注册失败但数据残留"的情况。
        return super().create(request, *args, **kwargs)

class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all().order_by('-created')
    serializer_class = ImageSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated:
            qs = Image.objects.filter(user=user).order_by('-created')
        else:
            qs = Image.objects.none()
        tag_id = self.request.query_params.get('tag_id')
        tag = self.request.query_params.get('tag')

        if tag_id:
            try:
                qs = qs.filter(tags__id=int(tag_id))
            except Exception:
                pass
        if tag:
            qs = qs.filter(tags__tag_name__icontains=tag.strip())

        return qs.distinct()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def ai_tag(self, request, pk=None):
        """Generate AI tags for one image and attach them.

        Response includes tags and updated image.
        """

        image_obj = self.get_object()

        # Ensure we can access the stored file
        image_path = getattr(getattr(image_obj, 'image', None), 'path', None)
        if not image_path:
            return Response({'detail': 'image file not found'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tags = generate_ai_tags(image_path)
        except Exception as e:
            msg = str(e) or 'AI tagging failed'
            if 'not set' in msg.lower() or 'unsupported ai_tagging_provider' in msg.lower():
                return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'detail': msg}, status=status.HTTP_502_BAD_GATEWAY)

        # Persist json field
        try:
            image_obj.ai_tags_json = json.dumps(tags, ensure_ascii=False)
        except Exception:
            image_obj.ai_tags_json = None

        tag_objs = []
        for name in tags:
            existing = Tag.objects.filter(tag_name=name, tag_type='AI', user=request.user).first()
            if existing:
                tag_objs.append(existing)
            else:
                tag_objs.append(Tag.objects.create(tag_name=name, tag_type='AI', user=request.user))

        if tag_objs:
            image_obj.tags.add(*tag_objs)

        image_obj.save(update_fields=['ai_tags_json'])

        serializer = self.get_serializer(image_obj)
        return Response({'ai_tags': tags, 'image': serializer.data}, status=status.HTTP_200_OK)

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Tag.objects.all()
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated:
            return qs.filter(user=user)
        return qs.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
