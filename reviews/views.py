from django.shortcuts import render

# Django REST Framework의 ViewSet 기능 import
# → 여러 API 기능(list, retrieve 등)을 하나의 클래스에서 처리할 수 있음
from rest_framework import viewsets, status

# API 접근 권한 설정 클래스 import
# → 인증된 사용자만 수정 가능, 비로그인 사용자는 읽기만 가능
from rest_framework.permissions import IsAuthenticatedOrReadOnly

# ViewSet에 추가 API endpoint(action)를 만들기 위한 데코레이터
from rest_framework.decorators import action

# HTTP 응답 객체
from rest_framework.response import Response

# 현재 앱의 모델과 Serializer import
from .models import CollectedReview
from .serializers import CollectedReviewSerializer, SentimentTextSerializer

# HuggingFace 감정 분석 함수
from .services import predict_sentiment

# 인증 없이 접근 가능하도록 하는 권한 클래스
from rest_framework.permissions import AllowAny

from celery.result import AsyncResult
from .tasks import analyze_review_sentiment_by_id, analyze_sentiment_text


# ============================================================
# CollectedReview 데이터 조회용 API ViewSet
# ============================================================
class CollectedReviewViewSet(viewsets.ReadOnlyModelViewSet):
    """
    데이터 확인용 API ViewSet

    ReadOnlyModelViewSet
    → 읽기 전용 ViewSet
    → 아래 API만 자동 생성됨

    GET /reviews/        : 리뷰 목록 조회 (list)
    GET /reviews/{id}/   : 리뷰 상세 조회 (retrieve)
    """

    # ------------------------------------------------------------
    # 조회할 데이터(QuerySet) 설정
    # ------------------------------------------------------------
    # DB에서 CollectedReview 데이터를 모두 가져오고
    # id 기준 내림차순 정렬 (최신 데이터 먼저)
    queryset = CollectedReview.objects.all().order_by("-doc_id")

    # ------------------------------------------------------------
    # 사용할 Serializer 지정
    # ------------------------------------------------------------
    # 모델 데이터를 JSON 형태로 변환할 때 사용
    serializer_class = CollectedReviewSerializer

    # ------------------------------------------------------------
    # API 접근 권한 설정
    # ------------------------------------------------------------
    # IsAuthenticatedOrReadOnly 의미
    #
    # 비로그인 사용자
    #   → GET 요청만 가능 (조회)
    #
    # 로그인 사용자
    #   → GET / POST / PUT / DELETE 가능
    #
    # 하지만 현재 ViewSet이 ReadOnlyModelViewSet이므로
    # 실제로는 GET 요청(list, retrieve)만 제공됨
    permission_classes = [IsAuthenticatedOrReadOnly]

    # ============================================================
    # 1️⃣ DB 리뷰 감정 분석 API
    # ============================================================
    @action(detail=True, methods=["get"], url_path="sentiment")
    def sentiment(self, request, pk=None):
        """
        GET /reviews/{id}/sentiment/

        DB에 저장된 review 텍스트를 가져와
        HuggingFace 모델로 감정 분석 수행
        """

        # URL의 id에 해당하는 리뷰 객체 조회
        obj = self.get_object()

        # 리뷰 텍스트가 없는 경우 에러 반환
        if not obj.review:
            return Response(
                {"detail": "review text is empty"}, status=status.HTTP_400_BAD_REQUEST
            )

        # 감정 분석 수행
        pred = predict_sentiment(obj.review)

        # 결과 반환
        return Response(
            {
                "id": obj.id,  # 리뷰 ID
                "title": obj.title,  # 리뷰 제목
                "sentiment": pred,  # 감정 분석 결과
            },
            status=status.HTTP_200_OK,
        )

    # ============================================================
    # 2️⃣ 텍스트 직접 감정 분석 API
    # ============================================================
    @action(
        detail=False,  # 특정 id 필요 없음
        methods=["post"],  # POST 요청
        url_path="sentiment",  # URL 경로
        permission_classes=[AllowAny],  # 로그인 없이 접근 가능
    )
    def sentiment_text(self, request):
        """
        POST /reviews/sentiment/

        요청 body 예시
        {
            "text": "이 영화 정말 재미있다"
        }

        사용자가 직접 텍스트를 보내면
        해당 텍스트에 대해 감정 분석 수행
        """

        # 입력 데이터 검증
        serializer = SentimentTextSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 검증된 텍스트 추출
        text = serializer.validated_data["text"]

        # 감정 분석 수행
        pred = predict_sentiment(text)

        # 결과 반환
        return Response(pred, status=status.HTTP_200_OK)

    # ---------------------------------------------------------
    # ✅ (추가 1) DB 리뷰 비동기 분석 시작: job_id 즉시 반환
    # POST /api/reviews/collected-reviews/{id}/sentiment-async/
    # ---------------------------------------------------------
    @action(detail=True, methods=["post"], url_path="sentiment-async")
    def sentiment_async(self, request, pk=None):
        review_id = int(pk)
        task = analyze_review_sentiment_by_id.delay(review_id)

        return Response(
            {"task_id": task.id, "status": "queued"}, status=status.HTTP_202_ACCEPTED
        )

    # ---------------------------------------------------------
    # ✅ (추가 2) 텍스트 비동기 분석 시작
    # POST /api/reviews/collected-reviews/sentiment-async/
    # body: {"text": "..."}
    # ---------------------------------------------------------
    @action(detail=False, methods=["post"], url_path="sentiment-async")
    def sentiment_text_async(self, request):
        serializer = SentimentTextSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        text = serializer.validated_data["text"]
        task = analyze_sentiment_text.delay(text)

        return Response(
            {"task_id": task.id, "status": "queued"}, status=status.HTTP_202_ACCEPTED
        )

    # ---------------------------------------------------------
    # ✅ (추가 3) 결과 조회
    # GET /api/reviews/collected-reviews/sentiment-result/{task_id}/
    # ---------------------------------------------------------
    @action(
        detail=False, methods=["get"], url_path=r"sentiment-result/(?P<task_id>[^/.]+)"
    )
    def sentiment_result(self, request, task_id=None):
        res = AsyncResult(task_id)

        payload = {"task_id": task_id, "state": res.state}

        if res.state == "PENDING":
            return Response(payload, status=status.HTTP_200_OK)

        if res.state == "FAILURE":
            payload["error"] = str(res.result)
            return Response(payload, status=status.HTTP_200_OK)

        if res.state == "SUCCESS":
            payload["result"] = res.result
            return Response(payload, status=status.HTTP_200_OK)

        return Response(payload, status=status.HTTP_200_OK)


# 독립적인 함수 생성
def reviews_page(request):
    return render(request, "reviews/reviews_page.html")
