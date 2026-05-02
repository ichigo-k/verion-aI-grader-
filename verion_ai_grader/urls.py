"""
URL configuration for verion_ai_grader project.
"""

from django.urls import include, path

urlpatterns = [
    path('', include('grader.urls')),
]
