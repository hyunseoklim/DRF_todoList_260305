# Celery 작업(Task)을 만들기 위한 데코레이터
# shared_task는 Django 앱 어디서든 사용할 수 있는 Celery 작업을 정의할 때 사용
from celery import shared_task

# Django ORM에서 객체가 없을 때 발생하는 예외
from django.core.exceptions import ObjectDoesNotExist

# 리뷰 모델 (DB에서 리뷰 데이터를 가져오기 위해 사용)
from .models import CollectedReview

# 실제 AI 감정분석 로직이 들어있는 서비스 함수
from .services import predict_sentiment


# ============================================================
# 1️⃣ 리뷰 ID 기반 감정분석 Celery Task
# ============================================================
# bind=True
# → Celery task 내부에서 self 접근 가능 (retry, request 정보 등 사용 가능)
@shared_task(bind=True)
def analyze_review_sentiment_by_id(self, review_id: int) -> dict:
    """
    DB에 있는 리뷰(id)를 가져와서
    services의 AI 로직으로 감정분석 후 결과 반환하는 Celery Task
    """

    # --------------------------------------------------------
    # 1) DB에서 리뷰 객체 조회
    # --------------------------------------------------------
    try:
        obj = CollectedReview.objects.get(id=review_id)

    # 해당 ID 리뷰가 존재하지 않을 경우
    except ObjectDoesNotExist:
        return {"status": "error", "detail": "review not found", "review_id": review_id}

    # --------------------------------------------------------
    # 2) 리뷰 텍스트 가져오기
    # --------------------------------------------------------
    # None일 가능성이 있으므로 기본값 "" 처리
    # strip() → 앞뒤 공백 제거
    text = (obj.review or "").strip()

    # 텍스트가 비어있는 경우
    if not text:
        return {
            "status": "error",
            "detail": "review text is empty",
            "review_id": review_id,
        }

    # --------------------------------------------------------
    # 3) AI 감정 분석 수행
    # --------------------------------------------------------
    # HuggingFace 모델을 이용한 sentiment 분석
    pred = predict_sentiment(text)

    # --------------------------------------------------------
    # 4) 결과 반환
    # --------------------------------------------------------
    # Celery Task 결과는 dict 형태로 반환 가능
    return {
        "status": "ok",
        "review_id": obj.id,
        "title": obj.title,
        "sentiment": pred,  # 감정 분석 결과
    }


# ============================================================
# 2️⃣ 텍스트 직접 감정분석 Celery Task
# ============================================================
@shared_task(bind=True)
def analyze_sentiment_text(self, text: str) -> dict:
    """
    사용자가 입력한 텍스트를 직접 받아 감정분석 수행하는 Celery Task
    """

    # --------------------------------------------------------
    # 1) 텍스트 전처리
    # --------------------------------------------------------
    # None일 수 있으므로 기본값 "" 처리 후 공백 제거
    text = (text or "").strip()

    # 텍스트가 비어있는 경우 에러 반환
    if not text:
        return {"status": "error", "detail": "text is empty"}

    # --------------------------------------------------------
    # 2) AI 감정 분석 수행
    # --------------------------------------------------------
    pred = predict_sentiment(text)

    # --------------------------------------------------------
    # 3) 결과 반환
    # --------------------------------------------------------
    return {"status": "ok", "sentiment": pred}
