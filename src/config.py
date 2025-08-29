"""
Configuration for Daily Intelligence Briefing System
"""
import os
from pathlib import Path
from datetime import datetime, timedelta
import json

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
CACHE_DIR = BASE_DIR / "cache"
DB_PATH = DATA_DIR / "intelligence.db"

# Ensure directories exist
for dir_path in [DATA_DIR, REPORTS_DIR, CACHE_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# API Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")  # Optional, increases rate limits
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")

# Time configuration
REPORT_GENERATION_TIME = "04:30"  # 4:30 AM
REPORT_READY_TIME = "05:00"  # 5:00 AM
TIMEZONE = "America/New_York"  # Adjust as needed

# Cache configuration
CACHE_EXPIRY_HOURS = 6  # Re-fetch data after 6 hours
MAX_CACHE_SIZE_MB = 100

# Data sources configuration
DATA_SOURCES = {
    "github_repos": [
        {"owner": "anthropics", "repo": "anthropic-sdk-python"},
        {"owner": "anthropics", "repo": "anthropic-sdk-typescript"},
        {"owner": "anthropics", "repo": "courses"},
        {"owner": "openai", "repo": "openai-python"},
        {"owner": "openai", "repo": "openai-node"},
        {"owner": "google", "repo": "generative-ai-python"},
        {"owner": "google", "repo": "generative-ai-js"},
        {"owner": "microsoft", "repo": "vscode"},
        {"owner": "modelcontextprotocol", "repo": "servers"},
    ],
    "npm_packages": [
        "@anthropic-ai/sdk",
        "@modelcontextprotocol/sdk",
        "openai",
        "@google-ai/generativelanguage",
    ],
    "pypi_packages": [
        "anthropic",
        "openai",
        "google-generativeai",
        "langchain",
        "crewai",
    ],
    "rss_feeds": [
        "https://www.anthropic.com/rss.xml",
        "https://openai.com/blog/rss.xml",
        "https://blog.google/technology/ai/rss",
    ],
    "reddit_subreddits": [
        "LocalLLaMA",
        "MachineLearning",
        "artificial",
        "OpenAI",
        "singularity"
    ],
    "hackernews_keywords": [
        "claude",
        "gpt",
        "gemini",
        "llm",
        "ai agent",
        "mcp server"
    ]
}

# Content categorization
CONTENT_CATEGORIES = {
    "claude_updates": {
        "title": "Claude & Anthropic Updates",
        "keywords": ["claude", "anthropic", "constitutional ai"],
        "priority": 1
    },
    "codex_updates": {
        "title": "Codex & OpenAI Updates",
        "keywords": ["codex", "openai", "gpt", "chatgpt"],
        "priority": 2
    },
    "gemini_updates": {
        "title": "Gemini & Google AI Updates",
        "keywords": ["gemini", "bard", "google ai", "palm"],
        "priority": 3
    },
    "cli_tools": {
        "title": "CLI Tools & Developer Updates",
        "keywords": ["cli", "terminal", "command line", "developer tools"],
        "priority": 4
    },
    "mcp_updates": {
        "title": "MCP & Model Context Protocol",
        "keywords": ["mcp", "model context", "mcp server"],
        "priority": 5
    },
    "agent_improvements": {
        "title": "AI Agent Enhancements",
        "keywords": ["agent", "autonomous", "workflow", "orchestration"],
        "priority": 6
    }
}

# Rate limiting
RATE_LIMITS = {
    "github": {"calls": 60, "period": 3600},  # 60 calls per hour without token
    "reddit": {"calls": 60, "period": 60},  # 60 calls per minute
    "npm": {"calls": 100, "period": 60},  # 100 calls per minute
    "pypi": {"calls": 100, "period": 60},  # 100 calls per minute
}

# Report configuration
REPORT_CONFIG = {
    "title": "AI Intelligence Daily Briefing",
    "subtitle": f"Your Daily Update on AI Development Tools",
    "max_items_per_category": 10,
    "summary_max_length": 500,
    "enable_dark_mode": True,
    "auto_open_browser": True
}