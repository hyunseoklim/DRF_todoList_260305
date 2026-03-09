// ======================================================
// Todo List 페이지 전용 JS
// - 목록 조회
// - 좋아요/북마크/댓글(조회/등록)
// - 페이지네이션
// ======================================================

document.addEventListener("DOMContentLoaded", () => {
    // ======================================================
    // 0) 기본 설정 / 상태값
    // ======================================================
    const LOGIN_PAGE_URL = "/login/";
    const LIST_API_URL = "/todo/viewsets/view/"; // GET: 목록, POST: 생성(여긴 목록만 사용)
    const PAGE_SIZE = 3; // ⚠️ 백엔드 pagination page_size와 동일해야 total 계산이 정확함

    // 현재 페이지 상태값
    let currentPage = 1;

    // ======================================================
    // 0-1) window.api(axios 인스턴스) 존재 확인
    // - base.html에서 api.js가 먼저 로드되어야 함
    // ======================================================
    if (!window.api) {
        console.error("window.api가 없습니다. base.html에서 static/js/api.js 로드 확인");
        alert("설정 오류: api.js가 로드되지 않았습니다.");
        return;
    }

    // ======================================================
    // 0-2) access_token 확인 (없으면 로그인 페이지로)
    // - 토큰이 있는데 만료된 경우는 401/403 처리에서 이동됨
    // ======================================================
    const access = localStorage.getItem("access_token");
    if (!access) {
        console.log("access_token 없음 → 로그인 이동");
        window.location.href = LOGIN_PAGE_URL;
        return;
    }

    // ======================================================
    // 1) 공통 헬퍼
    // ======================================================

    // 인증 실패(401/403) → 토큰 삭제 후 로그인 이동
    function handleAuthError(err) {
        const status = err.response?.status;
        if (status === 401 || status === 403) {
            console.log("인증 실패(401/403) → 토큰 삭제 후 로그인 이동");
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
            window.location.href = LOGIN_PAGE_URL;
        }
        // 호출한 쪽에서 이어서 catch 할 수 있게 reject 반환
        return Promise.reject(err);
    }

    // 숫자 안전 변환 (NaN 방지)
    function toNumber(v, fallback = 0) {
        const n = Number(v);
        return Number.isFinite(n) ? n : fallback;
    }

    // interaction API 경로 헬퍼
    const InteractionAPI = {
        like: (todoId) => `/interaction/like/${todoId}/`,
        bookmark: (todoId) => `/interaction/bookmark/${todoId}/`,
        comment: (todoId) => `/interaction/comment/${todoId}/`,
        commentList: (todoId) => `/interaction/comment/${todoId}/list/`,
    };

    // ======================================================
    // 2) 데이터 로딩 함수 (Read)
    // ======================================================

    // 특정 페이지의 Todo 목록을 서버에서 가져와 렌더링한다.
    async function loadPage(page) {
        try {
            const res = await window.api.get(`${LIST_API_URL}?page=${page}`);
            const data = res.data;

            // 서버 응답 형태가 data 또는 results일 수 있으니 둘 다 대응
            const todos = data.data || data.results || [];

            renderTodos(todos);
            updatePaginationUI(data);

            // 서버가 current_page를 내려주면 그걸 우선 사용
            currentPage = data.current_page || page;
        } catch (err) {
            handleAuthError(err).catch(() => { });
            console.error("페이지 로드 실패", err.response?.data || err.message);
        }
    }

    // 특정 todoId의 댓글 목록을 서버에서 가져와 카드에 표시한다.
    async function loadComments(todoId, card) {
        const listEl = card.querySelector(".comment-list");
        if (!listEl) return;

        try {
            const res = await window.api.get(InteractionAPI.commentList(todoId));
            const comments = res.data || [];

            listEl.innerHTML = "";
            comments.forEach((c) => {
                const item = document.createElement("div");
                item.className = "comment-item";
                item.style.padding = "6px 0";
                item.innerHTML = `
          <div style="font-size:14px;">
            <strong>${c.username ?? ""}</strong> : ${c.content ?? ""}
          </div>
        `;
                listEl.appendChild(item);
            });
        } catch (err) {
            handleAuthError(err).catch(() => { });
            console.error("댓글 목록 로드 실패", err.response?.data || err.message);
        }
    }

    // ======================================================
    // 3) 렌더링 함수 (UI)
    // ======================================================

    // 목록 렌더링 (서버에서 받은 todos 배열을 DOM으로 그린다)
    function renderTodos(todos) {
        const container = document.querySelector(".list_container");
        container.innerHTML = "";

        if (!todos || todos.length === 0) {
            container.innerHTML = "<p>등록된 Todo 없음</p>";
            return;
        }

        todos.forEach((todo) => {
            const card = document.createElement("div");
            card.className = "todo-item";
            card.dataset.id = todo.id;

            // 이미지 URL 처리
            const imageSrc = todo.image
                ? (todo.image.startsWith("http") ? todo.image : `${location.origin}${todo.image}`)
                : "";

            // 카운트/상태 값 안전 처리
            const likeCount = toNumber(todo.like_count, 0);
            const bookmarkCount = toNumber(todo.bookmark_count, 0);
            const commentCount = toNumber(todo.comment_count, 0);

            const isLiked = Boolean(todo.is_liked ?? false);
            const isBookmarked = Boolean(todo.is_bookmarked ?? false);

            // 카드 내부 HTML 구성
            card.innerHTML = `
        <p><strong>제목:</strong> ${todo.name ?? ""}</p>
        <p><strong>설명:</strong> ${todo.description ?? ""}</p>
        <p><strong>작성자:</strong> ${todo.username ?? ""}</p>
        <p><strong>완료 여부:</strong> ${todo.complete ? "완료" : "미완료"}</p>
        <p><strong>exp:</strong> ${toNumber(todo.exp, 0)}</p>

        ${imageSrc ? `<img src="${imageSrc}" style="max-width:200px;">` : ""}

        <div class="todo-actions" style="display:flex; gap:10px; align-items:center; margin-top:10px;">
          <button class="btn-like" type="button"
            data-id="${todo.id}" aria-pressed="${isLiked}"
            style="display:flex; gap:6px; align-items:center; border-radius:999px; padding:6px 10px;">
            <span class="icon">${isLiked ? "❤️" : "🤍"}</span>
            <span class="count">${likeCount}</span>
          </button>

          <button class="btn-bookmark" type="button"
            data-id="${todo.id}" aria-pressed="${isBookmarked}"
            style="display:flex; gap:6px; align-items:center; border-radius:999px; padding:6px 10px;">
            <span class="icon">${isBookmarked ? "🔖" : "📑"}</span>
            <span class="count">${bookmarkCount}</span>
          </button>

          <button class="btn-comment" type="button"
            data-id="${todo.id}"
            style="display:flex; gap:6px; align-items:center; border-radius:999px; padding:6px 10px;">
            <span class="icon">💬</span>
            <span class="count">${commentCount}</span>
          </button>
        </div>

        <div class="comment-box" style="display:none; margin-top:10px;">
          <textarea class="comment-text" rows="3" style="width:100%;"></textarea>
          <button class="comment-submit" data-id="${todo.id}">등록</button>
        </div>

        <div class="comment-list" style="margin-top:8px;"></div>
      `;

            // 카드 클릭 시 detail 이동 (단, 버튼 영역 클릭은 제외)
            card.addEventListener("click", (e) => {
                if (e.target.closest(".todo-actions") || e.target.closest(".comment-box")) return;
                window.location.href = `/todo/detail/${todo.id}/`;
            });

            container.appendChild(card);

            // 카드가 DOM에 붙은 뒤 댓글 목록 로딩
            loadComments(todo.id, card);
        });
    }

    // 페이지네이션 UI 갱신
    function updatePaginationUI(data) {
        // 현재 페이지는 서버 값(current_page)이 있으면 우선
        const current = data.current_page ?? currentPage ?? 1;

        // total 계산 우선순위:
        // 1) 서버가 page_count(총 페이지)를 내려주면 그걸 사용
        // 2) 아니면 count / PAGE_SIZE 로 계산
        const total =
            typeof data.page_count === "number"
                ? data.page_count
                : (typeof data.count === "number"
                    ? Math.max(1, Math.ceil(data.count / PAGE_SIZE))
                    : "?");

        // 화면 표시
        document.getElementById("pageInfo").innerText = `${current} / ${total}`;

        // next/previous 값으로 버튼 활성/비활성
        document.getElementById("prevBtn").disabled = !data.previous;
        document.getElementById("nextBtn").disabled = !data.next;
    }

    // ======================================================
    // 4) 이벤트 처리 (이벤트 위임)
    // - 카드가 동적으로 렌더링되므로 document 단에서 처리
    // ======================================================
    document.addEventListener("click", async (e) => {
        // (1) 좋아요 버튼
        const likeBtn = e.target.closest(".btn-like");
        if (likeBtn) {
            e.stopPropagation();
            e.preventDefault();

            const todoId = likeBtn.dataset.id;
            try {
                const res = await window.api.post(InteractionAPI.like(todoId));
                const { liked, like_count } = res.data;

                likeBtn.setAttribute("aria-pressed", String(liked));
                likeBtn.querySelector(".icon").textContent = liked ? "❤️" : "🤍";
                likeBtn.querySelector(".count").textContent = toNumber(like_count, 0);
            } catch (err) {
                handleAuthError(err).catch(() => { });
                console.error("좋아요 실패:", err.response?.data || err.message);
                alert("좋아요 실패");
            }
            return;
        }

        // (2) 북마크 버튼
        const bookmarkBtn = e.target.closest(".btn-bookmark");
        if (bookmarkBtn) {
            e.stopPropagation();
            e.preventDefault();

            const todoId = bookmarkBtn.dataset.id;
            try {
                const res = await window.api.post(InteractionAPI.bookmark(todoId));
                const { bookmarked, bookmark_count } = res.data;

                bookmarkBtn.setAttribute("aria-pressed", String(bookmarked));
                bookmarkBtn.querySelector(".icon").textContent = bookmarked ? "🔖" : "📑";
                bookmarkBtn.querySelector(".count").textContent = toNumber(bookmark_count, 0);
            } catch (err) {
                handleAuthError(err).catch(() => { });
                console.error("북마크 실패:", err.response?.data || err.message);
                alert("북마크 실패");
            }
            return;
        }

        // (3) 댓글 버튼 → 입력 박스 토글
        const commentBtn = e.target.closest(".btn-comment");
        if (commentBtn) {
            e.stopPropagation();
            e.preventDefault();

            const card = commentBtn.closest(".todo-item");
            const box = card.querySelector(".comment-box");

            box.style.display = (box.style.display === "none" || !box.style.display) ? "block" : "none";
            return;
        }

        // (4) 댓글 등록 버튼
        const submitBtn = e.target.closest(".comment-submit");
        if (submitBtn) {
            e.stopPropagation();
            e.preventDefault();

            const todoId = submitBtn.dataset.id;
            const card = submitBtn.closest(".todo-item");
            const textarea = card.querySelector(".comment-text");
            const content = textarea.value.trim();

            if (!content) return;

            try {
                const res = await window.api.post(InteractionAPI.comment(todoId), { content });
                const saved = res.data;

                const listEl = card.querySelector(".comment-list");

                // 화면에 즉시 댓글 추가
                const item = document.createElement("div");
                item.className = "comment-item";
                item.style.padding = "6px 0";
                item.innerHTML = `
          <div style="font-size:14px;">
            <strong>${saved.username ?? "me"}</strong> : ${saved.content}
          </div>
        `;
                listEl.prepend(item);

                // 댓글 수 +1 (UI만 증가)
                const countEl = card.querySelector(".btn-comment .count");
                countEl.textContent = toNumber(countEl.textContent, 0) + 1;

                // 입력 초기화
                textarea.value = "";

                // 입력창 유지
                card.querySelector(".comment-box").style.display = "block";
            } catch (err) {
                handleAuthError(err).catch(() => { });
                console.error("댓글 등록 실패", err.response?.data || err.message);
                alert("댓글 등록 실패");
            }
            return;
        }
    });

    // ======================================================
    // 4-2) 페이지 이동 버튼(고정 DOM)
    // ======================================================
    document.getElementById("prevBtn").addEventListener("click", () => {
        if (currentPage > 1) loadPage(currentPage - 1);
    });

    document.getElementById("nextBtn").addEventListener("click", () => {
        loadPage(currentPage + 1);
    });

    // ======================================================
    // 4-3) 기타 버튼
    // ======================================================
    document.getElementById("createBtn").addEventListener("click", () => {
        window.location.href = "/todo/create/";
    });

    document.getElementById("movieReviewsBtn").addEventListener("click", () => {
        window.location.href = "/reviews/page/";
    });

    // ======================================================
    // 5) 초기 실행
    // ======================================================
    loadPage(1);
});
