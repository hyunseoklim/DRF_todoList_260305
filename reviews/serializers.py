# Django REST Framework의 serializer 모듈 import
# → API에서 데이터를 변환(직렬화/역직렬화)할 때 사용
from rest_framework import serializers

# 현재 앱의 CollectedReview 모델 import
# → DB 테이블(stg_movie_reviews)에 매핑된 모델
from .models import CollectedReview


# ============================================================
# CollectedReview 데이터를 API용으로 변환하는 Serializer
# ============================================================
class CollectedReviewSerializer(serializers.ModelSerializer):

    # ------------------------------------------------------------
    # Serializer 설정 클래스
    # ------------------------------------------------------------
    class Meta:

        # 어떤 Django 모델을 기반으로 Serializer를 만들지 지정
        model = CollectedReview

        # API에서 사용할 필드 목록 지정
        # → 모델의 필드 중 아래 항목만 JSON으로 변환됨
        fields = [
            "doc_id",  # DB 기본 키 (Primary Key)
            "title",  # 리뷰 제목
            "review",  # 리뷰 본문
            "doc_id",  # 중복 방지용 문서 ID
            "collected_at",  # 데이터 수집 시각
        ]


# ============================================================
# 2️⃣ 감정 분석 API 입력 검증용 Serializer
# ============================================================
class SentimentTextSerializer(serializers.Serializer):
    """
    감정 분석 API에서 사용자가 직접 텍스트를 POST로 보낼 때
    입력 데이터 검증(validation)을 수행하는 Serializer

    예시 요청

    POST /api/sentiment/

    {
        "text": "이 영화 정말 재미있다"
    }
    """

    # ------------------------------------------------------------
    # 분석할 텍스트 필드
    # ------------------------------------------------------------
    text = serializers.CharField(
        # 빈 문자열 허용 여부
        # False → 반드시 내용이 있어야 함
        allow_blank=False,
        # 최대 길이 제한
        # 너무 긴 텍스트 입력 방지 (서버 보호 목적)
        max_length=5000,
    )
