import csv
from enum import Enum

from django.http import HttpResponse
from rest_framework.response import Response

from quizz.serializers import ExportResultsSerializer


class FileType(Enum):
    CSV = 'csv'
    JSON = 'json'


def export_results(results, file_type):
    serializer = ExportResultsSerializer(results, many=True)

    if file_type == FileType.CSV.value:
        response = HttpResponse(content_type='text/csv')
        fieldnames = ExportResultsSerializer.Meta.fields

        writer = csv.DictWriter(response, fieldnames=fieldnames)
        writer.writeheader()
        for row in serializer.data:
            writer.writerow(row)
    elif file_type == FileType.JSON.value:
        response = Response(serializer.data, content_type='application/json')

    response['Content-Disposition'] = f'attachment; filename="user_results.{file_type}"'
    return response
