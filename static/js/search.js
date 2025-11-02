function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text == null ? '' : String(text);
    return div.innerHTML;
}

function createTypeBadge(type) {
    const map = {
        paper: { icon: 'fa-file-alt', color: 'text-blue-500', label: '論文' },
        poster: { icon: 'fa-image', color: 'text-emerald-500', label: 'ポスター' },
        dataset: { icon: 'fa-database', color: 'text-purple-500', label: 'データセット' },
    };
    const config = map[type] || map.paper;
    const wrapper = document.createElement('span');
    wrapper.className = `inline-flex items-center gap-2 text-xs font-semibold ${config.color}`;
    wrapper.innerHTML = `<i class="fas ${config.icon}"></i>${config.label}`;
    return wrapper;
}

function createResultCard(item) {
    const card = document.createElement('div');
    card.className = 'border border-slate-200 rounded-lg p-5 hover:border-emerald-300 transition-colors';

    const header = document.createElement('div');
    header.className = 'flex items-start justify-between gap-4';

    const titleBlock = document.createElement('div');
    titleBlock.className = 'space-y-2';

    const titleRow = document.createElement('div');
    titleRow.className = 'flex items-center gap-3';
    titleRow.appendChild(createTypeBadge(item.type));

    const title = document.createElement('h3');
    title.className = 'text-lg font-semibold text-slate-800';
    title.textContent = item.title || item.name || item.file_name || '名称未設定';
    titleRow.appendChild(title);

    titleBlock.appendChild(titleRow);

    if (item.authors) {
        const authors = document.createElement('p');
        authors.className = 'text-xs text-slate-500';
        authors.textContent = `著者: ${item.authors}`;
        titleBlock.appendChild(authors);
    }

    if (item.abstract || item.description) {
        const summary = document.createElement('p');
        summary.className = 'text-sm text-slate-600';
        summary.textContent = (item.abstract || item.description).slice(0, 120) + ((item.abstract || item.description).length > 120 ? '…' : '');
        titleBlock.appendChild(summary);
    }

    const meta = document.createElement('div');
    meta.className = 'flex flex-col items-end gap-2 text-xs text-slate-500';

    if (item.file_size) {
        const size = document.createElement('span');
        size.textContent = `${(item.file_size / 1024).toFixed(1)} KB`;
        meta.appendChild(size);
    }

    if (item.file_count) {
        const files = document.createElement('span');
        files.textContent = `${item.file_count} ファイル`;
        meta.appendChild(files);
    }

    const actions = document.createElement('div');
    actions.className = 'flex gap-2';

    if (item.drive_url) {
        const driveLink = document.createElement('a');
        driveLink.href = item.drive_url;
        driveLink.target = '_blank';
        driveLink.rel = 'noopener';
        driveLink.className = 'inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-xs bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors';
        driveLink.innerHTML = '<i class="fab fa-google-drive"></i>Driveを開く';
        actions.appendChild(driveLink);
    }

    if (item.type === 'dataset') {
        const detailBtn = document.createElement('button');
        detailBtn.type = 'button';
        detailBtn.className = 'inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-xs bg-purple-50 text-purple-600 hover:bg-purple-100 transition-colors';
        detailBtn.innerHTML = '<i class="fas fa-search"></i>詳細';
        detailBtn.addEventListener('click', () => openDatasetDetail(item.id));
        actions.appendChild(detailBtn);
    }

    if (actions.children.length > 0) {
        meta.appendChild(actions);
    }

    header.appendChild(titleBlock);
    header.appendChild(meta);
    card.appendChild(header);
    return card;
}

async function searchData() {
    const queryInput = document.getElementById('search-query');
    const typeSelect = document.getElementById('search-type');
    const resultsDiv = document.getElementById('search-results');
    if (!queryInput || !typeSelect || !resultsDiv) return;

    const query = queryInput.value.trim();
    if (!query) {
        resultsDiv.innerHTML = '<p class="text-slate-500">検索キーワードを入力してください。</p>';
        queryInput.focus();
        return;
    }

    resultsDiv.innerHTML = `
        <div class="flex items-center gap-3 text-slate-500">
            <i class="fas fa-spinner fa-spin"></i>
            <span>検索中です...</span>
        </div>
    `;

    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, search_type: typeSelect.value }),
        });
        const data = await response.json();

        if (!Array.isArray(data.results) || data.results.length === 0) {
            resultsDiv.innerHTML = `<p class="text-slate-500">"${escapeHtml(query)}" に該当する結果は見つかりませんでした。</p>`;
            return;
        }

        const fragment = document.createDocumentFragment();
        const summary = document.createElement('p');
        summary.className = 'text-sm text-slate-500';
        summary.innerHTML = `<span class="font-semibold text-slate-700">${data.total}</span> 件の結果が見つかりました。`;
        fragment.appendChild(summary);

        data.results.forEach((item) => {
            fragment.appendChild(createResultCard(item));
        });

        resultsDiv.innerHTML = '';
        resultsDiv.appendChild(fragment);
    } catch (error) {
        console.error('検索エラー:', error);
        resultsDiv.innerHTML = `
            <div class="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
                <i class="fas fa-triangle-exclamation mr-2"></i>
                検索中にエラーが発生しました。しばらくしてから再度お試しください。
            </div>
        `;
    }
}

