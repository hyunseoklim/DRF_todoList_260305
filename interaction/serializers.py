# DRF Serializer 사용
# 모델 데이터를 JSON으로 변환하거나
# JSON 데이터를 모델 객체로 변환할 때 사용
from rest_framework import serializers

# 현재 앱의 모델 import
from .models import TodoLike, TodoBookmark, TodoComment


# ============================================
# Todo 좋아요 Serializer
# ============================================
class TodoLikeSerializer(serializers.ModelSerializer):

    # ModelSerializer
    # → Django 모델을 기반으로 자동 필드 생성
    class Meta:

        # 어떤 모델을 사용할지 지정
        model = TodoLike

        # 모델의 모든 필드를 serializer에 포함
        # user, todo, created_at 등
        fields = "__all__"


# ============================================
# Todo 북마크 Serializer
# ============================================
class TodoBookmarkSerializer(serializers.ModelSerializer):

    class Meta:

        # TodoBookmark 모델을 기반으로 직렬화
        model = TodoBookmark

        # 모델의 모든 필드 포함
        fields = "__all__"


# ============================================
# Todo 댓글 Serializer
# ============================================
class TodoCommentSerializer(serializers.ModelSerializer):

    # username 필드를 추가
    # source="user.username"
    # → user 모델의 username 값을 가져옴
    # read_only=True
    # → 클라이언트가 수정할 수 없음 (조회용)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:

        # TodoComment 모델 기반
        model = TodoComment

        # API에서 사용할 필드 목록
        fields = [
            "id",  # 댓글 id
            "todo",  # 어떤 Todo에 달린 댓글인지
            "user",  # 댓글 작성자
            "username",  # 작성자 username (추가 필드)
            "content",  # 댓글 내용
            "created_at",  # 작성 시간
        ]

        # 읽기 전용 필드
        # user는 보통 request.user로 서버에서 자동 설정
        read_only_fields = ["user"]
