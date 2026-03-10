from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Todo(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    complete = models.BooleanField(default=False)
    exp = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to="todo_images/", blank=True, null=True)

    is_public = models.BooleanField(default=True)

    # user 추가
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="todos", null=True, blank=True
    )

    def __str__(self):
        return self.name

    # 모델의 save() 메서드를 오버라이딩
    # → Todo가 저장될 때 complete 상태에 따라 completed_at을 자동으로 관리
    def save(self, *args, **kwargs):

        # 완료 상태(True)인데 완료 시간이 없는 경우
        # → 현재 시간을 완료 시간으로 자동 저장
        if self.complete and self.completed_at is None:
            self.completed_at = timezone.now()

        # 완료 상태(False)인데 완료 시간이 이미 있는 경우
        # → 완료 취소로 판단하고 완료 시간을 제거
        if not self.complete and self.completed_at is not None:
            self.completed_at = None

        # 부모 모델(Model)의 원래 save() 실행 (DB에 실제 저장)
        super().save(*args, **kwargs)
