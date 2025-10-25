from django.urls import path

from analysis.view import AnalysisStatusView, AnalysisTriggerView

urlpatterns = [
    path("analysis/", AnalysisTriggerView.as_view(), name="analysis-trigger"),
    path(
        "analysis/status/<int:task_id>",
        AnalysisStatusView.as_view(),
        name="analysis-status",
    ),
]