async function openDatasetDetail(datasetId) {
    const modal = document.getElementById('dataset-detail-modal');
    if (!modal) return;

    modal.classList.remove('hidden');
    modal.classList.add('flex');

    try {
        const response = await fetch(`/api/datasets/${datasetId}`);
        const data = await response.json();

        if (!data.success) {
            throw new Error('dataset detail failed');
        }

        const { dataset, files, citing_papers: citingPapers, citing_posters: citingPosters } = data;

        document.getElementById('dataset-name').textContent = dataset.name || '名称未設定';
        document.getElementById('dataset-file-count').textContent = dataset.file_count || 0;
        document.getElementById('dataset-total-size').textContent = dataset.total_size_mb || 0;
        document.getElementById('dataset-description').textContent = dataset.description || '説明は登録されていません。';

        const summarySection = document.getElementById('dataset-summary-section');
        if (dataset.summary) {
            document.getElementById('dataset-summary').textContent = dataset.summary;
            summarySection.classList.remove('hidden');
        } else {
            summarySection.classList.add('hidden');
        }

        const driveLinkSection = document.getElementById('dataset-drive-link-section');
        const driveLink = document.getElementById('dataset-drive-link');
        if (dataset.drive_url) {
            driveLink.href = dataset.drive_url;
            driveLinkSection.classList.remove('hidden');
        } else {
            driveLinkSection.classList.add('hidden');
        }

        const updated = document.getElementById('dataset-updated');
        if (updated) {
            updated.textContent = dataset.updated_at ? new Date(dataset.updated_at).toLocaleString('ja-JP') : '-';
        }

        const filesList = document.getElementById('dataset-files-list');
        filesList.innerHTML = '';

        files.forEach((file) => {
            const item = document.createElement('div');
            item.className = 'bg-white border border-slate-200 rounded-lg p-4 flex flex-col gap-3 hover:border-emerald-300 transition-colors';

            const header = document.createElement('div');
            header.className = 'flex items-center justify-between gap-4';

            const fileMeta = document.createElement('div');
            fileMeta.innerHTML = `
                <div class="font-medium text-slate-800 flex items-center gap-2">
                    <i class="fas ${file.file_type === 'csv' ? 'fa-file-csv text-emerald-500' : file.file_type === 'json' || file.file_type === 'jsonl' ? 'fa-file-code text-blue-500' : 'fa-file text-slate-400'} text-lg"></i>
                    ${escapeHtml(file.file_name)}
                </div>
                <div class="text-xs text-slate-500 ml-6 mt-1">
                    ${file.file_size_mb || 0} MB / ${file.file_type ? file.file_type.toUpperCase() : '-'}
                </div>
            `;

            header.appendChild(fileMeta);

            const actionGroup = document.createElement('div');
            actionGroup.className = 'flex items-center gap-2';

            if (file.drive_url) {
                const openLink = document.createElement('a');
                openLink.href = file.drive_url;
                openLink.target = '_blank';
                openLink.rel = 'noopener';
                openLink.className = 'px-3 py-1.5 text-xs bg-blue-50 text-blue-600 rounded-md hover:bg-blue-100 transition-colors';
                openLink.innerHTML = '<i class="fab fa-google-drive mr-1"></i>開く';
                actionGroup.appendChild(openLink);
            }

            if (['csv', 'json', 'jsonl'].includes(file.file_type)) {
                const previewBtn = document.createElement('button');
                previewBtn.type = 'button';
                previewBtn.className = 'px-3 py-1.5 text-xs bg-purple-50 text-purple-600 rounded-md hover:bg-purple-100 transition-colors';
                previewBtn.innerHTML = '<i class="fas fa-eye mr-1"></i>プレビュー';
                previewBtn.addEventListener('click', () => loadFilePreview(datasetId, file.id, file.file_name));
                actionGroup.appendChild(previewBtn);
            }

            header.appendChild(actionGroup);
            item.appendChild(header);

            if (file.summary) {
                const summary = document.createElement('p');
                summary.className = 'text-sm text-slate-600 ml-6';
                summary.textContent = file.summary;
                item.appendChild(summary);
            }

            filesList.appendChild(item);
        });

        const citingSection = document.getElementById('citing-docs-section');
        const citingPapersSection = document.getElementById('citing-papers-section');
        const citingPostersSection = document.getElementById('citing-posters-section');

        if ((citingPapers && citingPapers.length) || (citingPosters && citingPosters.length)) {
            citingSection.classList.remove('hidden');
            if (citingPapers && citingPapers.length) {
                citingPapersSection.classList.remove('hidden');
                const list = document.getElementById('citing-papers-list');
                list.innerHTML = '';
                citingPapers.forEach((paper) => {
                    const item = document.createElement('div');
                    item.className = 'bg-blue-50 border border-blue-200 rounded p-3';
                    item.innerHTML = `
                        <div class="font-medium text-slate-800">${escapeHtml(paper.title || paper.file_name || '')}</div>
                        ${paper.authors ? `<div class="text-xs text-slate-500 mt-1">著者: ${escapeHtml(paper.authors)}</div>` : ''}
                    `;
                    list.appendChild(item);
                });
            } else {
                citingPapersSection.classList.add('hidden');
            }

            if (citingPosters && citingPosters.length) {
                citingPostersSection.classList.remove('hidden');
                const list = document.getElementById('citing-posters-list');
                list.innerHTML = '';
                citingPosters.forEach((poster) => {
                    const item = document.createElement('div');
                    item.className = 'bg-emerald-50 border border-emerald-200 rounded p-3';
                    item.innerHTML = `
                        <div class="font-medium text-slate-800">${escapeHtml(poster.title || poster.file_name || '')}</div>
                        ${poster.authors ? `<div class="text-xs text-slate-500 mt-1">著者: ${escapeHtml(poster.authors)}</div>` : ''}
                    `;
                    list.appendChild(item);
                });
            } else {
                citingPostersSection.classList.add('hidden');
            }
        } else {
            citingSection.classList.add('hidden');
        }

        document.getElementById('data-preview-section').classList.add('hidden');
        document.getElementById('dataset-stats-summary').classList.add('hidden');
        document.getElementById('preview-table-body').innerHTML = '';
        document.getElementById('preview-table').querySelector('thead').innerHTML = '';
        document.getElementById('preview-error').classList.add('hidden');
        document.getElementById('preview-table-container').classList.add('hidden');
        document.getElementById('preview-loading').classList.add('hidden');
    } catch (error) {
        console.error('データセット詳細の取得に失敗:', error);
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        alert('データセット詳細の取得に失敗しました');
    }
}

