# 🤖 Daily AI Intelligence Briefing System

A comprehensive daily intelligence briefing system that monitors AI development tools, generates professional HTML reports, and provides interactive installation capabilities for discovered improvements.

## 🌟 Features

- **📰 Professional Daily Reports**: Newspaper-style HTML briefings ready by 5 AM
- **🔍 Comprehensive Monitoring**: Tracks Claude Code, Codex, Gemini, CLI tools, and MCP servers
- **📊 Local Project Analysis**: Scans and analyzes your local development projects
- **✅ Interactive Installation**: Checkbox-style inventory with one-click bulk installation
- **🎯 AI-Powered Recommendations**: Smart suggestions for project improvements
- **⚡ Efficient API Usage**: Smart caching and differential updates
- **🔒 Security First**: Validated installations with comprehensive logging

## 🚀 One-Click Installation

Install the complete system with a single command:

```bash
curl -fsSL https://raw.githubusercontent.com/heyfinal/daily-intelligence-briefing/main/install.sh | bash
```

This will automatically:
- ✅ Check system requirements (macOS, Python 3.9+, Git, curl)
- ✅ Install Homebrew if needed
- ✅ Clone the repository to `~/daily-intelligence-briefing`
- ✅ Set up the complete system with all dependencies
- ✅ Generate your first demo report
- ✅ Open the report in your browser

## 🔧 Manual Installation

```bash
# Clone the repository
git clone https://github.com/heyfinal/daily-intelligence-briefing.git
cd daily-intelligence-briefing

# Install the system
python3 enhanced_install.py

# Generate your first enhanced report
python3 run_enhanced_briefing.py --enhanced --web-api

# Open the report
open reports/latest_report.html
```

## 📋 What You Get Every Morning

### 1. **Daily Intelligence Section**
- Latest Claude Code updates and improvements
- Codex CLI enhancements and new features
- Gemini API updates and capabilities
- New CLI tools for development productivity
- MCP server updates and new integrations
- Sub-agent improvements and optimizations

### 2. **Local Project Status Dashboard**
- Health analysis of all your development projects
- Git status (uncommitted changes, branch info)
- Dependency analysis (outdated packages, vulnerabilities)
- Code quality metrics and suggestions
- AI-powered recommendations with priority levels

### 3. **Interactive Installation Checklist**
- Checkbox inventory of all discoverable tools and packages
- Categories: CLI Tools, MCP Servers, Python packages, npm packages
- One-click "Install Selected" with real-time progress
- Secure installation with validation and rollback

### 4. **System Health & Recommendations**
- Overall system performance metrics
- API usage efficiency tracking
- Recommended system optimizations
- Predictive maintenance alerts

## 🛠 System Requirements

- **macOS** (tested on macOS 14+)
- **Python 3.9+**
- **Git** (for project analysis)
- **Internet connection** (for data collection)
- **Web browser** (for viewing reports)

## 📁 Project Structure

```
daily-intelligence-briefing/
├── src/                        # Core system modules
│   ├── config.py              # Configuration management
│   ├── database.py            # SQLite database operations
│   ├── data_collector.py      # Async data collection
│   ├── html_generator.py      # Report generation
│   ├── project_scanner.py     # Local project analysis
│   ├── installation_manager.py # Package installation
│   └── web_api.py             # REST API server
├── templates/                  # HTML/CSS/JS templates
├── data/                      # SQLite database (auto-created)
├── reports/                   # Generated HTML reports
├── logs/                      # System logs
├── cache/                     # API response cache
├── enhanced_install.py        # System installer
├── enhanced_uninstall.py      # System remover
├── run_enhanced_briefing.py   # Main orchestrator
└── requirements.txt           # Python dependencies
```

## 🔧 Configuration

The system auto-generates a `config.json` file with sensible defaults. You can customize:

```json
{
  "data_sources": {
    "github_repos": ["anthropics/claude-code", "openai/openai-python"],
    "npm_packages": ["@anthropic-ai/sdk", "openai"],
    "pypi_packages": ["anthropic", "openai", "langchain"]
  },
  "schedule": {
    "daily_run_time": "04:30",
    "report_launch_time": "05:00"
  },
  "cache": {
    "expiry_hours": 6,
    "max_entries": 10000
  }
}
```

## 🎯 Usage Examples

```bash
# Generate report now with all features
python3 run_enhanced_briefing.py --enhanced --web-api

# Check system status
python3 run_enhanced_briefing.py --status

# Force refresh all data (ignore cache)
python3 run_enhanced_briefing.py --force --enhanced

# Open latest report in browser
python3 run_enhanced_briefing.py --open

# Run web API server only
python3 src/web_api.py

# Scan local projects only
python3 -c "from src.project_scanner import ProjectScanner; scanner = ProjectScanner(); projects = scanner.scan_projects('/Users/yourusername'); print(f'Found {len(projects)} projects')"
```

## 🔒 Security Features

- **Input Validation**: All installation commands are sanitized
- **Package Manager Whitelist**: Only approved package managers allowed
- **Audit Logging**: Comprehensive logs of all system changes
- **Rollback Capability**: Failed installations can be reverted
- **Local-Only**: No data leaves your machine

## 📊 Performance

- **Execution Time**: 2-5 minutes for complete daily cycle
- **Memory Usage**: ~50MB during data collection
- **API Efficiency**: ~100-200 API calls per day (well within limits)
- **Disk Usage**: ~10MB database, ~5MB per report
- **Cache Hit Rate**: Typically 70-85% (reduces redundant API calls)

## 🐛 Troubleshooting

### Common Issues

**Report not generating?**
```bash
python3 run_enhanced_briefing.py --force --verbose
```

**Installation failures?**
```bash
# Check logs
tail -f logs/installation.log

# Verify system status
python3 run_enhanced_briefing.py --status
```

**Scheduling not working?**
```bash
# Check macOS LaunchAgent
launchctl list | grep intelligence-briefing

# Reload scheduler
python3 src/scheduler.py install
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with meta-ai-agent orchestration
- Inspired by the need for daily AI development intelligence
- Designed for the Claude Code ecosystem

## 🔗 Related Projects

- [Claude Code](https://claude.ai/code) - The AI coding assistant this system monitors
- [MCP Registry](https://registry.modelcontextprotocol.io) - Model Context Protocol servers
- [Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python) - Official Anthropic Python SDK

---

**Generated daily intelligence briefings since 2025** 🤖📰