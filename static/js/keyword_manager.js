const keywordListElement = document.getElementById('hotdeal-keyword-list');
const keywordInputElement = document.getElementById('hotdeal-keyword-input');

// UI 업데이트 함수
function renderKeywords(keywords) {
    keywordListElement.innerHTML = ''; // 기존 목록 초기화
    if (!keywords || keywords.length === 0) {
        keywordListElement.innerHTML = '<li>등록된 키워드가 없습니다.</li>';
        return;
    }
    keywords.forEach((keyword) => {
        const listItem = document.createElement('li');
        listItem.dataset.id = keyword.id; // data-id 속성 추가
        listItem.innerHTML = `
            <span class="keyword-title">${keyword.title}</span>
            <div class="keyword-actions">
                <a href="https://www.algumon.com/search/${encodeURIComponent(
                    keyword.title
                )}" target="_blank" class="search-link-button" title="알구몬에서 검색하기">
                    전체 목록 보기
                </a>
                <button class="delete-button" title="키워드 삭제">삭제</button>
            </div>
        `;
        keywordListElement.appendChild(listItem);
    });
}

// 키워드 목록 로드 함수
async function loadKeywords() {
    try {
        const response = await fetchWithAuth('/hotdeal/v1/keywords');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const keywords = await response.json();
        renderKeywords(keywords);
    } catch (error) {
        console.error('키워드 로드 실패:', error);
        keywordListElement.innerHTML = '<li>키워드를 불러오는 중 오류가 발생했습니다.</li>';
    }
}

// 키워드 추가 함수
async function addKeyword(title) {
    if (!title) {
        alert('키워드를 입력해주세요.');
        return;
    }
    // title에 특수문자가 포함되어 있으면 추가 불가
    if (title.match(/[^\w\s가-힣]/)) {
        alert('키워드에 특수문자를 포함할 수 없습니다.');
        keywordInputElement.value = '';
        return;
    }
    // title 공백 제거
    title = title.trim();
    // title이 빈 문자열이면 추가 불가
    if (title.length === 0) {
        alert('빈 공백만은 입력이 불가능합니다.');
        // 입력창 초기화
        keywordInputElement.value = '';
        return;
    }
    try {
        const response = await fetchWithAuth('/hotdeal/v1/keywords', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ title: title }),
        });
        if (!response.ok) {
            if (response.status === 400) {
                const errorData = await response.json();
                alert(`키워드 추가 실패: ${errorData.detail || '잘못된 요청입니다.'}`);
                // 입력창 초기화
                keywordInputElement.value = '';
            } else {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
        } else {
            // 성공 시 목록 새로고침
            await loadKeywords();
            keywordInputElement.value = ''; // 입력 필드 초기화
        }
    } catch (error) {
        console.error('키워드 추가 실패:', error);
        alert('키워드 추가 중 오류가 발생했습니다.');
    }
}

// 키워드 삭제 함수
async function deleteKeyword(keywordId) {
    if (!keywordId) {
        console.error('삭제할 키워드의 ID가 없습니다.');
        return;
    }
    if (!confirm('정말로 이 키워드를 삭제하시겠습니까?')) {
        return;
    }
    try {
        const response = await fetchWithAuth(`/hotdeal/v1/keywords/${keywordId}`, {
            method: 'DELETE',
        });
        if (!response.ok) {
            if (response.status === 404) {
                alert('삭제하려는 키워드를 찾을 수 없습니다.');
            } else {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
        } else if (response.status === 204) {
            // No Content 성공 응답
            console.log('키워드 삭제 성공');
            // 성공 시 목록 새로고침
            await loadKeywords();
        }
    } catch (error) {
        console.error('키워드 삭제 실패:', error);
        alert('키워드 삭제 중 오류가 발생했습니다.');
    }
}
