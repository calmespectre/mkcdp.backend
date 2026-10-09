from django.db.models import Q
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Publication
from .serializers import PublicationSerializer, PublicationCreateSerializer


def _is_superuser(request):
    return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class PublicationListView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        qs = Publication.objects.all()
        if not _is_superuser(request):
            qs = qs.filter(published=True)

        category = request.query_params.get("category")
        year = request.query_params.get("year")
        q = (request.query_params.get("q") or "").strip()

        if category and category != "all":
            qs = qs.filter(category=category)
        if year and year != "all":
            try:
                qs = qs.filter(year=int(year))
            except ValueError:
                pass
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

        serializer = PublicationSerializer(qs, many=True, context={"request": request})
        return Response(
            {
                "results": serializer.data,
                "count": qs.count(),
                "categories": [
                    {"id": c[0], "label": c[1]} for c in Publication.CATEGORY_CHOICES
                ],
                "years": list(
                    Publication.objects.filter(published=True)
                    .exclude(year__isnull=True)
                    .values_list("year", flat=True)
                    .distinct()
                    .order_by("-year")
                ),
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        if not _is_superuser(request):
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)

        serializer = PublicationCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        publication = serializer.save()

        return Response(
            PublicationSerializer(publication, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class PublicationDetailView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self, pk):
        try:
            return Publication.objects.get(pk=pk)
        except Publication.DoesNotExist:
            return None

    def get(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        if not obj.published and not _is_superuser(request):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(PublicationSerializer(obj, context={"request": request}).data)

    def patch(self, request, pk):
        if not _is_superuser(request):
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
        obj = self.get_object(pk)
        if not obj:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = PublicationCreateSerializer(
            obj, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(PublicationSerializer(obj, context={"request": request}).data)

    def delete(self, request, pk):
        if not _is_superuser(request):
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
        obj = self.get_object(pk)
        if not obj:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            obj.file.delete(save=False)
        except Exception:
            pass
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)