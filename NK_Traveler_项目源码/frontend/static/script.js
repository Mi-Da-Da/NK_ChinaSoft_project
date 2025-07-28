let currentSessionId = null;

// 加载会话列表
function loadSessions() {
    fetch('/sessions')
        .then(res => res.json())
        .then(sessions => {
            const list = document.getElementById('session-list');
            list.innerHTML = '';
            sessions.forEach(s => {
                const li = document.createElement('li');
                li.className = 'session-item';
                li.textContent = s.title;
                li.onclick = (e) => {
                    // 避免点击菜单时触发选中
                    if (e.target.classList.contains('session-menu-btn') || e.target.classList.contains('session-menu-dropdown') || e.target.closest('.session-menu-dropdown')) return;
                    selectSession(s.id);
                };
                li.dataset.sessionId = s.id;
                // ...菜单按钮
                const menuBtn = document.createElement('button');
                menuBtn.className = 'session-menu-btn';
                menuBtn.innerText = '...';
                menuBtn.title = '更多操作';
                menuBtn.type = 'button';
                menuBtn.tabIndex = -1;
                // 下拉菜单
                const dropdown = document.createElement('div');
                dropdown.className = 'session-menu-dropdown';
                // 删除按钮
                const delBtn = document.createElement('button');
                delBtn.innerText = '删除';
                delBtn.onclick = function(ev) {
                    ev.stopPropagation();
                    dropdown.style.display = 'none';
                    showDeleteSessionModal(s.id);
                };
                // 重命名按钮
                const renameBtn = document.createElement('button');
                renameBtn.innerText = '重命名';
                renameBtn.onclick = function(ev) {
                    ev.stopPropagation();
                    dropdown.style.display = 'none';
                    showRenameSessionModal(s.id, s.title);
                };
                dropdown.appendChild(renameBtn);
                dropdown.appendChild(delBtn);
                menuBtn.onclick = function(ev) {
                    ev.stopPropagation();
                    // 关闭其他菜单
                    document.querySelectorAll('.session-menu-dropdown').forEach(d => { d.style.display = 'none'; });
                    dropdown.style.display = 'flex';
                };
                // 点击外部关闭菜单
                document.addEventListener('click', function hideDropdown(e) {
                    if (!menuBtn.contains(e.target) && !dropdown.contains(e.target)) {
                        dropdown.style.display = 'none';
                    }
                });
                menuBtn.appendChild(dropdown);
                li.appendChild(menuBtn);
                list.appendChild(li);
            });
            // 默认选中第一个会话
            if (currentSessionId === null && sessions.length > 0) {
                selectSession(sessions[0].id);
            } else {
                highlightCurrentSession();
            }
        });
}

// 高亮当前会话
function highlightCurrentSession() {
    document.querySelectorAll('.session-item').forEach(li => {
        li.classList.toggle('active', Number(li.dataset.sessionId) === currentSessionId);
    });
}

function renderMessage(msg) {
    const div = document.createElement('div');
    div.className = 'message ' + msg.role;
    // 设置对齐方式
    if (msg.role === 'user') {
        div.style.justifyContent = 'flex-end';
        div.style.textAlign = 'right';
    } else {
        div.style.justifyContent = 'flex-start';
        div.style.textAlign = 'left';
    }
    div.style.display = 'flex';
    // 头像图片
    const avatarImg = document.createElement('img');
    avatarImg.className = 'avatar';
    avatarImg.src = msg.role === 'user' ? '/static/avatars/user.png' : '/static/avatars/bot.png';
    avatarImg.alt = msg.role === 'user' ? '你' : 'NK-Traveler';
    // 昵称和内容
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    const nickname = document.createElement('span');
    nickname.className = 'nickname';
    nickname.innerText = msg.role === 'user' ? '你' : 'NK-Traveler';
    const text = document.createElement('span');
    text.className = 'text';
    if (msg.role === 'bot' && window.marked) {
        text.innerHTML = marked.parse(msg.message);
    } else {
    text.innerText = msg.message;
    }
    bubble.appendChild(nickname);
    bubble.appendChild(text);
    // 用户消息：内容在右，头像在右
    if (msg.role === 'user') {
        div.appendChild(bubble);
        div.appendChild(avatarImg);
    } else {
        // AI消息：头像在左，内容在右
        div.appendChild(avatarImg);
        div.appendChild(bubble);
    }
    return div;
}

// 选择会话并加载内容
function selectSession(sessionId) {
    currentSessionId = Number(sessionId);
    highlightCurrentSession();
    fetch(`/session/${sessionId}`)
        .then(res => res.json())
        .then(history => {
            const chatBox = document.getElementById('chat-box');
            chatBox.innerHTML = '';
            // 始终插入自我介绍气泡
            const introMsg = {
                role: 'bot',
                message: '你好，我是NK-Traveler，我是一个基于通义千问大模型构建起来的旅游规划助手，我们可以帮助你规划行程，实施规划行程路径等等，很高兴能够帮助你。'
            };
            chatBox.appendChild(renderMessage(introMsg));
            history.forEach(msg => {
                chatBox.appendChild(renderMessage(msg));
            });
            chatBox.scrollTop = chatBox.scrollHeight;
        });
}

