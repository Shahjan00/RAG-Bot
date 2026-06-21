from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import DocumentUploadSerializer


class DocumentUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save()

        return Response(
            {
                "message": "Document uploaded successfully.",
                "document_id": document.id,
                "business_id": document.business_id,
                "title": document.title,
            },
            status=status.HTTP_201_CREATED,
        )
