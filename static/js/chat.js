/* global marked, DOMPurify, hljs */

let availableModels = [];
let chatHistory = [];
let isChatting = false;

async function loadAvailableModels() {
    const select = document.getElementById('selected-model');
    if (!select) return;

    try {
        const response = await fetch('/api/models');
        const data = await response.json();

        if (!data.success || !Array.isArray(data.models)) {
            console.error('モデル一覧の取得に失敗しました');
            return;
        }

        const filteredModels = data.models.filter((model) => model.visible !== false);
        availableModels = filteredModels;

        select.innerHTML = '<option value="">デフォルトモデル</option>';
        filteredModels.forEach((model) => {
            const option = document.createElement('option');
            option.value = model.model_id;
            option.textContent = model.model_name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('モデル一覧取得エラー:', error);
    }
}

function showModelDescription() {
    const select = document.getElementById('selected-model');
    const description = document.getElementById('model-description');
    const name = document.getElementById('model-description-name');
    const text = document.getElementById('model-description-text');
    const info = document.getElementById('model-description-info');

    if (!select || !description || !name || !text || !info) return;

    const selectedModelId = select.value;
    if (!selectedModelId) {
        description.classList.add('hidden');
        return;
    }

    const model = availableModels.find((m) => m.model_id === selectedModelId);
    if (!model) {
        description.classList.add('hidden');
        return;
    }

    name.textContent = model.model_name;
    text.textContent = model.description || 'モデルの説明はありません';

    const infoText = [];
    if (model.context_length) {
        infoText.push(`コンテキスト長: ${Number(model.context_length).toLocaleString()}トークン`);
    }
    if (model.top_provider) {
        infoText.push(`プロバイダー: ${model.top_provider}`);
    }
    if (model.pricing_prompt) {
        infoText.push(`価格: $${model.pricing_prompt}/M入力トークン`);
    }
    info.textContent = infoText.join(' | ');

    description.classList.remove('hidden');
}

function toggleModelInfo() {
    const description = document.getElementById('model-description');
    if (!description) return;
    if (description.classList.contains('hidden')) {
        showModelDescription();
    } else {
        description.classList.add('hidden');
    }
}

async function updateSystemStatus() {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();

        const driveStatus = document.getElementById('google-drive-status');
        if (driveStatus) {
            driveStatus.className = `w-3 h-3 rounded-full ${status.google_drive ? 'bg-emerald-400' : 'bg-amber-400'}`;
        }

        const databaseStatus = document.getElementById('database-status');
        if (databaseStatus) {
            databaseStatus.className = `w-3 h-3 rounded-full ${status.database ? 'bg-emerald-400' : 'bg-amber-400'}`;
        }

        const paperCountEl = document.getElementById('papers-count');
        if (paperCountEl) paperCountEl.textContent = status.stats.papers;
        const posterCountEl = document.getElementById('posters-count');
        if (posterCountEl) posterCountEl.textContent = status.stats.posters;
        const datasetCountEl = document.getElementById('datasets-count');
        if (datasetCountEl) datasetCountEl.textContent = status.stats.datasets;

        const chatPapers = document.getElementById('chat-papers-count');
        if (chatPapers) chatPapers.textContent = status.stats.papers;
        const chatPosters = document.getElementById('chat-posters-count');
        if (chatPosters) chatPosters.textContent = status.stats.posters;
        const chatDatasets = document.getElementById('chat-datasets-count');
        if (chatDatasets) chatDatasets.textContent = status.stats.datasets;

        document.querySelectorAll('.chat-papers-stat').forEach((el) => (el.textContent = status.stats.papers));
        document.querySelectorAll('.chat-posters-stat').forEach((el) => (el.textContent = status.stats.posters));
        document.querySelectorAll('.chat-datasets-stat').forEach((el) => (el.textContent = status.stats.datasets));
    } catch (error) {
        console.error('システム状態取得エラー:', error);
    }
}

function handleChatKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendChatMessage();
    }
}

function quickQuestion(question) {
    const input = document.getElementById('chat-input');
    if (!input) return;
    input.value = question;
    sendChatMessage();
}

