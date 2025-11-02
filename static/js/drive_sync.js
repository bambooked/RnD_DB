let availableDriveFolders = [];
const selectedFolders = new Map();

function getSelectedFolderIds() {
    return Array.from(selectedFolders.keys());
}

function getSelectedFolderNames() {
    return Array.from(selectedFolders.values());
}

function formatSelectedFolderLabel(names) {
    if (names.length === 0) return 'フォルダを選択...';
    const unique = names.filter(Boolean);
    if (unique.length === 0) return `${names.length}件選択`;
    if (unique.length <= 3) return unique.join(', ');
    return `${unique.slice(0, 3).join(', ')} 他${unique.length - 3}件`;
}

function updateSelectedFoldersUI() {
    const label = document.getElementById('selected-folder-name');
    const hiddenInput = document.getElementById('selected-folder-ids');
    if (label) {
        label.textContent = formatSelectedFolderLabel(getSelectedFolderNames());
    }
    if (hiddenInput) {
        hiddenInput.value = JSON.stringify(getSelectedFolderIds());
    }
}

async function persistSelectedFolders() {
    try {
        await fetch('/api/drive/set-folder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ folder_ids: getSelectedFolderIds() }),
        });
    } catch (error) {
        console.error('フォルダ設定エラー:', error);
    }
}

async function initializeSelectedFolders() {
    try {
        const response = await fetch('/api/google-drive/status');
        const status = await response.json();

        if (status.enabled && Array.isArray(status.configured_folder_ids)) {
            selectedFolders.clear();
            const selectedInfo = Array.isArray(status.selected_folders) ? status.selected_folders : [];
            status.configured_folder_ids.forEach((folderId) => {
                const info = selectedInfo.find((item) => item.id === folderId);
                selectedFolders.set(folderId, info?.name || folderId);
            });
            updateSelectedFoldersUI();
        }
    } catch (error) {
        console.error('フォルダ初期化エラー:', error);
    }
}

async function checkAuthStatus() {
    try {
        const response = await fetch('/api/auth/google/status');
        const data = await response.json();
        const notAuth = document.getElementById('not-authenticated');
        const auth = document.getElementById('authenticated');

        if (!notAuth || !auth) return;

        if (data.authenticated) {
            notAuth.classList.add('hidden');
            auth.classList.remove('hidden');
            await initializeSelectedFolders();
        } else {
            notAuth.classList.remove('hidden');
            auth.classList.add('hidden');
        }
    } catch (error) {
        console.error('Auth status check error:', error);
    }
}

function renderFolderList(container) {
    container.innerHTML = '';
    availableDriveFolders.forEach((folder) => {
        const item = document.createElement('label');
        item.className = 'flex items-center gap-3 px-4 py-2 hover:bg-slate-50 cursor-pointer text-sm';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'h-4 w-4 text-blue-600';
        checkbox.value = folder.id;
        checkbox.checked = selectedFolders.has(folder.id);
        checkbox.addEventListener('change', (event) => {
            if (event.target.checked) {
                selectedFolders.set(folder.id, folder.name);
            } else {
                selectedFolders.delete(folder.id);
            }
            updateSelectedFoldersUI();
            persistSelectedFolders();
        });

        const labelText = document.createElement('span');
        labelText.textContent = folder.name;

        item.appendChild(checkbox);
        item.appendChild(labelText);
        container.appendChild(item);
    });
}

async function populateFolderList() {
    const listWrapper = document.getElementById('folder-list');
    const listContent = document.getElementById('folder-list-content');
    if (!listWrapper || !listContent) return;

    if (!listWrapper.classList.contains('hidden')) {
        listWrapper.classList.add('hidden');
        return;
    }

    listContent.innerHTML = `
        <div class="flex items-center gap-2 px-4 py-3 text-sm text-slate-500">
            <i class="fas fa-spinner fa-spin"></i>
            <span>フォルダ一覧を取得しています...</span>
        </div>
    `;
    listWrapper.classList.remove('hidden');

    try {
        const response = await fetch('/api/drive/folders');
        if (response.status === 401) {
            listContent.innerHTML = '<p class="px-4 py-3 text-sm text-red-500">Google認証を先に実施してください。</p>';
            return;
        }
        const data = await response.json();
        availableDriveFolders = Array.isArray(data.folders) ? data.folders : [];
        if (availableDriveFolders.length === 0) {
            listContent.innerHTML = '<p class="px-4 py-3 text-sm text-slate-500">利用可能なフォルダが見つかりませんでした。</p>';
            return;
        }
        renderFolderList(listContent);
    } catch (error) {
        console.error('フォルダ一覧取得エラー:', error);
        listContent.innerHTML = '<p class="px-4 py-3 text-sm text-red-500">フォルダ一覧の取得に失敗しました。</p>';
    }
}

