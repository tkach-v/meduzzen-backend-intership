import csv

from django.http import HttpResponse
from rest_framework.response import Response

from quizz.serializers import ExportResultsSerializer


def export_results(results, file_type):
    serializer = ExportResultsSerializer(results, many=True)

    if file_type == "csv":
        response = HttpResponse(content_type='text/csv')
        fieldnames = ExportResultsSerializer.Meta.fields

        writer = csv.DictWriter(response, fieldnames=fieldnames)
        writer.writeheader()
        for row in serializer.data:
            writer.writerow(row)

    else:
        response = Response(serializer.data, content_type='application/json')

    response['Content-Disposition'] = f'attachment; filename="user_results.{file_type}"'
    return response
