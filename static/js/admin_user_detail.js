(async () => {
    // URL 파라미터에서 ID 추출
    const getQueryParam = (name) => {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(name);
    };

    const targetUserId = getQueryParam('id');

    // ID가 없으면 돌아가기
    if (!targetUserId) {
        alert('잘못된 접근입니다.');
        window.location.href = '/admin.html';
        return;
    }

    // 관리자 권한 체크
    if (!hasValidTokens()) {
        window.location.href = '/login';
        return;
    }

    let currentUserInfo;
    try {
        currentUserInfo = await getUserInfo();
    } catch (error) {
        console.error('Failed to get user info:', error);
        window.location.href = '/login';
        return;
    }

    if (!currentUserInfo || currentUserInfo.auth_level < 9) {
        alert('접근 권한이 없습니다.');
        window.location.href = '/hotdeal.html';
        return;
    }

    // 상단 닉네임 표시
    const nicknameEl = document.getElementById('user-nickname');
    if (nicknameEl) {
        nicknameEl.textContent = currentUserInfo.nickname;
    }

    // 로그아웃 버튼 이벤트
    document.getElementById('logout-button')?.addEventListener('click', () => {
        if (confirm('정말로 로그아웃하시겠습니까?')) {
            logout();
        }
    });

    // 사용자 상세 정보 로드
    await loadUserDetail(targetUserId);

    async function loadUserDetail(id) {
        try {
            const response = await fetchWithAuth(`/admin/users/${id}`);
            if (!response.ok) {
                throw new Error(`Failed to fetch user details: ${response.status}`);
            }
            const user = await response.json();
            renderUser(user);
        } catch (error) {
            console.error('Error loading user details:', error);
            alert('사용자 정보를 불러오는데 실패했습니다.');
            window.location.href = '/admin.html';
        }
    }

    function renderUser(user) {
        // 기본 정보 렌더링
        setText('user-id', user.id);
        setText('user-email', user.email);
        setText('user-nickname-display', user.nickname);
        
        const roleText = user.auth_level >= 9 ? '관리자' : '일반 사용자';
        setText('user-role', roleText);

        const lastLogin = user.last_login 
            ? new Date(user.last_login).toLocaleString('ko-KR') 
            : '-';
        setText('user-last-login', lastLogin);

        // 상태 표시 (admin.html 스타일 참고)
        const statusEl = document.getElementById('user-status');
        if (statusEl) {
            if (user.is_active) {
                statusEl.innerHTML = '<span class="status-badge status-admin">활성 (승인됨)</span>';
            } else {
                statusEl.innerHTML = '<span class="status-badge status-user">비활성 (미승인)</span>';
            }
        }

        // 키워드 목록 렌더링
        const tbody = document.querySelector('#user-keywords-table tbody');
        tbody.innerHTML = '';
        
        if (!user.keywords || user.keywords.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">등록된 키워드가 없습니다.</td></tr>';
            return;
        }

        user.keywords.forEach(kw => {
            const tr = document.createElement('tr');
            const date = kw.wdate ? new Date(kw.wdate).toLocaleDateString() : '-';
            // sites가 배열이거나 문자열일 수 있음
            let sites = '전체';
            if (Array.isArray(kw.sites) && kw.sites.length > 0) {
                sites = kw.sites.join(', ');
            } else if (typeof kw.sites === 'string') {
                sites = kw.sites;
            }

            tr.innerHTML = `
                <td>${kw.id}</td>
                <td>${kw.title || kw.keyword}</td>
                <td>${sites}</td>
                <td>${date}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    function setText(id, text) {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    }
})();
