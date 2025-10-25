from celery.result import AsyncResult
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView


class AnalysisStatusView(APIView):
    throttle_classes = [AnonRateThrottle]

    def get(self, request, task_id):
        task = AsyncResult(task_id)

        if not task:
            return Response(
                {"error": "Task não encontrada"}, status=status.HTTP_404_NOT_FOUND
            )

        state = task.state
        response_data = {"state": state}

        if state == "STARTED":
            response_data["status"] = "Em processamento..."

        elif state == "PENDING":
            response_data["status"] = "Aguardando na Fila..."

        elif state == "FAILURE":
            response_data["status"] = "Falha na execução..."
            response_data["error"] = str(task.result)
            print(f"Task {task.id} falhou: {task.result}")

        elif state == "SUCCESS":
            response_data["status"] = "Concluido"
            response_data["result"] = task.result

        return Response(response_data, status=status.HTTP_200_OK)