// 发送消息
function sendMessage() {
    const input = document.getElementById("user-input");
    const message = input.value.trim();
    if (!message || !currentSessionId) return;

    // 1. 立即插入用户消息气泡
    const chatBox = document.getElementById('chat-box');
    chatBox.appendChild(renderMessage({role: 'user', message: message}));
    chatBox.scrollTop = chatBox.scrollHeight;

    // 2. 显示“思考中”气泡
    const thinkingDiv = document.createElement('div');
    thinkingDiv.className = 'message bot';
    thinkingDiv.style.justifyContent = 'flex-start';
    thinkingDiv.style.textAlign = 'left';
    thinkingDiv.style.display = 'flex';
    const avatarImg = document.createElement('img');
    avatarImg.className = 'avatar';
    avatarImg.src = '/static/avatars/bot.png';
    avatarImg.alt = 'NK-Traveler';
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    const nickname = document.createElement('span');
    nickname.className = 'nickname';
    nickname.innerText = 'NK-Traveler';
    const text = document.createElement('span');
    text.className = 'text';
    text.innerHTML = '<span class="thinking-dot">●</span> <span class="thinking-dot">●</span> <span class="thinking-dot">●</span> 正在思考...';
    bubble.appendChild(nickname);
    bubble.appendChild(text);
    thinkingDiv.appendChild(avatarImg);
    thinkingDiv.appendChild(bubble);
    chatBox.appendChild(thinkingDiv);
    chatBox.scrollTop = chatBox.scrollHeight;

    // 3. 发送请求
    const rag = document.getElementById('option-rag').checked;
    const search = document.getElementById('option-search').checked;
    fetch('/send', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: message, session_id: currentSessionId, rag: rag, search: search })
    })
    .then(response => response.json())
    .then(data => {
        // 替换“思考中”气泡为真实AI回复
        thinkingDiv.remove();
        selectSession(currentSessionId); // 重新加载会话内容
        input.value = "";
    });
}

// 新建会话弹窗逻辑
function showNewSessionModal() {
    const overlay = document.getElementById('modal-overlay');
    const input = document.getElementById('modal-session-title');
    overlay.style.display = 'flex';
    input.value = '';
    input.focus();

    // 绑定事件
    document.getElementById('modal-confirm-btn').onclick = function() {
        const title = input.value.trim() || '新会话';
        fetch('/session/new', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title })
        })
        .then(res => res.json())
        .then(newSession => {
            overlay.style.display = 'none';
            loadSessions();
            setTimeout(() => selectSession(newSession.id), 200);
        });
    };
    document.getElementById('modal-cancel-btn').onclick = function() {
        overlay.style.display = 'none';
    };
    input.onkeydown = function(e) {
        if (e.key === 'Enter') document.getElementById('modal-confirm-btn').onclick();
    };
}
document.getElementById('new-session-btn').onclick = showNewSessionModal;

function showDeleteSessionModal(sessionId) {
    const overlay = document.getElementById('delete-modal-overlay');
    overlay.style.display = 'flex';

    document.getElementById('delete-modal-confirm-btn').onclick = function() {
        overlay.style.display = 'none';
        fetch(`/session/${sessionId}`, {
            method: 'DELETE'
        }).then(res => {
            if (res.ok) {
                if (Number(sessionId) === currentSessionId) {
                    currentSessionId = null;
                }
                loadSessions();
                document.getElementById('chat-box').innerHTML = '';
            }
        });
    };
    document.getElementById('delete-modal-cancel-btn').onclick = function() {
        overlay.style.display = 'none';
    };
}

function showClearHistoryModal() {
    const overlay = document.getElementById('clear-modal-overlay');
    overlay.style.display = 'flex';

    document.getElementById('clear-modal-confirm-btn').onclick = function() {
        overlay.style.display = 'none';
        fetch(`/sessions/clear`, {
            method: 'POST'
        }).then(res => {
            if (res.ok) {
                loadSessions();
                document.getElementById('chat-box').innerHTML = '';
            }
        });
    };
    document.getElementById('clear-modal-cancel-btn').onclick = function() {
        overlay.style.display = 'none';
    };
}
document.getElementById('clear-history-btn').onclick = showClearHistoryModal;

// 重命名弹窗逻辑
function showRenameSessionModal(sessionId, oldTitle) {
    const overlay = document.getElementById('rename-modal-overlay');
    const input = document.getElementById('rename-session-title');
    overlay.style.display = 'flex';
    input.value = oldTitle || '';
    input.focus();
    document.getElementById('rename-modal-confirm-btn').onclick = function() {
        const newTitle = input.value.trim();
        if (!newTitle) return;
        fetch(`/session/${sessionId}/rename`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: newTitle })
        })
        .then(res => res.json())
        .then(result => {
            if (result.success) {
                overlay.style.display = 'none';
                loadSessions();
            } else {
                alert(result.message || '重命名失败');
            }
        });
    };
    document.getElementById('rename-modal-cancel-btn').onclick = function() {
        overlay.style.display = 'none';
    };
    input.onkeydown = function(e) {
        if (e.key === 'Enter') document.getElementById('rename-modal-confirm-btn').onclick();
    };
}

