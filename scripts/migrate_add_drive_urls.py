"""
データベースマイグレーション: drive_url フィールドを追加
"""
import sqlite3
import logging
from tools.config import DATABASE_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_add_drive_urls():
    """既存のテーブルに drive_url カラムを追加"""
    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.cursor()

    try:
        # datasetsテーブルにカラムを追加
        logger.info("Adding drive_folder_id and drive_url to datasets table...")
        try:
            cursor.execute("ALTER TABLE datasets ADD COLUMN drive_folder_id TEXT")
            cursor.execute("ALTER TABLE datasets ADD COLUMN drive_url TEXT")
            logger.info("✓ datasets table updated")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                logger.info("✓ datasets table already has drive_url columns")
            else:
                raise

        # papersテーブルにカラムを追加
        logger.info("Adding drive_file_id and drive_url to papers table...")
        try:
            cursor.execute("ALTER TABLE papers ADD COLUMN drive_file_id TEXT")
            cursor.execute("ALTER TABLE papers ADD COLUMN drive_url TEXT")
            logger.info("✓ papers table updated")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                logger.info("✓ papers table already has drive_url columns")
            else:
                raise

        # postersテーブルにカラムを追加
        logger.info("Adding drive_file_id and drive_url to posters table...")
        try:
            cursor.execute("ALTER TABLE posters ADD COLUMN drive_file_id TEXT")
            cursor.execute("ALTER TABLE posters ADD COLUMN drive_url TEXT")
            logger.info("✓ posters table updated")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                logger.info("✓ posters table already has drive_url columns")
            else:
                raise

        # dataset_filesテーブルにカラムを追加
        logger.info("Adding drive_file_id and drive_url to dataset_files table...")
        try:
            cursor.execute("ALTER TABLE dataset_files ADD COLUMN drive_file_id TEXT")
            cursor.execute("ALTER TABLE dataset_files ADD COLUMN drive_url TEXT")
            logger.info("✓ dataset_files table updated")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                logger.info("✓ dataset_files table already has drive_url columns")
            else:
                raise

        conn.commit()
        logger.info("Migration completed successfully!")

        # 既存データのfile_pathからdrive_file_idとdrive_urlを生成
        logger.info("Updating existing records with drive URLs...")

        # papers
        cursor.execute("SELECT id, file_path FROM papers WHERE drive_file_id IS NULL")
        papers = cursor.fetchall()
        for paper_id, file_path in papers:
            if file_path and file_path.startswith("gdrive://"):
                # gdrive://paper/{file_id} -> file_id を抽出
                parts = file_path.split("/")
                if len(parts) >= 3:
                    file_id = parts[-1]
                    drive_url = f"https://drive.google.com/file/d/{file_id}/view"
                    cursor.execute(
                        "UPDATE papers SET drive_file_id = ?, drive_url = ? WHERE id = ?",
                        (file_id, drive_url, paper_id)
                    )

        # posters
        cursor.execute("SELECT id, file_path FROM posters WHERE drive_file_id IS NULL")
        posters = cursor.fetchall()
        for poster_id, file_path in posters:
            if file_path and file_path.startswith("gdrive://"):
                parts = file_path.split("/")
                if len(parts) >= 3:
                    file_id = parts[-1]
                    drive_url = f"https://drive.google.com/file/d/{file_id}/view"
                    cursor.execute(
                        "UPDATE posters SET drive_file_id = ?, drive_url = ? WHERE id = ?",
                        (file_id, drive_url, poster_id)
                    )

        # dataset_files
        cursor.execute("SELECT id, file_path FROM dataset_files WHERE drive_file_id IS NULL")
        dataset_files = cursor.fetchall()
        for file_id_rec, file_path in dataset_files:
            if file_path and file_path.startswith("gdrive://"):
                parts = file_path.split("/")
                if len(parts) >= 4:
                    file_id = parts[-1]
                    drive_url = f"https://drive.google.com/file/d/{file_id}/view"
                    cursor.execute(
                        "UPDATE dataset_files SET drive_file_id = ?, drive_url = ? WHERE id = ?",
                        (file_id, drive_url, file_id_rec)
                    )

        conn.commit()
        logger.info("✓ Existing records updated with drive URLs")

    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_add_drive_urls()
