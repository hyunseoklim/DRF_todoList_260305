# Django 설정에서 AUTH_USER_MODEL 가져오기
# 기본 User 모델 또는 커스텀 User 모델을 참조하기 위해 사용
from django.conf import settings

# Django ORM 모델 클래스 사용
from django.db import models


# ============================================
# Todo 좋아요 모델
# ============================================
class TodoLike(models.Model):

    # 좋아요를 누른 사용자
    # settings.AUTH_USER_MODEL → 현재 프로젝트에서 사용하는 User 모델
    # on_delete=models.CASCADE
    # → 사용자가 삭제되면 좋아요도 함께 삭제
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # 좋아요 대상 Todo
    # "todo.Todo" → todo 앱의 Todo 모델을 문자열로 참조
    # related_name="likes"
    # → Todo 객체에서 todo.likes 로 접근 가능
    # 예: todo.likes.all()
    todo = models.ForeignKey(
        "todo.Todo",  # 기존 todo 앱 모델 참조
        on_delete=models.CASCADE,
        related_name="likes",
    )

    # 좋아요 생성 시간
    # auto_now_add=True
    # → 생성될 때 자동으로 현재 시간이 저장됨
    created_at = models.DateTimeField(auto_now_add=True)

    # 모델 추가 옵션 설정
    class Meta:

        # 동일한 user + todo 조합은 한 번만 허용
        # 즉 한 사용자가 같은 Todo에 여러 번 좋아요 못 누르게 함
        unique_together = ("user", "todo")


# ============================================
# Todo 북마크 모델
# ============================================
class TodoBookmark(models.Model):

    # 북마크를 등록한 사용자
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # 북마크 대상 Todo
    # related_name="bookmarks"
    # → todo.bookmarks 로 접근 가능
    # 예: todo.bookmarks.count()
    todo = models.ForeignKey(
        "todo.Todo", on_delete=models.CASCADE, related_name="bookmarks"
    )

    # 북마크 생성 시간
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:

        # 동일 사용자 + Todo 조합 중복 방지
        # 같은 Todo를 여러 번 북마크 못하도록 제한
        unique_together = ("user", "todo")


# ============================================
# Todo 댓글 모델
# ============================================
class TodoComment(models.Model):

    # 댓글 작성 사용자
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # 댓글이 달린 Todo
    # related_name="comments"
    # → todo.comments 로 접근 가능
    # 예: todo.comments.all()
    todo = models.ForeignKey(
        "todo.Todo", on_delete=models.CASCADE, related_name="comments"
    )

    # 댓글 내용
    # TextField → 긴 문자열 저장 가능
    content = models.TextField()

    # 댓글 작성 시간
    created_at = models.DateTimeField(auto_now_add=True)
