"""CareerAI Agent Service 入口。

复用 backend 镜像与代码（PYTHONPATH=/app），以独立进程运行 Agent worker。
后续可在此实现：
- 消费 Redis 队列中的 Agent 任务
- 运行 LangGraph Agent 工作流
- 异步处理耗时的简历解析、匹配分析、面试模拟等任务
"""

import asyncio
import logging

from loguru import logger

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    logger.info("CareerAI Agent Service 启动...")
    logger.info("Agent worker 占位运行中，等待任务实现...")
    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