// 语音识别相关
let recognition;
if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
} else if ('SpeechRecognition' in window) {
    recognition = new SpeechRecognition();
}
if (recognition) {
    recognition.lang = 'zh-CN'; // 中文识别
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        document.getElementById('user-input').value = transcript;
    };
    recognition.onerror = function(event) {
        alert('语音识别出错: ' + event.error);
    };
}

window.addEventListener('DOMContentLoaded', function() {
    const voiceBtn = document.getElementById('voice-btn');
    if (voiceBtn) {
        voiceBtn.onclick = function() {
            if (recognition) {
                recognition.start();
            } else {
                alert('当前浏览器不支持语音识别');
            }
        };
    }
});

// 页面加载时初始化
window.onload = function() {
    loadSessions();
};

document.getElementById('toggle-sidebar-btn').onclick = function() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('collapsed');
    // 收缩时隐藏清空历史按钮，展开时显示
    const clearBtn = document.getElementById('clear-history-btn');
    if (sidebar.classList.contains('collapsed')) {
        clearBtn.style.display = 'none';
    } else {
        clearBtn.style.display = '';
    }
};

document.getElementById('toggle-weather-sidebar-btn').onclick = function() {
    const sidebar = document.getElementById('weather-sidebar');
    sidebar.classList.toggle('collapsed');
};

document.getElementById('weather-search-btn').onclick = function() {
    const city = document.getElementById('weather-city-input').value.trim();
    if (!city) {
        document.getElementById('weather-result').innerText = '请输入城市名';
        return;
    }
    document.getElementById('weather-result').innerText = '查询中...';
    fetch(`/api/weather?city=${encodeURIComponent(city)}&days=3`)
        .then(res => res.json())
        .then(data => {
            if (!data.success) {
                document.getElementById('weather-result').innerHTML = `<div class='bubble-output'>${data.message || '未查询到天气信息'}</div>`;
                return;
            }
            let html = `<div class='bubble-output'><div style='margin-bottom:8px;'>${data.current}</div>`;
            if (data.forecast && data.forecast.length > 0) {
                html += '<div>未来3天天气预报：</div>';
                html += '<ul style="padding-left:18px;">';
                data.forecast.forEach(day => {
                    html += `<li>${day.date}：${day.dayweather}，最高${day.daytemp}℃，最低${day.nighttemp}℃，${day.daywind}风${day.daypower}级</li>`;
                });
                html += '</ul>';
            }
            html += '</div>';
            document.getElementById('weather-result').innerHTML = html;
        })
        .catch(() => {
            document.getElementById('weather-result').innerText = '查询失败，请重试';
        });
};

// 右侧栏Tab切换逻辑
const tabWeather = document.getElementById('tab-weather');
const tabRoute = document.getElementById('tab-route');
const weatherTabContent = document.getElementById('weather-tab-content');
const routeTabContent = document.getElementById('route-tab-content');
tabWeather.onclick = function() {
    tabWeather.classList.add('active');
    tabRoute.classList.remove('active');
    weatherTabContent.style.display = '';
    routeTabContent.style.display = 'none';
};
tabRoute.onclick = function() {
    tabRoute.classList.add('active');
    tabWeather.classList.remove('active');
    weatherTabContent.style.display = 'none';
    routeTabContent.style.display = '';
};

// 路径规划查询
const routeSearchBtn = document.getElementById('route-search-btn');
routeSearchBtn.onclick = function() {
    const origin = document.getElementById('route-origin-input').value.trim();
    const dest = document.getElementById('route-dest-input').value.trim();
    const mode = document.getElementById('route-mode-input').value;
    const resultDiv = document.getElementById('route-result');
    if (!origin || !dest) {
        resultDiv.innerText = '请输入起点和终点';
        return;
    }
    resultDiv.innerText = '查询中...';
    fetch(`/api/route?origin=${encodeURIComponent(origin)}&dest=${encodeURIComponent(dest)}&mode=${encodeURIComponent(mode)}`)
        .then(res => res.json())
        .then(data => {
            if (!data.success) {
                resultDiv.innerText = data.message || '\u672a\u67e5\u8be2\u5230\u8def\u5f84';
                return;
            }
            resultDiv.innerHTML = `<div class='bubble-output'>${window.marked ? marked.parse(data.answer || '\u672a\u67e5\u8be2\u5230\u8def\u5f84') : (data.answer || '\u672a\u67e5\u8be2\u5230\u8def\u5f84')}</div>`;
        })
        .catch(() => {
            resultDiv.innerText = '查询失败，请重试';
        });
};

// 保留原有对话相关逻辑，不包含天气和路线的按钮及函数
