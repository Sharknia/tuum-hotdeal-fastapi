const keywordListElement = document.getElementById('hotdeal-keyword-list');
const keywordInputElement = document.getElementById('hotdeal-keyword-input');

let siteList = [];

async function loadSites() {
    try {
        const response = await fetch(`${API_URL}/hotdeal/v1/sites`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        siteList = await response.json();
    } catch (error) {
        console.error('사이트 목록 로드 실패:', error);
        siteList = [];
    }
}

function buildSearchUrl(template, keyword) {
    return template.replace('{keyword}', encodeURIComponent(keyword));
}

function renderSiteLinks(keyword) {
    if (siteList.length === 0) {
        return '';
    }
    return siteList
        .map(
            (site) =>
                `<a href="${buildSearchUrl(site.search_url_template, keyword)}" target="_blank" class="search-link-button" title="${site.display_name}에서 검색">${site.display_name}</a>`
        )
        .join('');
}

function renderKeywords(keywords) {
    keywordListElement.innerHTML = '';
    if (!keywords || keywords.length === 0) {
        keywordListElement.innerHTML = '<li>등록된 키워드가 없습니다.</li>';
        return;
    }
    keywords.forEach((keyword) => {
        const listItem = document.createElement('li');
        listItem.dataset.id = keyword.id;
        listItem.innerHTML = `
            <span class="keyword-title">${keyword.title}</span>
            <div class="keyword-actions">
                ${renderSiteLinks(keyword.title)}
                <button class="delete-button" title="키워드 삭제">삭제</button>
            </div>
        `;
        keywordListElement.appendChild(listItem);
    });
}

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

async function addKeyword(title) {
    if (!title) {
        alert('키워드를 입력해주세요.');
        return;
    }
    if (title.match(/[^\w\s가-힣]/)) {
        alert('키워드에 특수문자를 포함할 수 없습니다.');
        keywordInputElement.value = '';
        return;
    }
    title = title.trim();
    if (title.length === 0) {
        alert('빈 공백만은 입력이 불가능합니다.');
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
                keywordInputElement.value = '';
            } else {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
        } else {
            await loadKeywords();
            keywordInputElement.value = '';
        }
    } catch (error) {
        console.error('키워드 추가 실패:', error);
        alert('키워드 추가 중 오류가 발생했습니다.');
    }
}

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
            console.log('키워드 삭제 성공');
            await loadKeywords();
        }
    } catch (error) {
        console.error('키워드 삭제 실패:', error);
        alert('키워드 삭제 중 오류가 발생했습니다.');
    }
}

async function initKeywordManager() {
    await loadSites();
    await loadKeywords();
}
