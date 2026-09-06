-- ============================================================
-- CareerAI 数据库初始化脚本
-- 包含 pgvector 扩展启用与向量列补充
-- 业务表由 SQLAlchemy 自动创建（见 app/models）
-- ============================================================

-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 为 document_chunk 表补充向量列
ALTER TABLE document_chunk
    ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- 为 embedding 列创建 HNSW 向量索引
CREATE INDEX IF NOT EXISTS idx_document_chunk_embedding
    ON document_chunk USING hnsw (embedding vector_cosine_ops);

-- 创建管理员账号（密码: admin123，bcrypt 哈希）
INSERT INTO "user" (username, password_hash, email, role)
VALUES (
    'admin',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'admin@careerai.local',
    'admin'
)
ON CONFLICT (username) DO NOTHING;
