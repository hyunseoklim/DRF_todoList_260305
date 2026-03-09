from django.urls import path
from .views import (
    TodoLikeToggleAPIView,
    TodoBookmarkToggleAPIView,
    TodoCommentCreateAPIView,
    TodoCommentListAPIView,
)

urlpatterns = [
    path("like/<int:todo_id>/", TodoLikeToggleAPIView.as_view()),
    path("bookmark/<int:todo_id>/", TodoBookmarkToggleAPIView.as_view()),
    path("comment/<int:todo_id>/", TodoCommentCreateAPIView.as_view()),
    path("comment/<int:todo_id>/list/", TodoCommentListAPIView.as_view()),
]
