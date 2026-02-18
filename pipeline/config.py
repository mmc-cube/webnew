"""全局配置"""

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    dashscope_api_key: str = ""
    github_token: str = ""

    # Web3 关键词
    web3_keywords: list = field(default_factory=lambda: [
        "airdrop", "points", "testnet", "quest",
        "galxe", "zealy", "layer3", "polymarket",
    ])

    # 主题列表
    themes: list = field(default_factory=lambda: [
        "Coding Agents",
        "IDE / Copilot Tools",
        "Workflow Automation",
        "Model Releases & Updates",
        "Tooling / Infra",
        "Evaluation / Evals",
        "RAG / Retrieval",
        "Demos / New Apps",
    ])

    # 输出路径
    output_dir: str = "output"
    data_dir: str = "data"

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY", ""),
            github_token=os.getenv("GITHUB_TOKEN", ""),
            output_dir=os.getenv("OUTPUT_DIR", "output"),
            data_dir=os.getenv("DATA_DIR", "data"),
        )
