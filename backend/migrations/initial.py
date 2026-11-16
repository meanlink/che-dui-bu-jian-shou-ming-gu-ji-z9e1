from sqlalchemy import inspect, text
from src.config.database import Base, engine
from src import models
# 既有库补列：create_all 只建缺失的表，不会为已存在的表加列
PATCHES = {
    'reports': [
        ('recipient_ids', "JSON DEFAULT '[]'"),
        ('sign_deadline_seconds', 'INTEGER DEFAULT 86400'),
        ('supervisor_id', 'INTEGER'),
    ],
    'deliveries': [('settled_at', 'DOUBLE PRECISION')],
}
def migrate():
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        for table, columns in PATCHES.items():
            existing = {c['name'] for c in inspect(conn).get_columns(table)}
            for name, ddl in columns:
                if name not in existing:
                    conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {name} {ddl}'))
        conn.execute(text("UPDATE reports SET recipient_ids='[]' WHERE recipient_ids IS NULL"))
        conn.execute(text('UPDATE reports SET sign_deadline_seconds=86400 WHERE sign_deadline_seconds IS NULL'))
if __name__ == '__main__':
    migrate()