function clearChat() {
    chatHistory = [];
    const historyDiv = document.getElementById('chat-history');
    if (!historyDiv) return;

    const papersCount = document.getElementById('papers-count');
    const postersCount = document.getElementById('posters-count');
    const datasetsCount = document.getElementById('datasets-count');

    historyDiv.innerHTML = `
        <div id="chat-welcome" class="text-center text-slate-500 py-8 space-y-3">
            <i class="fas fa-comment-alt text-4xl"></i>
            <p class="font-medium">研究について何でもお聞きください！</p>
            <p class="text-sm">データベース内の論文・ポスター・データセットを参照して回答します</p>
            <div class="mt-4 text-xs text-slate-400 space-x-3">
                <span>論文 <span class="chat-papers-stat">${papersCount ? papersCount.textContent : '-'}</span>件</span>
                <span>ポスター <span class="chat-posters-stat">${postersCount ? postersCount.textContent : '-'}</span>件</span>
                <span>データセット <span class="chat-datasets-stat">${datasetsCount ? datasetsCount.textContent : '-'}</span>件</span>
            </div>
        </div>
    `;

    const relatedSection = document.getElementById('related-items-section');
    if (relatedSection) relatedSection.classList.add('hidden');
}

async function sendChatMessage() {
    if (isChatting) return;

    const input = document.getElementById('chat-input');
    const sendButton = document.getElementById('chat-send-button');
    const historyDiv = document.getElementById('chat-history');
    const statusSpan = document.getElementById('chat-status');
    const consultationSelect = document.getElementById('consultation-type');
    const modelSelect = document.getElementById('selected-model');

    if (!input || !sendButton || !historyDiv || !statusSpan || !consultationSelect) return;

    const message = input.value.trim();
    if (!message) return;

    const welcome = document.getElementById('chat-welcome');
    if (welcome) welcome.remove();

    addChatMessage('user', message);

    input.value = '';
    input.disabled = true;
    sendButton.disabled = true;
    isChatting = true;
    statusSpan.textContent = '応答中...';

    const typingDiv = document.createElement('div');
    typingDiv.id = 'typing-indicator';
    typingDiv.className = 'flex items-start space-x-3 mb-4';
    typingDiv.innerHTML = `
        <div class="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center">
            <i class="fas fa-robot text-emerald-600 text-sm"></i>
        </div>
        <div class="flex-1 bg-white border border-slate-200 rounded-lg p-3 shadow-sm">
            <div class="flex space-x-1">
                <div class="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                <div class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                <div class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
            </div>
        </div>
    `;
    historyDiv.appendChild(typingDiv);
    historyDiv.scrollTop = historyDiv.scrollHeight;

    try {
        const body = {
            query: message,
            consultation_type: consultationSelect.value,
        };

        if (modelSelect && modelSelect.value) {
            body.model = modelSelect.value;
        }

        const response = await fetch('/api/consultation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });

        const data = await response.json();
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) typingIndicator.remove();

        addChatMessage('ai', data.advice, data);
        updateRelatedItems(data);
    } catch (error) {
        console.error('チャットエラー:', error);
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) typingIndicator.remove();
        addChatMessage('ai', '申し訳ございません。エラーが発生しました。もう一度お試しください。');
    } finally {
        input.disabled = false;
        sendButton.disabled = false;
        isChatting = false;
        statusSpan.textContent = '';
        input.focus();
    }
}

