"""
ベクトルインデックス作成・管理機能
データベースの全データをベクトル化してChromaDBにインデックス
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..database.new_repository import DatasetRepository, PaperRepository, PosterRepository, DatasetFileRepository
from .vector_search import VectorSearchEngine

logger = logging.getLogger(__name__)


class VectorIndexer:
    """ベクトルインデックス作成・管理クラス"""

    def __init__(self):
        self.dataset_repo = DatasetRepository()
        self.paper_repo = PaperRepository()
        self.poster_repo = PosterRepository()
        self.dataset_file_repo = DatasetFileRepository()
        self.vector_engine = VectorSearchEngine()

    def index_all_documents(self) -> Dict[str, Any]:
        """全ドキュメントをインデックス化"""
        if not self.vector_engine.is_enabled():
            logger.error("Vector search engine is not enabled")
            return {
                'success': False,
                'error': 'Vector search engine is not enabled',
                'indexed_count': 0
            }

        logger.info("Starting full document indexing...")

        indexed_count = 0
        errors = []

        # 論文をインデックス化
        papers = self.paper_repo.find_all()
        logger.info(f"Indexing {len(papers)} papers...")
        for paper in papers:
            try:
                doc_text = self._build_paper_text(paper)
                metadata = {
                    'type': 'paper',
                    'id': paper.id,
                    'title': paper.title or '',
                    'authors': paper.authors or '',
                    'file_name': paper.file_name
                }

                doc_id = f"paper_{paper.id}"
                if self.vector_engine.add_document(doc_id, doc_text, metadata):
                    indexed_count += 1
                else:
                    errors.append(f"Failed to index paper {paper.id}")

            except Exception as e:
                logger.error(f"Error indexing paper {paper.id}: {e}")
                errors.append(f"Paper {paper.id}: {str(e)}")

        # ポスターをインデックス化
        posters = self.poster_repo.find_all()
        logger.info(f"Indexing {len(posters)} posters...")
        for poster in posters:
            try:
                doc_text = self._build_poster_text(poster)
                metadata = {
                    'type': 'poster',
                    'id': poster.id,
                    'title': poster.title or '',
                    'authors': poster.authors or '',
                    'file_name': poster.file_name
                }

                doc_id = f"poster_{poster.id}"
                if self.vector_engine.add_document(doc_id, doc_text, metadata):
                    indexed_count += 1
                else:
                    errors.append(f"Failed to index poster {poster.id}")

            except Exception as e:
                logger.error(f"Error indexing poster {poster.id}: {e}")
                errors.append(f"Poster {poster.id}: {str(e)}")

        # データセットをインデックス化
        datasets = self.dataset_repo.find_all()
        logger.info(f"Indexing {len(datasets)} datasets...")
        for dataset in datasets:
            try:
                doc_text = self._build_dataset_text(dataset)
                metadata = {
                    'type': 'dataset',
                    'id': dataset.id,
                    'name': dataset.name,
                    'file_count': dataset.file_count,
                    'description': dataset.description or ''
                }

                doc_id = f"dataset_{dataset.id}"
                if self.vector_engine.add_document(doc_id, doc_text, metadata):
                    indexed_count += 1
                else:
                    errors.append(f"Failed to index dataset {dataset.id}")

            except Exception as e:
                logger.error(f"Error indexing dataset {dataset.id}: {e}")
                errors.append(f"Dataset {dataset.id}: {str(e)}")

        logger.info(f"Indexing completed. Indexed {indexed_count} documents with {len(errors)} errors")

        return {
            'success': True,
            'indexed_count': indexed_count,
            'total_papers': len(papers),
            'total_posters': len(posters),
            'total_datasets': len(datasets),
            'errors': errors,
            'timestamp': datetime.now().isoformat()
        }

    def index_single_document(self, doc_type: str, doc_id: int) -> bool:
        """単一ドキュメントをインデックス化"""
        if not self.vector_engine.is_enabled():
            logger.error("Vector search engine is not enabled")
            return False

        try:
            if doc_type == 'paper':
                paper = self.paper_repo.find_by_id(doc_id)
                if not paper:
                    logger.error(f"Paper {doc_id} not found")
                    return False

                doc_text = self._build_paper_text(paper)
                metadata = {
                    'type': 'paper',
                    'id': paper.id,
                    'title': paper.title or '',
                    'authors': paper.authors or '',
                    'file_name': paper.file_name
                }
                vector_id = f"paper_{paper.id}"

            elif doc_type == 'poster':
                poster = self.poster_repo.find_by_id(doc_id)
                if not poster:
                    logger.error(f"Poster {doc_id} not found")
                    return False

                doc_text = self._build_poster_text(poster)
                metadata = {
                    'type': 'poster',
                    'id': poster.id,
                    'title': poster.title or '',
                    'authors': poster.authors or '',
                    'file_name': poster.file_name
                }
                vector_id = f"poster_{poster.id}"

            elif doc_type == 'dataset':
                dataset = self.dataset_repo.find_by_id(doc_id)
                if not dataset:
                    logger.error(f"Dataset {doc_id} not found")
                    return False

                doc_text = self._build_dataset_text(dataset)
                metadata = {
                    'type': 'dataset',
                    'id': dataset.id,
                    'name': dataset.name,
                    'file_count': dataset.file_count,
                    'description': dataset.description or ''
                }
                vector_id = f"dataset_{dataset.id}"

            else:
                logger.error(f"Unknown document type: {doc_type}")
                return False

            return self.vector_engine.add_document(vector_id, doc_text, metadata)

        except Exception as e:
            logger.error(f"Error indexing {doc_type} {doc_id}: {e}")
            return False

    def _build_paper_text(self, paper) -> str:
        """論文の検索用テキストを構築"""
        parts = []

        if paper.title:
            parts.append(f"Title: {paper.title}")
        if paper.authors:
            parts.append(f"Authors: {paper.authors}")
        if paper.abstract:
            parts.append(f"Abstract: {paper.abstract}")
        if paper.keywords:
            parts.append(f"Keywords: {paper.keywords}")

        parts.append(f"File: {paper.file_name}")

        return "\n".join(parts)

    def _build_poster_text(self, poster) -> str:
        """ポスターの検索用テキストを構築"""
        parts = []

        if poster.title:
            parts.append(f"Title: {poster.title}")
        if poster.authors:
            parts.append(f"Authors: {poster.authors}")
        if poster.abstract:
            parts.append(f"Abstract: {poster.abstract}")
        if poster.keywords:
            parts.append(f"Keywords: {poster.keywords}")

        parts.append(f"File: {poster.file_name}")

        return "\n".join(parts)

    def _build_dataset_text(self, dataset) -> str:
        """データセットの検索用テキストを構築"""
        parts = []

        parts.append(f"Dataset Name: {dataset.name}")

        if dataset.description:
            parts.append(f"Description: {dataset.description}")

        if dataset.summary:
            parts.append(f"Summary: {dataset.summary}")

        parts.append(f"File Count: {dataset.file_count}")

        # データセット内のファイル情報も含める
        files = self.dataset_file_repo.find_by_dataset_id(dataset.id)
        if files:
            file_names = [f.file_name for f in files[:10]]  # 最大10ファイル
            parts.append(f"Files: {', '.join(file_names)}")

        return "\n".join(parts)

    def get_index_stats(self) -> Dict[str, Any]:
        """インデックスの統計情報を取得"""
        if not self.vector_engine.is_enabled():
            return {
                'enabled': False,
                'provider': self.vector_engine.provider,
                'error': 'Vector search is not enabled'
            }

        return {
            'enabled': True,
            'provider': self.vector_engine.provider,
            'embedding_model': self.vector_engine.embedding_model_name,
            'vector_dimension': self.vector_engine.vector_dimension
        }
