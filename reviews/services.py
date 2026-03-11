# ============================================================
# reviews/services.py
# HuggingFace Transformers 기반 감정 분석 서비스
# ============================================================

# 운영체제 환경 변수 설정을 위해 os 모듈 import
import os

# HuggingFace Transformers의 pipeline 기능 import
# → 텍스트 분류, 번역, 요약 등 다양한 NLP 작업을 간단하게 수행 가능
from transformers import pipeline


# ============================================================
# tokenizer 병렬 처리 경고 비활성화
# ============================================================

# TOKENIZERS_PARALLELISM
# → tokenizer가 멀티스레드로 실행될 때 발생하는 경고 메시지를 비활성화
# → 실제 서비스 환경에서 불필요한 로그를 줄이기 위해 설정
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


# ============================================================
# 사용할 감정 분석 모델 지정
# ============================================================

# HuggingFace Hub에 올라와 있는 한국어 감정 분석 모델
# → NSMC (네이버 영화 리뷰 데이터셋) 기반 파인튜닝 모델
MODEL_NAME = "blockenters/finetuned-nsmc-sentiment"


# ============================================================
# 전역 pipeline 객체 (모델 캐싱용)
# ============================================================

# pipeline을 매번 새로 생성하면
# → 모델 로딩 시간이 매우 오래 걸림
# → 따라서 최초 1회만 로딩 후 재사용
_pipe = None


# ============================================================
# 감정 분석 pipeline 로드 함수
# ============================================================


def get_sentiment_pipe():
    """
    감정 분석 pipeline을 생성하거나
    이미 생성된 pipeline을 반환하는 함수
    """

    global _pipe

    # pipeline이 아직 생성되지 않았으면
    if _pipe is None:

        # HuggingFace pipeline 생성
        # task: sentiment-analysis (감정 분석)
        _pipe = pipeline(
            "sentiment-analysis",
            model=MODEL_NAME,
            tokenizer=MODEL_NAME,
        )

    # 이미 생성된 pipeline 재사용
    return _pipe


# ============================================================
# 모델 라벨을 사람이 이해하기 쉬운 형태로 변환
# ============================================================


def normalize_label(label_raw: str) -> str:
    """
    HuggingFace 모델이 반환하는 LABEL 값을
    사람이 이해하기 쉬운 값으로 변환

    일반적인 NSMC 모델 convention
    LABEL_1 → positive
    LABEL_0 → negative
    """

    if label_raw == "LABEL_1":
        return "positive"

    if label_raw == "LABEL_0":
        return "negative"

    # 예외 상황에서는 원래 값 그대로 반환
    return label_raw


# ============================================================
# 감정 분석 예측 함수
# ============================================================


def predict_sentiment(text: str) -> dict:
    """
    입력 텍스트(text)에 대해 감정 분석 수행

    반환 값:
    {
        "model": 모델 이름
        "label_raw": 모델 원래 출력
        "label": 정규화된 감정 결과
        "score": 예측 확률
    }
    """

    # 감정 분석 pipeline 가져오기
    pipe = get_sentiment_pipe()

    # --------------------------------------------------------
    # 모델 추론
    # --------------------------------------------------------
    # truncation=True
    # → 입력 문장이 너무 길 경우 잘라서 처리
    #
    # max_length=512
    # → BERT 기반 모델의 최대 토큰 길이 제한
    #
    # [0]
    # → pipeline 결과는 리스트로 반환되므로 첫 번째 결과 사용
    result = pipe(text, truncation=True, max_length=512)[0]

    # --------------------------------------------------------
    # 결과 값 추출
    # --------------------------------------------------------

    # 모델이 반환한 원본 라벨 (예: LABEL_1)
    label_raw = result.get("label")

    # 예측 확률 (confidence score)
    score = float(result.get("score", 0.0))

    # --------------------------------------------------------
    # 최종 결과 반환
    # --------------------------------------------------------

    return {
        "model": MODEL_NAME,  # 사용한 모델 이름
        "label_raw": label_raw,  # 모델 원본 라벨
        "label": normalize_label(label_raw),  # 사람이 이해하기 쉬운 라벨
        "score": score,  # 감정 예측 확률
    }
