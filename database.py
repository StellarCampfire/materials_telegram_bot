import sqlite3
from typing import List, Dict, Optional
from material import Material

class Database:
    def __init__(self, db_path: str = "materials.db"):
        """Инициализация подключения к базе данных"""
        self.db_path = db_path
        self._create_table()

    def _create_table(self) -> None:
        """Создание таблицы materials, если она не существует"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS materials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    img_link TEXT NOT NULL,
                    demo_file_link TEXT NOT NULL,
                    full_file_link TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    is_active BOOL NOT NULL
                )
            """)
            conn.commit()

    def get_material_by_id(self, material_id: int) -> Optional[Dict]:
        """Получение материала по ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM materials WHERE id = ? AND is_active = true", (material_id,))
            row = cursor.fetchone()
            if row:
                return Material(row["id"], row["title"], row["img_link"], row["demo_file_link"], row["full_file_link"], row["price"])
            return None

    def get_all_materials(self) -> List[Dict]:
        """Получение всех материалов"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM materials")
            rows = cursor.fetchall()
            return [
                Material(row["id"], row["title"], row["img_link"], row["demo_file_link"], row["full_file_link"], row["price"])
            for row in rows]