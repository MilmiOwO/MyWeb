async function loadRequests() {
    const listContainer = document.getElementById('requestList');
    if (!listContainer) return;
    const selectAllCheckbox = document.getElementById('selectAll');
    const isSelectAllActive = selectAllCheckbox ? selectAllCheckbox.checked : false;

    try {
        const response = await fetch('/api/requests');
        const data = await response.json();
        const requests = data.requests || [];

        listContainer.innerHTML = '';

        if (requests.length === 0) {
            listContainer.innerHTML = `<div class="empty-message">Waiting for requests on /q...</div>`;
            return;
        }

        requests.forEach(req => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'bin-request-item';
            itemDiv.onclick = () => showRequestDetails(req);

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'request-checkbox';
            checkbox.value = req.id;
            checkbox.onclick = (e) => e.stopPropagation();
            if (isSelectAllActive) {
                checkbox.checked = true;
            }

            checkbox.addEventListener('change', () => {
                if (!checkbox.checked && selectAllCheckbox) {
                    selectAllCheckbox.checked = false;
                } else if (checkbox.checked && selectAllCheckbox) {
                    const allBoxes = document.querySelectorAll('.request-checkbox');
                    const allChecked = Array.from(allBoxes).every(cb => cb.checked);
                    selectAllCheckbox.checked = allChecked;
                }
            });

            const timeStr = req.timestamp ? req.timestamp.substring(11) : '';
            const nameSpan = document.createElement('span');
            nameSpan.className = 'request-name';
            nameSpan.textContent = `${req.method} (${timeStr})`;

            itemDiv.appendChild(checkbox);
            itemDiv.appendChild(nameSpan);
            listContainer.appendChild(itemDiv);
        });

    } catch (error) {
        console.error('Error fetching requests:', error);
        listContainer.innerHTML = `<div class="empty-message" style="color: red;">Failed to load requests.</div>`;
    }
}

function showRequestDetails(req) {
    const detailContainer = document.getElementById('requestDetail');
    if (!detailContainer) return;
    const createTableHTML = (obj) => {
        if (!obj || Object.keys(obj).length === 0) return '<div class="detail-empty">None</div>';

        let html = '<table class="detail-table">';
        for (const [key, value] of Object.entries(obj)) {
            const displayValue = typeof value === 'object' ? JSON.stringify(value) : value;
            html += `<tr><th>${key}</th><td>${displayValue}</td></tr>`;
        }
        html += '</table>';
        return html;
    };

    let bodyHTML = '<div class="detail-empty">None</div>';
    if (req.body) {
        try {
            const parsedBody = typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
            bodyHTML = `<pre class="detail-body-pre">${JSON.stringify(parsedBody, null, 2)}</pre>`;
        } catch (e) {
            bodyHTML = `<div class="detail-body-text">${req.body}</div>`;
        }
    }

    const queryObj = req.query || req.args || {};

    detailContainer.innerHTML = `
        <div class="detail-container">
            <h2 class="detail-title">${req.method} ${req.path || '/q'}</h2>
            <div class="detail-meta">
                <span><strong>ID:</strong> ${req.id}</span>
                <span><strong>Time:</strong> ${req.timestamp}</span>
                <span><strong>IP:</strong> ${req.ip}</span>
                <button onclick="copyRawHttp(\`${btoa(unescape(encodeURIComponent(req.raw_http)))} \`)" class="copy-btn">
                    Copy Raw HTTP
                </button>
            </div>
            
            <h3 class="detail-section-title">Query Parameters</h3>
            ${createTableHTML(queryObj)}
            
            <h3 class="detail-section-title">Headers</h3>
            ${createTableHTML(req.headers)}
            
            <h3 class="detail-section-title">Body</h3>
            <div class="detail-body-wrapper">
                ${bodyHTML}
            </div>
        </div>
    `;
}

async function deleteSelectedRequests() {
    const checkedBoxes = document.querySelectorAll('.request-checkbox:checked');
    const idsToDelete = Array.from(checkedBoxes).map(cb => cb.value);
    if (idsToDelete.length === 0) {
        return;
    }
    try {
        const response = await fetch('/api/requests/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids: idsToDelete })
        });

        const result = await response.json();

        if (result.status === 'success') {
            const selectAllCheckbox = document.getElementById('selectAll');
            if (selectAllCheckbox) selectAllCheckbox.checked = false;
            await loadRequests();
            document.getElementById('requestDetail').innerHTML = `
                <div class="content-placeholder">request info</div>
            `;
        }
    } catch (error) {
        console.error('Error deleting requests:', error);
        alert('an error occurred while deleting');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadRequests();
    const selectAllCheckbox = document.getElementById('selectAll');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', (e) => {
            const isChecked = e.target.checked;
            const checkboxes = document.querySelectorAll('.request-checkbox');
            checkboxes.forEach(cb => cb.checked = isChecked);
        });
    }
});

const source = new EventSource('/api/stream');

source.onmessage = function(event) {
    if (event.data === 'update') {
        loadRequests();
    }
};

function copyRawHttp(base64Str) {
    // 줄바꿈 및 특수문자 깨짐 방지를 위해 인코딩된 base64를 다시 디코딩합니다.
    const textToCopy = decodeURIComponent(escape(atob(base64Str.trim())));

    navigator.clipboard.writeText(textToCopy).then(() => {
        alert('HTTP 원본 요청이 클립보드에 복사되었습니다!');
    }).catch(err => {
        console.error('복사 실패:', err);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    // 1. 현재 브라우저 주소창의 경로를 가져옵니다 (예: '/requestbin')
    const currentPath = window.location.pathname;

    // 2. 상단 바에 있는 모든 메뉴 링크들('a' 태그)을 가져옵니다
    const navLinks = document.querySelectorAll('.navbar-element');

    // 3. 각 링크의 주소(href)와 현재 주소창의 경로가 일치하면 active 클래스를 추가합니다
    navLinks.forEach(link => {
        // link.getAttribute('href')는 '/requestbin', '/about' 등을 반환합니다.
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});