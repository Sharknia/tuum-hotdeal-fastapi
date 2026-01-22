import { checkLoginStatus, getUserInfo, logout } from './js/auth_utils.js';

const chatbox = document.getElementById('chatbox');
const messageInput = document.getElementById('message');
const appLayout = document.getElementById('app-layout'); // 앱 레이아웃 요소
const sidebarToggle = document.getElementById('sidebar-toggle'); // 사이드바 토글 버튼
const newChatButton = document.getElementById('new-chat-button'); // 새 채팅 버튼
const modelSelector = document.getElementById('model-selector'); // 모델 선택 드롭다운
const userProfileArea = document.getElementById('user-profile-area'); // 사용자 프로필 영역
const profileDropdown = document.getElementById('profile-dropdown'); // 프로필 드롭다운

// WebSocket 연결 및 메시지 처리는 나중에 추가됩니다.
let ws;

function addMessageToChatbox(text, type) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', type === 'user' ? 'user-message' : 'assistant-message');
    messageDiv.textContent = text;
    chatbox.appendChild(messageDiv);
    chatbox.scrollTop = chatbox.scrollHeight;
}

function sendMessage() {
    const message = messageInput.value.trim();
    if (message) {
        addMessageToChatbox(message, 'user'); // 사용자 메시지 표시 함수 사용
        messageInput.value = ''; // 입력창 비우기

        // TODO: WebSocket을 통해 서버로 메시지 전송 로직 추가
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'message', content: message }));
        } else {
            console.error('WebSocket is not connected.');
            // 임시로 에러 메시지 표시 또는 다른 처리
            addMessageToChatbox('서버에 연결되지 않았습니다.', 'assistant');
        }
    }
}

// Enter 키로 메시지 전송
messageInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// 사이드바 토글 버튼 이벤트 리스너
sidebarToggle.addEventListener('click', () => {
    appLayout.classList.toggle('sidebar-collapsed');
});

// 새 채팅 버튼 이벤트 리스너 (현재는 콘솔 로그만)
newChatButton.addEventListener('click', () => {
    console.log('New Chat button clicked!');
    // TODO: 새 채팅 시작 로직 구현 (예: 채팅 목록 초기화, 서버에 새 세션 요청 등)
    chatbox.innerHTML = ''; // 임시로 채팅 내용 비우기
    addMessageToChatbox('새 채팅이 시작되었습니다.', 'assistant');
});

// 모델 선택 변경 이벤트 리스너 (현재는 콘솔 로그만)
modelSelector.addEventListener('change', (event) => {
    const selectedModel = event.target.value;
    console.log('Model selected:', selectedModel);
    // TODO: 선택된 모델을 서버로 전달하거나 관련 로직 처리
    addMessageToChatbox(`모델이 ${selectedModel}(으)로 변경되었습니다. (실제 적용 로직 필요)`, 'assistant');
});

// 사용자 프로필 영역 클릭 이벤트 리스너 (드롭다운 토글)
userProfileArea.addEventListener('click', (event) => {
    profileDropdown.classList.toggle('show');
    event.stopPropagation(); // 이벤트 버블링 방지
});

// 드롭다운 메뉴 항목 이벤트 리스너 (현재는 콘솔 로그만)
document.getElementById('settings-button').addEventListener('click', (event) => {
    event.preventDefault(); // 기본 링크 동작 방지
    console.log('Settings clicked!');
    profileDropdown.classList.remove('show'); // 메뉴 닫기
    // TODO: 설정 관련 로직 구현
});

document.getElementById('logout-button').addEventListener('click', logout);

// 드롭다운 외부 클릭 시 메뉴 닫기
window.addEventListener('click', (event) => {
    if (!userProfileArea.contains(event.target)) {
        if (profileDropdown.classList.contains('show')) {
            profileDropdown.classList.remove('show');
        }
    }
});

