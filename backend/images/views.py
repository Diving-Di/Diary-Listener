from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Image, Tag, User
from .serializers import ImageSerializer, TagSerializer, UserSerializer

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

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