async function loadFilePreview(datasetId, fileId, fileName) {
    const previewSection = document.getElementById('data-preview-section');
    const previewLoading = document.getElementById('preview-loading');
    const previewContainer = document.getElementById('preview-table-container');
    const previewError = document.getElementById('preview-error');
    const previewFileNameSpan = document.getElementById('preview-file-name');
    const summarySection = document.getElementById('dataset-stats-summary');
    const rowCount = document.getElementById('preview-row-count');

    if (!previewSection || !previewLoading || !previewContainer || !previewError || !previewFileNameSpan || !summarySection || !rowCount) {
        return;
    }

    previewSection.classList.remove('hidden');
    previewLoading.classList.remove('hidden');
    previewContainer.classList.add('hidden');
    previewError.classList.add('hidden');
    summarySection.classList.add('hidden');
    previewFileNameSpan.textContent = fileName || '';
    previewSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    try {
        const response = await fetch(`/api/datasets/${datasetId}/files/${fileId}/preview?rows=100`);
        const data = await response.json();
        if (!data.success) {
            throw new Error('preview failed');
        }

        const { preview } = data;
        const table = document.getElementById('preview-table');
        const thead = table.querySelector('thead');
        const tbody = document.getElementById('preview-table-body');

        thead.innerHTML = '';
        tbody.innerHTML = '';

        if (preview.columns && preview.columns.length) {
            const headerRow = document.createElement('tr');
            preview.columns.forEach((col) => {
                const th = document.createElement('th');
                th.className = 'px-4 py-3 text-left text-xs font-semibold text-slate-600 bg-slate-50';
                th.textContent = col;
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);
        }

        if (preview.rows && preview.rows.length) {
            preview.rows.forEach((row, idx) => {
                const tr = document.createElement('tr');
                tr.className = idx % 2 === 0 ? 'bg-white' : 'bg-slate-50';
                preview.columns.forEach((col) => {
                    const td = document.createElement('td');
                    td.className = 'px-4 py-2 text-sm text-slate-700';
                    const value = row[col];
                    td.textContent = value === null || value === undefined ? '' : String(value);
                    tr.appendChild(td);
                });
                tbody.appendChild(tr);
            });
            rowCount.textContent = preview.rows.length;
        }

        if (preview.statistics) {
            const statsText = document.getElementById('stats-summary-text');
            const colCount = Object.keys(preview.statistics).length;
            const totalRows = preview.total_rows || (preview.rows ? preview.rows.length : 0);
            statsText.textContent = `${totalRows.toLocaleString()} rows × ${colCount} columns`;
            summarySection.classList.remove('hidden');
        }

        previewLoading.classList.add('hidden');
        previewContainer.classList.remove('hidden');
    } catch (error) {
        console.error('File preview error:', error);
        previewLoading.classList.add('hidden');
        previewError.classList.remove('hidden');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const searchButton = document.getElementById('search-button');
    const queryInput = document.getElementById('search-query');
    const modal = document.getElementById('dataset-detail-modal');
    const closeModal = document.getElementById('close-dataset-modal');

    if (searchButton) {
        searchButton.addEventListener('click', () => searchData());
    }
    if (queryInput) {
        queryInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                searchData();
            }
        });
    }

    if (modal) {
        modal.addEventListener('click', (event) => {
            if (event.target === modal) {
                modal.classList.add('hidden');
                modal.classList.remove('flex');
            }
        });
    }

    if (closeModal) {
        closeModal.addEventListener('click', () => {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        });
    }
});