// TODO: WebSocket 연결 및 서버로부터 메시지 수신 로직 추가
function connectWebSocket() {
    // WebSocket 주소는 FastAPI 서버 설정에 맞게 조정해야 합니다.
    const wsUrl = `ws://${window.location.host}/ws`;
    ws = new WebSocket(wsUrl);

    ws.onopen = function (event) {
        console.log('WebSocket connection opened');
        addMessageToChatbox('서버에 연결되었습니다.', 'assistant');
    };

    ws.onmessage = function (event) {
        console.log('Message from server: ', event.data);
        // 서버로부터 받은 메시지 처리 (LLM 응답)
        // 데이터 형식에 따라 파싱 필요 (예: JSON)
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'stream') {
                // 스트리밍 데이터 처리 (기존 메시지에 이어붙이거나 새 메시지 생성)
                let lastMessage = chatbox.lastElementChild;
                if (lastMessage && lastMessage.classList.contains('assistant-message')) {
                    lastMessage.textContent += data.content;
                } else {
                    addMessageToChatbox(data.content, 'assistant');
                }
                chatbox.scrollTop = chatbox.scrollHeight; // 스크롤 업데이트
            } else if (data.type === 'full_response') {
                // 전체 응답을 한 번에 받는 경우 (스트리밍 아닌 경우)
                addMessageToChatbox(data.content, 'assistant');
            } else if (data.type === 'system') {
                // 시스템 메시지 처리 (예: 모델 변경 확인)
                addMessageToChatbox(data.content, 'assistant');
            }
        } catch (e) {
            // 일반 텍스트 데이터 처리 (단순 스트리밍 등)
            let lastMessage = chatbox.lastElementChild;
            if (lastMessage && lastMessage.classList.contains('assistant-message')) {
                // 이어붙이기 (임시방편, 서버 응답 형식에 따라 개선 필요)
                lastMessage.textContent += event.data;
            } else {
                addMessageToChatbox(event.data, 'assistant');
            }
            chatbox.scrollTop = chatbox.scrollHeight;
        }
    };

    ws.onerror = function (event) {
        console.error('WebSocket error observed:', event);
        addMessageToChatbox('연결 오류가 발생했습니다.', 'assistant');
    };

    ws.onclose = function (event) {
        console.log('WebSocket connection closed. Code:', event.code, 'Reason:', event.reason);
        addMessageToChatbox('서버와의 연결이 끊어졌습니다.', 'assistant');
        // 필요시 재연결 로직 추가
        // setTimeout(connectWebSocket, 5000); // 5초 후 재연결 시도
    };
}

// 페이지 로드 시 WebSocket 연결 시작
// connectWebSocket(); // WebSocket 엔드포인트 구현 후 주석 해제
console.log('WebSocket connection logic to be added here.'); // 임시 로그

// 페이지 초기화
async function init() {
    // 로그인 체크
    const needLogin = await checkLoginStatus();
    if (needLogin) return;

    // 사용자 정보 표시
    const userInfo = await getUserInfo();
    if (userInfo) {
        document.getElementById('user-nickname').textContent = userInfo.nickname;
    }

    // 기존 초기화 로직...
    setupEventListeners();
    loadChatHistory();
}

// 이벤트 리스너 설정
function setupEventListeners() {
    // 로그아웃 버튼
    document.getElementById('logout-button').addEventListener('click', logout);

    // 프로필 드롭다운 토글
    const userProfileArea = document.getElementById('user-profile-area');
    const dropdownContent = document.getElementById('profile-dropdown');

    userProfileArea.addEventListener('click', () => {
        dropdownContent.classList.toggle('show');
    });

    // 사이드바 토글
    document.getElementById('sidebar-toggle').addEventListener('click', () => {
        document.getElementById('app-layout').classList.toggle('sidebar-collapsed');
    });

    // 메시지 전송
    document.getElementById('message').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
}

// 채팅 기록 로드
async function loadChatHistory() {
    // 채팅 기록 로드 로직 구현...
}

// 페이지 로드 시 초기화
init();
