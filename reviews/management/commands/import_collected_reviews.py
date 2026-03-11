# ============================================================
# CSV / JSONL 파일로 저장된 "수집 리뷰 데이터"를
# Django ORM(CollectedReview 모델)을 통해 DB에 적재하는 커맨드
# ============================================================

import csv  # CSV 파일을 dict 형태로 읽기 위해 사용
import json  # JSONL(한 줄당 JSON) 파싱을 위해 사용
import hashlib  # doc_id 생성(내용 기반 해시)용
from pathlib import Path  # 파일 경로 처리 (OS 독립적)
from datetime import datetime  # 날짜 문자열을 datetime으로 변환할 때 사용

from django.core.management.base import (
    BaseCommand,
    CommandError,
)  # 커맨드 생성/에러 처리
from django.utils.dateparse import parse_datetime  # ISO datetime 문자열 파싱 도우미

from reviews.models import CollectedReview  # DB에 저장할 Django 모델


# ============================================================
# 1) pick 함수: 컬럼명이 서로 다른 데이터에 대응하기 위한 유틸
# ============================================================
def pick(d: dict, candidates: list[str], default=None):
    """
    여러 후보 키(candidates) 중에서
    실제 dict(d)에 존재하고 값이 비어있지 않은 첫 번째 값을 반환합니다.

    예)
      r = {"title": "abc", "review": "내용"}
      pick(r, ["name", "title", "subject"]) => "abc"
    """
    for k in candidates:
        # 값이 None 또는 ""(빈문자열)이면 없는 값으로 취급하고 넘어감
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default


# ============================================================
# 2) doc_id 생성 함수: doc_id가 없을 때 "내용 기반" 임시 ID 생성
# ============================================================
def make_doc_id(name: str, description: str, source: str = "") -> str:
    """
    doc_id가 파일에 없거나 비어있을 때 사용하는 임시 doc_id 생성기입니다.
    - source + name + description 을 합쳐서 해시를 만들기 때문에
      같은 내용이면 같은 doc_id가 생성될 확률이 높습니다.
    - sha256 해시 문자열을 만들고, 앞 32자리만 잘라 사용합니다.
    """
    raw = f"{source}||{name}||{description}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