function addChatMessage(sender, message, data = null) {
    const historyDiv = document.getElementById('chat-history');
    if (!historyDiv) return;

    const timestamp = new Date().toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
    const wrapper = document.createElement('div');
    wrapper.className = 'flex items-start space-x-3 mb-4';

    if (sender === 'user') {
        wrapper.innerHTML = `
            <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <i class="fas fa-user text-blue-600 text-sm"></i>
            </div>
            <div class="flex-1 bg-blue-50 border border-blue-200 rounded-lg p-3">
                <div class="text-blue-900">${escapeHtml(message)}</div>
                <div class="text-xs text-blue-600 mt-1">${timestamp}</div>
            </div>
        `;
    } else {
        let responseHtml = `
            <div class="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center">
                <i class="fas fa-robot text-emerald-600 text-sm"></i>
            </div>
            <div class="flex-1 bg-white border border-slate-200 rounded-lg p-3 shadow-sm">
                <div class="text-slate-900 mb-2">${formatResponse(message)}</div>
        `;

        if (data && Array.isArray(data.related_documents) && data.related_documents.length > 0) {
            responseHtml += `
                <div class="mt-3 p-2 bg-slate-50 rounded border">
                    <div class="text-xs font-semibold text-slate-700 mb-1">関連文書 (${data.related_documents.length}件)</div>
                    <div class="space-y-1">
                        ${data.related_documents.slice(0, 3).map((doc) => `
                            <div class="text-xs text-slate-600">
                                <i class="fas fa-file-alt mr-1"></i>${escapeHtml(doc.title || doc.file_name || '')}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        if (data && Array.isArray(data.relevant_datasets) && data.relevant_datasets.length > 0) {
            responseHtml += `
                <div class="mt-3 p-2 bg-emerald-50 rounded border">
                    <div class="text-xs font-semibold text-emerald-700 mb-1">関連データセット (${data.relevant_datasets.length}件)</div>
                    <div class="space-y-1">
                        ${data.relevant_datasets.slice(0, 3).map((ds) => `
                            <div class="text-xs text-emerald-700">
                                <i class="fas fa-database mr-1"></i>${escapeHtml(ds.name || '')}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        responseHtml += `
                <div class="text-xs text-slate-500 mt-2">${timestamp}</div>
            </div>
        `;
        wrapper.innerHTML = responseHtml;
    }

    historyDiv.appendChild(wrapper);
    historyDiv.scrollTop = historyDiv.scrollHeight;
    chatHistory.push({ sender, message, timestamp, data });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function initializeMarkdown() {
    if (!marked) return;
    marked.setOptions({
        highlight(code, lang) {
            if (lang && hljs.getLanguage(lang)) {
                try {
                    return hljs.highlight(code, { language: lang }).value;
                } catch (err) {
                    console.error('Highlight error:', err);
                }
            }
            return hljs.highlightAuto(code).value;
        },
        breaks: true,
        gfm: true,
    });
}

function formatResponse(text) {
    try {
        const rawHtml = marked.parse(text);
        return `<div class="markdown-content">${DOMPurify.sanitize(rawHtml, {
            ALLOWED_TAGS: [
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                'p', 'br', 'strong', 'em', 'u', 's', 'del',
                'ul', 'ol', 'li',
                'a', 'code', 'pre',
                'blockquote', 'hr',
                'table', 'thead', 'tbody', 'tr', 'th', 'td',
                'div', 'span',
            ],
            ALLOWED_ATTR: ['href', 'title', 'class', 'id', 'target', 'rel'],
        })}</div>`;
    } catch (error) {
        console.error('Markdown rendering error:', error);
        return `<div class="markdown-content">${escapeHtml(text).replace(/\n/g, '<br>')}</div>`;
    }
}

function updateRelatedItems(data) {
    const section = document.getElementById('related-items-section');
    const content = document.getElementById('related-items-content');
    if (!section || !content) return;

    const hasDocs = data && Array.isArray(data.related_documents) && data.related_documents.length > 0;
    const hasDatasets = data && Array.isArray(data.relevant_datasets) && data.relevant_datasets.length > 0;

    if (!hasDocs && !hasDatasets) {
        section.classList.add('hidden');
        return;
    }

    let html = '';

    if (hasDocs) {
        html += '<div class="space-y-2">';
        html += '<h4 class="text-xs font-semibold text-slate-700 flex items-center gap-2"><i class="fas fa-file-alt text-emerald-500"></i>関連文書</h4>';
        html += data.related_documents.map((doc) => `
            <div class="bg-white border border-slate-200 rounded-md p-3 hover:shadow-sm transition-shadow">
                <div class="font-medium text-slate-800 text-sm">${escapeHtml(doc.title || doc.file_name || '')}</div>
                ${doc.authors ? `<div class="text-xs text-slate-500 mt-1">${escapeHtml(doc.authors)}</div>` : ''}
            </div>
        `).join('');
        html += '</div>';
    }

    if (hasDatasets) {
        html += '<div class="space-y-2 pt-3 border-t border-emerald-100">';
        html += '<h4 class="text-xs font-semibold text-slate-700 flex items-center gap-2"><i class="fas fa-database text-emerald-500"></i>関連データセット</h4>';
        html += data.relevant_datasets.map((ds) => `
            <div class="bg-white border border-slate-200 rounded-md p-3 hover:shadow-sm transition-shadow text-sm text-slate-700">
                ${escapeHtml(ds.name || '')} <span class="text-xs text-slate-400">(${ds.file_count || 0}ファイル)</span>
            </div>
        `).join('');
        html += '</div>';
    }

    content.innerHTML = html;
    section.classList.remove('hidden');
}

document.addEventListener('DOMContentLoaded', () => {
    initializeMarkdown();
    loadAvailableModels();
    updateSystemStatus();
    setInterval(updateSystemStatus, 60000);

    const sendButton = document.getElementById('chat-send-button');
    if (sendButton) {
        sendButton.addEventListener('click', sendChatMessage);
    }

    const modelSelect = document.getElementById('selected-model');
    if (modelSelect) {
        modelSelect.addEventListener('change', showModelDescription);
    }

    const modelInfoBtn = document.getElementById('model-info-btn');
    if (modelInfoBtn) {
        modelInfoBtn.addEventListener('click', toggleModelInfo);
    }
});
