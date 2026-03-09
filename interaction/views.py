# DRF APIView 사용
# 클래스 기반 API를 만들 때 사용
from rest_framework.views import APIView

# API 응답을 JSON 형태로 반환하기 위한 클래스
from rest_framework.response import Response

# 로그인한 사용자만 접근하도록 제한하는 권한 클래스
from rest_framework.permissions import IsAuthenticated

# 객체가 없을 경우 자동으로 404 반환
from django.shortcuts import get_object_or_404


# Todo 모델 import
from todo.models import Todo

# 좋아요 / 북마크 / 댓글 모델 import
from .models import TodoLike, TodoBookmark, TodoComment

# 댓글 serializer import
from .serializers import TodoCommentSerializer


# =========================================================
# 좋아요 토글 API
# POST /interaction/like/<todo_id>/
# =========================================================
class TodoLikeToggleAPIView(APIView):

    # 로그인한 사용자만 접근 가능
    permission_classes = [IsAuthenticated]

    def post(self, request, todo_id):

        # 해당 todo_id에 해당하는 Todo 객체 가져오기
        # 없으면 자동으로 404 반환
        todo = get_object_or_404(Todo, id=todo_id)

        # 좋아요 객체 생성 또는 조회
        # 이미 좋아요가 있으면 기존 객체 반환
        # 없으면 새로 생성
        obj, created = TodoLike.objects.get_or_create(todo=todo, user=request.user)

        # 이미 좋아요가 존재했던 경우
        if not created:

            # 좋아요 취소 (삭제)
            obj.delete()
            liked = False

        else:
            # 좋아요 새로 생성됨
            liked = True

        # 현재 Todo의 전체 좋아요 개수 계산
        count = TodoLike.objects.filter(todo=todo).count()

        # JSON 응답 반환
        return Response(
            {"liked": liked, "like_count": count}  # 현재 좋아요 상태  # 총 좋아요 수
        )


# =========================================================
# 북마크 토글 API
# POST /interaction/bookmark/<todo_id>/
# =========================================================
class TodoBookmarkToggleAPIView(APIView):

    # 로그인 사용자만 접근 가능
    permission_classes = [IsAuthenticated]

    def post(self, request, todo_id):

        # Todo 객체 조회
        todo = get_object_or_404(Todo, id=todo_id)

        # 북마크 생성 또는 조회
        obj, created = TodoBookmark.objects.get_or_create(todo=todo, user=request.user)

        # 이미 북마크가 존재하면
        if not created:

            # 북마크 취소 (삭제)
            obj.delete()
            bookmarked = False

        else:
            # 새 북마크 생성
            bookmarked = True

        # 현재 Todo의 북마크 개수 계산
        count = TodoBookmark.objects.filter(todo=todo).count()

        # JSON 응답 반환
        return Response(
            {
                "bookmarked": bookmarked,  # 현재 북마크 상태
                "bookmark_count": count,  # 전체 북마크 수
            }
        )


# =========================================================
# 댓글 등록 API
# POST /interaction/comment/<todo_id>/
# =========================================================
class TodoCommentCreateAPIView(APIView):

    # 로그인 사용자만 댓글 작성 가능
    permission_classes = [IsAuthenticated]

    def post(self, request, todo_id):

        # 댓글이 달릴 Todo 객체 조회
        todo = get_object_or_404(Todo, id=todo_id)

        # 요청 데이터에서 content 값 가져오기
        # strip() → 앞뒤 공백 제거
        content = request.data.get("content", "").strip()

        # 댓글 내용이 없는 경우
        if not content:

            # 오류 메시지 반환
            return Response({"detail": "내용이 필요합니다."}, status=400)

        # 댓글 생성
        comment = TodoComment.objects.create(
            todo=todo,  # 어떤 Todo에 달렸는지
            user=request.user,  # 작성자
            content=content,  # 댓글 내용
        )

        # 생성된 댓글을 serializer로 변환
        serializer = TodoCommentSerializer(comment)

        # JSON 응답 반환
        return Response(serializer.data)


# =========================================================
# 댓글 목록 조회 API
# GET /interaction/comment/<todo_id>/
# =========================================================
class TodoCommentListAPIView(APIView):

    def get(self, request, todo_id):

        # Todo 객체 조회
        todo = get_object_or_404(Todo, id=todo_id)

        # 해당 Todo의 댓글 목록 조회
        # 최신 댓글이 먼저 나오도록 정렬
        comments = TodoComment.objects.filter(todo=todo).order_by("-created_at")

        # 댓글 목록을 serializer로 변환
        serializer = TodoCommentSerializer(
            comments, many=True  # 여러 개 객체이기 때문에 many=True
        )

        # JSON 응답 반환
        return Response(serializer.data)