# ============================================================
# 3) Django Management Command 본체
#    실행 예)
#    python manage.py import_collected_reviews --path data.csv --source naver
# ============================================================
class Command(BaseCommand):
    help = "Import collected reviews from CSV or JSONL into DB."

    # ------------------------------------------------------------
    # 커맨드 옵션 설정
    # ------------------------------------------------------------
    def add_arguments(self, parser):
        # --path : 입력 파일 경로 (필수)
        parser.add_argument("--path", required=True, help="data file path (csv/jsonl)")

        # --source : 데이터 출처 메타 정보 (옵션)
        parser.add_argument(
            "--source", default="", help="source name e.g. naver/musinsa"
        )

        # --limit : 테스트용으로 일부 행만 적재하고 싶을 때 사용 (0이면 전체)
        parser.add_argument(
            "--limit", type=int, default=0, help="limit rows for test (0=all)"
        )

        # --batch : bulk_create를 몇 개 단위로 끊어서 넣을지(성능/메모리 조절)
        parser.add_argument(
            "--batch", type=int, default=1000, help="bulk_create batch size"
        )

    # ------------------------------------------------------------
    # 커맨드가 실제로 실행되는 메인 로직
    # ------------------------------------------------------------
    def handle(self, *args, **options):
        # 옵션 값 꺼내기
        path = Path(options["path"])  # 파일 경로
        source = options["source"].strip()  # 출처 문자열(공백 제거)
        limit = options["limit"]  # 적재 제한
        batch_size = options["batch"]  # 배치 크기

        # 파일 존재 여부 체크
        if not path.exists():
            raise CommandError(f"File not found: {path}")

        # 확장자 검사 (csv 또는 jsonl만 허용)
        suffix = path.suffix.lower()
        if suffix not in [".csv", ".jsonl"]:
            raise CommandError("Only .csv or .jsonl is supported")

        # --------------------------------------------------------
        # (1) 파일 읽기
        # --------------------------------------------------------
        if suffix == ".csv":
            rows = self._read_csv(path, limit=limit)
        else:
            rows = self._read_jsonl(path, limit=limit)

        total = len(rows)
        self.stdout.write(self.style.NOTICE(f"Loaded {total} rows from {path.name}"))

        # --------------------------------------------------------
        # (2) 각 row(dict)를 CollectedReview 객체로 변환
        # --------------------------------------------------------
        to_create = []

        for r in rows:
            # ---- 컬럼 매핑(데이터마다 키 이름이 다를 수 있어서 후보 키를 둠) ----
            # 제목 후보: name / title / subject
            name = pick(r, ["name", "title", "subject"], default="(no title)")

            # 본문 후보: description / text / content / review
            description = pick(
                r, ["description", "text", "content", "review"], default=""
            )

            # doc_id 후보: doc_id / id / document_id / uuid
            doc_id = pick(r, ["doc_id", "id", "document_id", "uuid"], default=None)

            # doc_id가 없으면 내용 기반 해시로 생성(중복 방지용)
            if not doc_id:
                doc_id = make_doc_id(name, description, source=source)

            # 수집 시간 후보: collected_at / created_at / date / datetime
            collected_at_raw = pick(
                r, ["collected_at", "created_at", "date", "datetime"], default=None
            )

            collected_at = None

            if collected_at_raw:
                # 문자열이라면 datetime 파싱 시도
                if isinstance(collected_at_raw, str):
                    # 1차: Django parse_datetime (ISO-8601 형태에 강함)
                    collected_at = parse_datetime(collected_at_raw)

                    # 2차: parse_datetime 실패 시, python 표준 fromisoformat 시도
                    if collected_at is None:
                        try:
                            collected_at = datetime.fromisoformat(collected_at_raw)
                        except Exception:
                            collected_at = None

            # ----------------------------------------------------
            # Django 모델 객체 생성 (아직 DB 저장 X)
            # ----------------------------------------------------
            # ⚠️ 주의:
            # CollectedReview 모델 필드명이
            # name/description/source 인지,
            # title/review/doc_id/collected_at 인지
            # 실제 models.py와 반드시 일치해야 합니다.
            obj = CollectedReview(
                doc_id=str(doc_id),
                name=str(name)[:255],  # 제목 길이 제한(255)
                description=str(description),  # 본문
                source=source,  # 출처
                collected_at=collected_at,  # 수집 시간
            )
            to_create.append(obj)

        # --------------------------------------------------------
        # (3) DB 적재 (bulk_create)
        # --------------------------------------------------------
        # bulk_create는 한 번에 여러 row를 insert해서 성능이 좋습니다.
        # batch_size로 끊어 넣으면 메모리 부담을 줄일 수 있습니다.
        created_count = 0

        for i in range(0, len(to_create), batch_size):
            chunk = to_create[i : i + batch_size]

            # ignore_conflicts=True:
            # - UNIQUE 제약조건(예: doc_id UNIQUE)에 걸리는 데이터는 자동 스킵
            # - 즉 "중복 doc_id"는 insert되지 않고 넘어갑니다.
            CollectedReview.objects.bulk_create(
                chunk, ignore_conflicts=True, batch_size=batch_size
            )

            created_count += len(chunk)
            self.stdout.write(f"Inserted batch: {i} ~ {i + len(chunk) - 1}")

        self.stdout.write(
            self.style.SUCCESS("Done. (Duplicates skipped by doc_id unique)")
        )

    # ============================================================
    # CSV 파일 읽기 함수
    # ============================================================
    def _read_csv(self, path: Path, limit: int = 0) -> list[dict]:
        """
        CSV 파일을 DictReader로 읽어서
        각 행을 dict로 만든 뒤 list로 반환합니다.

        encoding="utf-8-sig":
        - 윈도우/엑셀에서 저장한 CSV에 BOM이 붙어도 깨지지 않도록 처리
        """
        data = []
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)

            for idx, row in enumerate(reader):
                data.append(row)

                # limit이 0이 아니면 해당 개수만큼만 읽고 종료
                if limit and (idx + 1) >= limit:
                    break

        return data

    # ============================================================
    # JSONL 파일 읽기 함수
    # ============================================================
    def _read_jsonl(self, path: Path, limit: int = 0) -> list[dict]:
        """
        JSONL 파일은 한 줄(line)마다 JSON 객체가 있는 형태입니다.
        예)
          {"title":"a","review":"..."}
          {"title":"b","review":"..."}

        각 줄을 json.loads로 dict로 변환 후 list로 반환합니다.
        """
        data = []
        with path.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                line = line.strip()

                # 빈 줄은 스킵
                if not line:
                    continue

                data.append(json.loads(line))

                # limit이 0이 아니면 해당 개수만큼만 읽고 종료
                if limit and (idx + 1) >= limit:
                    break

        return data
