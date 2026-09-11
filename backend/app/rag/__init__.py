"""RAG 知识库模块。

流程：原始文档 → 文档解析 → Chunk 切分 → Embedding → 向量存储(pgvector)
      → 相似度检索 → 构建上下文 → LLM 生成回答

子模块：
- chunker.py: 文本切分（RecursiveCharacterTextSplitter，Size/Overlap 可配置）
- embedder.py: 向量化（百炼 text-embedding-v3，OpenAI 兼容接口）
- retriever.py: pgvector 余弦距离 TopK 检索
"""
