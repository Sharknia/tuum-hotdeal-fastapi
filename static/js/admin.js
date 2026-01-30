(async () => {
    // 1. 탭 전환 로직 (초기화 우선 실행)
    const tabs = document.querySelectorAll('.admin-tab');
    const sections = document.querySelectorAll('.admin-section');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // 활성 탭 스타일 변경
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // 섹션 표시 변경
            const targetId = tab.dataset.tab;
            sections.forEach(sec => {
                sec.classList.remove('active');
                if (sec.id === `${targetId}-section`) {
                    sec.classList.add('active');
                }
            });

            // 데이터 로드
            if (targetId === 'users') loadUsers();
            if (targetId === 'keywords') loadKeywords();
            if (targetId === 'logs') loadLogs();
        });
    });

    // 2. 관리자 권한 체크
    if (!hasValidTokens()) {
        window.location.href = '/login';
        return;
    }

    let userInfo;
    try {
        userInfo = await getUserInfo();
    } catch (error) {
        console.error('Failed to get user info:', error);
        window.location.href = '/login';
        return;
    }

    if (!userInfo) {
        window.location.href = '/login';
        return;
    }

    // auth_level 9 이상이 아니면 홈으로 리다이렉트
    if (userInfo.auth_level < 9) {
        alert('접근 권한이 없습니다.');
        window.location.href = '/hotdeal.html';
        return;
    }

    // 닉네임 표시
    const nicknameEl = document.getElementById('user-nickname');
    if (nicknameEl) {
        nicknameEl.textContent = userInfo.nickname;
    }

    // 로그아웃 버튼
    document.getElementById('logout-button')?.addEventListener('click', () => {
        if (confirm('정말로 로그아웃하시겠습니까?')) {
            logout();
        }
    });

    // 초기 로드
    loadUsers();

    // 3. 데이터 로딩 함수들
    async function loadUsers() {
        const tbody = document.querySelector('#users-table tbody');
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">로딩 중...</td></tr>';

        try {
            const response = await fetchWithAuth('/admin/users');
            if (!response.ok) throw new Error('Failed to fetch users');
            
            const data = await response.json();
            const users = data.items || data;
            tbody.innerHTML = '';

            if (users.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">사용자가 없습니다.</td></tr>';
                return;
            }

            users.forEach(user => {
                const tr = document.createElement('tr');
                const roleBadge = user.auth_level >= 9 
                    ? '<span class="status-badge status-admin">관리자</span>' 
                    : '<span class="status-badge status-user">일반</span>';
                
                // 가입일 포맷팅
                const joinDate = new Date(user.created_at).toLocaleDateString();

                // 최근 접속일 포맷팅
                const lastLogin = user.last_login 
                    ? new Date(user.last_login).toLocaleString('ko-KR') 
                    : '-';

                // 버튼 로직
                let actionBtn;
                if (user.is_active) {
                    actionBtn = `<button class="action-btn btn-delete" onclick="unapproveUser('${user.id}')">승인 해제</button>`;
                } else {
                    actionBtn = `<button class="action-btn btn-approve" onclick="approveUser('${user.id}')">승인</button>`;
                }

                tr.innerHTML = `
                    <td>${user.id}</td>
                    <td>${user.email}</td>
                    <td><a href="admin_user_detail.html?id=${user.id}" style="text-decoration: underline; color: inherit;">${user.nickname}</a></td>
                    <td>${roleBadge}</td>
                    <td>${lastLogin}</td>
                    <td>${joinDate}</td>
                    <td>
                        ${actionBtn}
                    </td>
                `;
                tbody.appendChild(tr);
            });
        } catch (error) {
            console.error(error);
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:red;">데이터를 불러오는데 실패했습니다.</td></tr>';
        }
    }

    async function loadKeywords() {
        const tbody = document.querySelector('#keywords-table tbody');
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">로딩 중...</td></tr>';

        try {
            const response = await fetchWithAuth('/admin/keywords');
            if (!response.ok) throw new Error('Failed to fetch keywords');

            const data = await response.json();
            const keywords = data.items || data;
            tbody.innerHTML = '';

            if (keywords.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">키워드가 없습니다.</td></tr>';
                return;
            }

            keywords.forEach(kw => {
                const tr = document.createElement('tr');
                const date = new Date(kw.wdate).toLocaleDateString();

                tr.innerHTML = `
                    <td>${kw.id}</td>
                    <td>${kw.title || kw.keyword}</td>
                    <td>${date}</td>
                    <td>
                        <button class="action-btn btn-delete" onclick="deleteKeyword(${kw.id})">삭제</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        } catch (error) {
            console.error(error);
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:red;">데이터를 불러오는데 실패했습니다.</td></tr>';
        }
    }

    async function loadLogs() {
        const tbody = document.querySelector('#logs-table tbody');
        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">로딩 중...</td></tr>';

        try {
            const response = await fetchWithAuth('/admin/logs');
            if (!response.ok) throw new Error('Failed to fetch logs');

            const data = await response.json();
            const logs = data.items || data;
            tbody.innerHTML = '';

            if (logs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">로그가 없습니다.</td></tr>';
                return;
            }

            logs.forEach(log => {
                const tr = document.createElement('tr');
                const date = new Date(log.run_at || log.created_at).toLocaleString();
                let levelClass = '';
                if (log.status === 'SUCCESS') levelClass = 'log-level-info';
                else if (log.status === 'RUNNING') levelClass = 'log-level-warn';
                else if (log.status === 'FAIL') levelClass = 'log-level-error';

                tr.innerHTML = `
                    <td>${date}</td>
                    <td><span class="status-badge ${levelClass}">${log.status}</span></td>
                    <td>${log.message}</td>
                    <td>${log.details || '-'}</td>
                `;
                tbody.appendChild(tr);
            });
        } catch (error) {
            console.error(error);
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:red;">데이터를 불러오는데 실패했습니다.</td></tr>';
        }
    }

    // 4. 전역 함수로 액션 노출 (HTML onclick에서 호출 가능하도록)
    window.approveUser = async (userId) => {
        if (!confirm('이 사용자를 승인하시겠습니까?')) return;
        
        try {
            const response = await fetchWithAuth(`/admin/users/${userId}/approve`, {
                method: 'PATCH'
            });
            
            if (response.ok) {
                alert('사용자가 승인되었습니다.');
                loadUsers(); // 목록 새로고침
            } else {
                const error = await response.text();
                alert('승인 실패: ' + error);
            }
        } catch (error) {
            console.error(error);
            alert('오류가 발생했습니다.');
        }
    };

    window.deleteKeyword = async (keywordId) => {
        if (!confirm('이 키워드를 정말 삭제하시겠습니까?')) return;

        try {
            const response = await fetchWithAuth(`/admin/keywords/${keywordId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                alert('키워드가 삭제되었습니다.');
                loadKeywords(); // 목록 새로고침
            } else {
                const error = await response.text();
                alert('삭제 실패: ' + error);
            }
        } catch (error) {
            console.error(error);
            alert('오류가 발생했습니다.');
        }
    };

    window.unapproveUser = async (userId) => {
        if (!confirm('이 사용자의 승인을 해제하시겠습니까?')) return;
        
        try {
            const response = await fetchWithAuth(`/admin/users/${userId}/unapprove`, {
                method: 'PATCH'
            });
            
            if (response.ok) {
                alert('사용자 승인이 해제되었습니다.');
                loadUsers(); // 목록 새로고침
            } else {
                const error = await response.text();
                alert('승인 해제 실패: ' + error);
            }
        } catch (error) {
            console.error(error);
            alert('오류가 발생했습니다.');
        }
    };

})();
