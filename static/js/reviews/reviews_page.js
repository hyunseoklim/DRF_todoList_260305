/*
  ============================================================
  리뷰 목록 + 감정분석 UI 스크립트
  - DRF API(리뷰 목록/상세/감정분석)를 호출해서 화면에 표시
  - window.api (axios 인스턴스)가 base.html에서 로드되어 있어야 함
  ============================================================
*/
document.addEventListener("DOMContentLoaded", () => {

    // ============================================================
    // 0) 사전 체크: api.js 로드 확인
    // ============================================================
    // window.api는 보통 api.js에서 만들어둔 axios 인스턴스입니다.
    // (예: baseURL, Authorization 헤더, withCredentials 등 공통 설정)
    if (!window.api) {
        alert("설정 오류: api.js가 로드되지 않았습니다.");
        return;
    }

    // ============================================================
    // 1) 페이지 이동 버튼
    // ============================================================
    // 'Todo 목록' 페이지로 돌아가기
    document.getElementById("backToTodo").onclick = () => location.href = "/todo/list/";

    // ============================================================
    // 2) 상태(state) 변수
    // ============================================================
    // currentPage: 현재 페이지 번호 (페이지네이션)
    let currentPage = 1;

    // selected: 사용자가 클릭해서 선택한 리뷰(현재 선택 상태 저장)
    let selected = { id: null, title: "", review: "" };

    // ============================================================
    // 3) API 엔드포인트 (router.register 기준)
    // ============================================================
    // 목록 조회: GET /api/reviews/collected-reviews/?page=1
    const LIST_URL = (page) => `/api/reviews/collected-reviews/?page=${page}`;

    // 선택 리뷰 감정분석: GET /api/reviews/collected-reviews/{id}/sentiment/
    const SENTIMENT_BY_ID = (id) => `/api/reviews/collected-reviews/${id}/sentiment/`;

    // 텍스트 직접 감정분석: POST /api/reviews/collected-reviews/sentiment/
    const SENTIMENT_TEXT = `/api/reviews/collected-reviews/sentiment/`;

    // ============================================================
    // 4) DOM 요소 캐싱 (자주 쓰는 요소는 변수로 저장)
    // ============================================================
    const $list = document.getElementById("reviewsList");     // 리뷰 목록이 렌더링될 영역
    const $pageInfo = document.getElementById("pageInfo");    // "현재/전체" 페이지 표시 영역
    const $prev = document.getElementById("prevBtn");         // 이전 버튼
    const $next = document.getElementById("nextBtn");         // 다음 버튼

    const $selectedId = document.getElementById("selectedId");      // 선택된 리뷰 id 표시 영역
    const $selectedTitle = document.getElementById("selectedTitle");// 선택된 리뷰 제목 표시 영역
    const $inputText = document.getElementById("inputText");        // 분석할 텍스트 입력 textarea
    const $analyzeSelected = document.getElementById("analyzeSelected"); // 선택 리뷰 분석 버튼
    const $result = document.getElementById("resultArea");          // 감정 분석 결과 표시 영역

    // ✅ 비동기 시작
    const SENTIMENT_ASYNC_BY_ID = (id) => `/api/reviews/collected-reviews/${id}/sentiment-async/`;
    const SENTIMENT_ASYNC_TEXT = `/api/reviews/collected-reviews/sentiment-async/`;

    // ✅ 결과 조회
    const SENTIMENT_RESULT = (taskId) =>
        `/api/reviews/collected-reviews/sentiment-result/${taskId}/`;

    // ============================================================
    // 5) 결과 렌더링 함수
    // ============================================================
    // - id 기반 감정분석 응답은 { sentiment: {...} } 형태일 수 있고
    // - 텍스트 직접 감정분석 응답은 {...} 형태일 수 있어서
    //   payload.sentiment가 있으면 그것을 우선 사용합니다.
    function renderResult(payload) {
        const s = payload?.sentiment ?? payload; // id 기반이면 {sentiment:{...}} 형태

        if (!s) {
            $result.textContent = "결과 없음";
            return;
        }

        // label / score 추출 (서버 응답 키에 유연하게 대응)
        const label = s.label || s.label_raw || "unknown";
        const score = (typeof s.score === "number") ? s.score.toFixed(4) : "-";

        // NSMC 관례: LABEL_1 = positive, LABEL_0 = negative
        const isPos = (s.label === "positive" || s.label_raw === "LABEL_1");

        // 배지 UI 클래스/텍스트 결정
        const badgeClass = isPos ? "pos" : "neg";
        const badgeText = isPos ? "긍정" : "부정";

        // 결과를 HTML로 출력 (배지 + 부가정보)
        $result.innerHTML = `
      <div class="badge ${badgeClass}">
        <strong>${badgeText}</strong>
        <span class="muted">score: ${score}</span>
      </div>
      <div style="margin-top:10px;" class="muted">
        <div>model: <code>${s.model ?? "-"}</code></div>
        <div>label_raw: <code>${s.label_raw ?? "-"}</code></div>
      </div>
    `;
    }

    // ============================================================
    // 6) 리뷰 선택 처리 함수
    // ============================================================
    // - 목록에서 특정 리뷰를 클릭하면 선택 상태를 갱신하고
    // - 입력창에 리뷰 본문을 자동 채우며
    // - "선택 리뷰 분석" 버튼을 활성화합니다.
    function selectReview(itemEl, data) {

        // (1) 기존 active 표시 제거 후, 클릭된 항목에 active 추가
        [...document.querySelectorAll(".review-item")].forEach(el => el.classList.remove("active"));
        itemEl.classList.add("active");

        // (2) 선택 상태 업데이트
        selected = { id: data.id, title: data.title, review: data.review };

        // (3) 우측 패널 표시 업데이트
        $selectedId.textContent = String(selected.id);
        $selectedTitle.textContent = selected.title || "(제목 없음)";
        $inputText.value = selected.review || "";

        // (4) 분석 버튼 활성화
        $analyzeSelected.disabled = false;

        // (5) 안내 문구 출력
        $result.textContent = "선택 리뷰를 분석할 준비가 됐어요.";
    }

    // ============================================================
    // 7) 리뷰 목록 렌더링 함수
    // ============================================================
    function renderList(items) {
        $list.innerHTML = "";

        // 데이터가 없으면 안내 표시
        if (!items || items.length === 0) {
            $list.innerHTML = "<p class='muted'>리뷰가 없습니다.</p>";
            return;
        }

        // 각 리뷰를 카드 형태로 렌더링
        items.forEach(r => {
            const el = document.createElement("div");
            el.className = "review-item";

            // 본문 일부만 잘라서 스니펫으로 표시 (최대 120자)
            const snippet = (r.review || "").slice(0, 120);

            el.innerHTML = `
        <div style="display:flex; justify-content:space-between; gap:10px;">
          <strong>${r.title ?? "(제목 없음)"}</strong>
          <span class="muted"> 글번호 ${r.id}</span>
        </div>
        <div class="review-snippet">
          ${snippet}${(r.review || "").length > 120 ? "..." : ""}
        </div>
      `;

            // 클릭 시 선택 처리
            el.addEventListener("click", () => selectReview(el, r));

            $list.appendChild(el);
        });
    }

    // ============================================================
    // 8) 페이지네이션 표시 업데이트
    // ============================================================
    // 서버가 반환하는 형식에 따라 current_page/page_count/previous/next 를 사용
    function updatePagination(data) {
        const current = data.current_page ?? currentPage ?? 1;
        const total = data.page_count ?? "?";

        // 예: "1 / 10"
        $pageInfo.textContent = `${current} / ${total}`;

        // previous/next가 없으면 버튼 비활성화
        $prev.disabled = !data.previous;
        $next.disabled = !data.next;
    }

    // ============================================================
    // 9) 페이지 로드(목록 조회) 함수
    // ============================================================
    async function loadPage(page) {
        try {
            // GET 요청으로 목록 가져오기
            const res = await window.api.get(LIST_URL(page));
            const data = res.data;

            // 서버 응답이 {data:[...]} 또는 {results:[...]} 형태일 수 있으니 둘 다 대응
            renderList(data.data || data.results || []);

            // 페이지네이션 UI 갱신
            updatePagination(data);

            // currentPage 업데이트
            currentPage = data.current_page || page;

        } catch (err) {
            console.error("리뷰 목록 로드 실패", err.response?.data || err.message);
            alert("리뷰 목록 로드 실패");
        }
    }

    // ✅ task 완료까지 결과 조회(폴링)
    async function pollResult(taskId, { intervalMs = 800, timeoutMs = 30000 } = {}) {
        const start = Date.now();

        while (true) {
            const res = await window.api.get(SENTIMENT_RESULT(taskId));
            const data = res.data;

            if (data.state === "SUCCESS") return data.result;
            if (data.state === "FAILURE") throw new Error(data.error || "Task failed");

            if (Date.now() - start > timeoutMs) {
                throw new Error("분석 시간이 오래 걸려 타임아웃되었습니다.");
            }

            await new Promise((r) => setTimeout(r, intervalMs));
        }
    }

    // ============================================================
    // 10) 페이지 이동 버튼 이벤트
    // ============================================================
    $prev.onclick = () => {
        // 현재 페이지가 1보다 클 때만 이전 페이지 로드
        if (currentPage > 1) loadPage(currentPage - 1);
    };

    $next.onclick = () => {
        // 다음 페이지 로드 (서버에서 next가 없으면 disabled 처리됨)
        loadPage(currentPage + 1);
    };

    // ============================================================
    // 11) 선택 리뷰 감정 분석 버튼
    // ============================================================
    // const res = await window.api.get(SENTIMENT_BY_ID(selected.id));
    // renderResult(res.data);

    document.getElementById("analyzeSelected").onclick = async () => {
        if (!selected.id) return;

        try {
            $result.textContent = "분석 요청 중...";

            // ✅ 1) 비동기 작업 시작 (POST)
            const startRes = await window.api.post(SENTIMENT_ASYNC_BY_ID(selected.id));
            const taskId = startRes.data.task_id;

            $result.textContent = `분석 중... (task_id=${taskId})`;

            // ✅ 2) 결과 조회(폴링)
            const finalResult = await pollResult(taskId);

            // ✅ 3) 화면 표시
            renderResult(finalResult);

        } catch (err) {
            console.error("선택 리뷰 분석 실패", err.response?.data || err.message);
            alert(err.message || "선택 리뷰 분석 실패");
        }
    };

    // ============================================================
    // 12) 텍스트 직접 감정 분석 버튼
    // ============================================================
    document.getElementById("analyzeText").onclick = async () => {
        const text = $inputText.value.trim();

        // 입력이 없으면 안내
        if (!text) return alert("텍스트를 입력하세요.");

        try {
            $result.textContent = "분석 중...";

            // 입력 텍스트를 POST로 전달
            const res = await window.api.post(SENTIMENT_TEXT, { text });

            // 결과 렌더링
            renderResult(res.data);

        } catch (err) {
            console.error("텍스트 분석 실패", err.response?.data || err.message);
            alert("텍스트 분석 실패");
        }
    };

    // ============================================================
    // 13) 초기화 버튼: 선택 상태/입력/결과 UI 초기화
    // ============================================================
    document.getElementById("clearBtn").onclick = () => {
        // 선택 상태 초기화
        selected = { id: null, title: "", review: "" };

        // UI 초기화
        $selectedId.textContent = "없음";
        $selectedTitle.textContent = "리뷰를 선택하세요";
        $inputText.value = "";
        $analyzeSelected.disabled = true;
        $result.textContent = "결과가 여기에 표시됩니다.";

        // 목록 active 표시 제거
        [...document.querySelectorAll(".review-item")].forEach(el => el.classList.remove("active"));
    };

    // ============================================================
    // 14) 페이지 최초 진입 시 1페이지 로드
    // ============================================================
    loadPage(1);
});
