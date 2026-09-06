"""RAG 知识库模块。

流程：原始文档 → 文档解析 → Chunk 切分 → Embedding → 向量存储(pgvector)
      → 相似度检索 → 构建上下文 → LLM 生成回答

本目录为占位结构，后续实现：
- document_loader.py: PDF/Word/Markdown/TXT 解析
- text_splitter.py: Chunk 切分（Chunk Size / Overlap 可配置）
- embedding.py: 调用 DeepSeek Embedding API
- vector_store.py: pgvector 向量存储
- retriever.py: 相似度检索（TopK / 阈值可配置）
"""
