async function loadDatabaseSummary() {
    const container = document.getElementById('database-summary');
    const insights = document.getElementById('dataset-insights');
    if (!container) return;

    container.innerHTML = `
        <div class="flex items-center gap-3 text-slate-500">
            <i class="fas fa-spinner fa-spin"></i>
            <span>データベース概要を読み込んでいます...</span>
        </div>
    `;

    try {
        const response = await fetch('/api/database/summary');
        if (!response.ok) {
            throw new Error(`status ${response.status}`);
        }
        const data = await response.json();

        const majorDatasets = (data.datasets.items || []).slice(0, 5);

        let html = `
            <div class="grid gap-6 lg:grid-cols-2">
                <div class="space-y-4">
                    <h3 class="text-base font-semibold text-slate-700 flex items-center gap-2">
                        <i class="fas fa-layer-group text-indigo-500"></i>
                        主要データセット
                    </h3>
        `;

        if (majorDatasets.length === 0) {
            html += `
                <p class="text-sm text-slate-500">登録済みのデータセットがありません。Google Drive同期ページから取り込みを行ってください。</p>
            `;
        } else {
            html += '<div class="space-y-3">';
            majorDatasets.forEach((ds) => {
                html += `
                    <div class="border border-slate-200 rounded-lg p-4 hover:border-emerald-300 transition-colors">
                        <div class="flex items-start justify-between gap-4">
                            <div>
                                <p class="font-semibold text-slate-800">${ds.name || '名称未設定'}</p>
                                <p class="text-xs text-slate-500 mt-1">${ds.file_count || 0}ファイル / ${Number(ds.total_size_mb || 0).toLocaleString()} MB</p>
                                ${ds.summary ? `<p class="text-sm text-slate-600 mt-2">${ds.summary}</p>` : ''}
                            </div>
                            ${ds.drive_url ? `<a href="${ds.drive_url}" target="_blank" class="text-xs text-emerald-600 hover:text-emerald-700">Driveを開く</a>` : ''}
                        </div>
                    </div>
                `;
            });
            html += '</div>';
        }

        html += `
                </div>
                <div class="space-y-4">
                    <h3 class="text-base font-semibold text-slate-700 flex items-center gap-2">
                        <i class="fas fa-arrow-trend-up text-emerald-500"></i>
                        集計情報
                    </h3>
                    <div class="grid gap-4">
                        <div class="bg-slate-50 border border-slate-200 rounded-lg p-4">
                            <p class="text-xs text-slate-500">総登録数</p>
                            <p class="text-2xl font-semibold text-slate-800">${data.totals.total_items || 0}</p>
                            <p class="text-xs text-slate-500 mt-1">論文 ${data.totals.papers || 0} / ポスター ${data.totals.posters || 0} / データセット ${data.totals.datasets || 0}</p>
                        </div>
                        <div class="bg-slate-50 border border-slate-200 rounded-lg p-4">
                            <p class="text-xs text-slate-500">データセット内ファイル数</p>
                            <p class="text-2xl font-semibold text-slate-800">${(data.totals.total_dataset_files || 0).toLocaleString()}</p>
                            <p class="text-xs text-slate-500 mt-1">総容量 ${(data.totals.total_dataset_size_mb || 0).toLocaleString()} MB</p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = html;

        if (insights) {
            if (majorDatasets.length === 0) {
                insights.innerHTML = '<p>データセットがまだありません。Google Drive同期ページから追加しましょう。</p>';
            } else {
                const largest = [...majorDatasets].sort((a, b) => (b.total_size || 0) - (a.total_size || 0))[0];
                const mostFiles = [...majorDatasets].sort((a, b) => (b.file_count || 0) - (a.file_count || 0))[0];

                const insightItems = [];

                if (largest) {
                    insightItems.push(`総容量が最も大きいデータセットは <span class="font-semibold text-slate-800">${largest.name}</span>（${Number(largest.total_size_mb || 0).toLocaleString()} MB）です。`);
                }
                if (mostFiles && mostFiles.id !== (largest && largest.id)) {
                    insightItems.push(`ファイル数が最も多いデータセットは <span class="font-semibold text-slate-800">${mostFiles.name}</span>（${(mostFiles.file_count || 0).toLocaleString()} ファイル）です。`);
                }
                insightItems.push(`論文 ${data.totals.papers || 0} 件 / ポスター ${data.totals.posters || 0} 件の情報が登録されています。`);

                insights.innerHTML = `
                    <ul class="space-y-2">
                        ${insightItems.map((item) => `<li class="flex items-start gap-2"><i class="fas fa-circle text-[6px] text-slate-400 mt-2"></i><span>${item}</span></li>`).join('')}
                    </ul>
                `;
            }
        }
    } catch (error) {
        console.error('データベース概要の取得に失敗しました:', error);
        container.innerHTML = `
            <div class="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
                <i class="fas fa-triangle-exclamation mr-2"></i>
                データベース概要の取得に失敗しました。しばらくしてから再度お試しください。
            </div>
        `;
        if (insights) {
            insights.innerHTML = '<p class="text-red-500">データセット情報を取得できませんでした。</p>';
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadDatabaseSummary();
    const refreshButton = document.getElementById('refresh-summary');
    if (refreshButton) {
        refreshButton.addEventListener('click', () => {
            loadDatabaseSummary();
        });
    }
});
