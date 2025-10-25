import validators
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from analysis.tasks import run_full_analysis_task


class AnalysisTriggerView(APIView):
    def post(self, request):
        url = request.data.get("url")
        if not url:
            return Response(
                {"error": "URL é obrigatorio"}, status=status.HTTP_400_BAD_REQUEST
            )
        if not validators.url(url):
            return Response(
                {"error": "Campo URL é obrigatorio"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            task_result = run_full_analysis_task.delay(url)
            print(f"Task {task_result.id} iniciada para a URL: {url}")

        except Exception as e:
            print(f"Erro ao inciar a Task Celery: {e}")
            return Response(
                {"error": "Falha ao iniciar a Analise"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "message": "Analise iniciada em Backgroud",
                "task_id": task_result.id,
                "status_endpoint": f"/analysis/status/{task_result.id}",
            },
            status=status.HTTP_202_ACCEPTED,
        )