async function syncGoogleDrive() {
    const button = document.getElementById('sync-button');
    const text = document.getElementById('sync-text');
    const loading = document.getElementById('sync-loading');
    const result = document.getElementById('sync-result');
    const folderType = document.getElementById('sync-folder-type');

    if (!button || !text || !loading || !result || !folderType) return;

    result.classList.add('hidden');
    result.className = 'hidden p-4 rounded-lg text-sm';

    try {
        const authStatusResponse = await fetch('/api/auth/google/status');
        const authStatus = await authStatusResponse.json();
        if (!authStatus.authenticated) {
            result.className = 'p-4 rounded-lg text-sm bg-amber-50 border border-amber-200 text-amber-700';
            result.innerHTML = '<i class="fas fa-exclamation-triangle mr-2"></i>Google Drive認証が必要です。まずログインしてください。';
            result.classList.remove('hidden');
            return;
        }
    } catch (error) {
        console.error('認証状態確認エラー:', error);
        result.className = 'p-4 rounded-lg text-sm bg-red-50 border border-red-200 text-red-600';
        result.innerHTML = '<i class="fas fa-times mr-2"></i>認証状態の確認に失敗しました。';
        result.classList.remove('hidden');
        return;
    }

    button.disabled = true;
    text.style.display = 'none';
    loading.classList.add('show');

    try {
        const payload = {
            folder_type: folderType.value,
        };
        const folderIds = getSelectedFolderIds();
        if (folderIds.length > 0) {
            payload.folder_ids = folderIds;
        }

        const response = await fetch('/api/sync/google-drive', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await response.json();

        if (data.success) {
            result.className = 'p-4 rounded-lg text-sm bg-emerald-50 border border-emerald-200 text-emerald-700';
            result.innerHTML = `<i class="fas fa-check mr-2"></i>${data.message}`;
        } else {
            result.className = 'p-4 rounded-lg text-sm bg-red-50 border border-red-200 text-red-600';
            result.innerHTML = '<i class="fas fa-times mr-2"></i>同期に失敗しました。';
        }
    } catch (error) {
        console.error('同期エラー:', error);
        result.className = 'p-4 rounded-lg text-sm bg-red-50 border border-red-200 text-red-600';
        result.innerHTML = '<i class="fas fa-times mr-2"></i>同期エラーが発生しました。';
    } finally {
        result.classList.remove('hidden');
        button.disabled = false;
        text.style.display = 'inline';
        loading.classList.remove('show');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    checkAuthStatus();
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('auth_success')) {
        checkAuthStatus();
        window.history.replaceState({}, document.title, window.location.pathname);
    }

    const loginBtn = document.getElementById('google-login-btn');
    if (loginBtn) {
        loginBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/auth/google/login');
                const data = await response.json();
                if (data.auth_url) {
                    window.location.href = data.auth_url;
                }
            } catch (error) {
                console.error('ログインエラー:', error);
                alert('Googleログインの開始に失敗しました。');
            }
        });
    }

    const selectFolderBtn = document.getElementById('select-folder-btn');
    if (selectFolderBtn) {
        selectFolderBtn.addEventListener('click', () => populateFolderList());
    }

    const selectAllBtn = document.getElementById('select-all-folders');
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', () => {
            availableDriveFolders.forEach((folder) => {
                selectedFolders.set(folder.id, folder.name);
            });
            updateSelectedFoldersUI();
            persistSelectedFolders();
            const content = document.getElementById('folder-list-content');
            if (content) renderFolderList(content);
        });
    }

    const clearAllBtn = document.getElementById('clear-all-folders');
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', () => {
            selectedFolders.clear();
            updateSelectedFoldersUI();
            persistSelectedFolders();
            const content = document.getElementById('folder-list-content');
            if (content) renderFolderList(content);
        });
    }

    const syncBtn = document.getElementById('sync-button');
    if (syncBtn) {
        syncBtn.addEventListener('click', () => syncGoogleDrive());
    }
});
