# Enhanced AI Intelligence Briefing System

A comprehensive, production-ready system that generates daily intelligence reports from AI/ML news sources with advanced project management, installation automation, and health monitoring capabilities.

## 🚀 New Enhanced Features

### 1. **Interactive Installation Checklist**
- **Automatic Package Detection**: Scans intelligence data for installable tools and packages
- **Multi-Platform Support**: Supports Homebrew, npm, pip, cargo, go modules, and more  
- **One-Click Installation**: Select and install multiple packages with progress tracking
- **Security Validation**: All installation commands are validated for safety
- **Installation History**: Complete audit trail of all installations

### 2. **Local Project Status Dashboard**
- **Automated Project Discovery**: Recursively scans filesystem for Claude Code projects
- **Health Score Analysis**: Comprehensive health scoring (0-100) for each project
- **Git Integration**: Track uncommitted changes, branch status, and remote sync
- **Dependency Analysis**: Check for outdated packages and security vulnerabilities
- **Code Quality Metrics**: Linting issues, test coverage, documentation analysis

### 3. **AI-Powered Recommendations**
- **Smart Project Insights**: AI-generated recommendations for each project
- **Priority Classification**: Critical/High/Medium/Low priority recommendations
- **Actionable Steps**: Specific commands and changes to improve projects  
- **Time Estimates**: Realistic time estimates for implementing recommendations
- **Category-Based**: Security, Performance, Maintenance, and Feature Development categories

### 4. **System Health Monitoring**
- **Real-Time Metrics**: Data collection rates, cache performance, disk usage
- **System Recommendations**: AI-powered suggestions for system optimization
- **Performance Tracking**: Installation success rates, API response times
- **Automated Maintenance**: Self-healing and cleanup routines

### 5. **Professional Web API**
- **RESTful Endpoints**: Complete API for all system functions
- **Real-Time Updates**: WebSocket-like polling for live progress updates
- **Secure Operations**: Validated and sandboxed command execution
- **Cross-Platform**: Works on macOS, Linux, and Windows

## 📋 Enhanced Report Structure

The new newspaper-style HTML reports include four comprehensive sections:

### **Section 1: Daily Intelligence** (Enhanced)
- Traditional AI/ML news with improved categorization
- Priority-based article ranking with breaking news alerts  
- Enhanced metadata extraction and tagging

### **Section 2: Local Project Status Dashboard**
- Visual project health indicators with color-coded status
- Git repository status and branch information
- Dependency analysis with outdated package warnings
- TODO/FIXME comment extraction and analysis

### **Section 3: Interactive Installation Checklist**
- Categorized installable items from intelligence data
- Multi-select installation interface with progress tracking
- Package manager integration (Homebrew, npm, pip, etc.)
- Installation history and rollback capabilities

### **Section 4: System Health & Recommendations**
- Overall system health status and uptime monitoring
- Performance metrics and optimization suggestions
- Maintenance recommendations and automation status
- Security audit results and compliance checking

## 🛠️ Installation

### Quick Install
```bash
# Clone and run enhanced installer
git clone <repository-url>
cd daily-intelligence-briefing
python3 enhanced_install.py
```

### Manual Setup
```bash
# 1. Setup virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux

# 2. Install enhanced dependencies  
pip install -r enhanced_requirements.txt

# 3. Initialize enhanced system
python3 src/enhanced_html_generator.py
python3 src/web_api.py &

# 4. Configure API credentials
nano config.json
```

## ⚙️ Configuration

The enhanced system uses an extended configuration file:

```json
{
  "github_token": "your_github_token_here",
  "reddit_client_id": "your_reddit_client_id",  
  "reddit_client_secret": "your_reddit_client_secret",
  "report_generation_time": "04:30",
  "report_ready_time": "05:00",
  "timezone": "America/New_York",
  "auto_open_browser": true,
  "max_items_per_category": 10,
  "enhanced_features": {
    "project_scanning": true,
    "installation_management": true,
    "system_health_monitoring": true,
    "web_api": true,
    "api_port": 5000
  },
  "security": {
    "allowed_package_managers": ["brew", "npm", "pip", "cargo", "go"],
    "require_confirmation": true,
    "log_all_commands": true
  }
}
```

## 🚦 Usage

### Daily Operation
```bash
# Generate enhanced report (automatic at 5 AM)
python3 run_briefing.py --enhanced

# Check system status
python3 run_briefing.py --status

# Manual project scan
python3 src/project_scanner.py

# Start web API server
python3 src/web_api.py
```

### Web API Endpoints
```bash
# System health
GET /api/health

# Get installable items
GET /api/installable-items

# Install selected packages
POST /api/install
{"items": [{"id": "pkg1", "name": "jq", ...}]}

# Installation progress
GET /api/installation-progress/{batch_id}

# Project status
GET /api/projects

# System health metrics
GET /api/system-health
```

### Project Management
```bash
# Scan local projects (depth=3)
curl http://localhost:5000/api/projects

# Get project recommendations  
curl http://localhost:5000/api/projects/{project_id}/recommendations

# View system health
curl http://localhost:5000/api/system-health
```

## 📊 Features Detail

### Project Scanner Capabilities
- **Multi-Language Support**: Python, JavaScript, Rust, Go, Java, PHP, Ruby, Swift
- **Package Manager Detection**: Automatic detection of requirements files
- **Git Analysis**: Branch status, uncommitted changes, remote sync
- **Code Quality**: Linting, test coverage, documentation completeness
- **Security Scanning**: Vulnerability detection in dependencies
- **Performance Analysis**: Large file detection, unused dependencies

### Installation Management
- **Package Detection**: Automatically extracts installable packages from news
- **Security Validation**: Commands are sanitized and validated before execution
- **Atomic Operations**: All-or-nothing installation with rollback capability
- **Progress Tracking**: Real-time installation status and output capture
- **Multi-Platform**: Support for macOS, Linux package managers

### Health Monitoring
- **System Metrics**: CPU, memory, disk usage, network performance
- **Application Health**: Database status, cache hit rates, API response times
- **Predictive Analysis**: Early warning for potential issues
- **Automated Remediation**: Self-healing for common problems

## 🔒 Security Features

- **Command Validation**: All installation commands validated against allow-lists
- **Sandboxed Execution**: Package installations run in controlled environment  
- **Audit Logging**: Complete audit trail of all system operations
- **Permission Management**: Granular control over system-level operations
- **Input Sanitization**: All user inputs properly escaped and validated

## 📈 Performance & Scale

- **Parallel Processing**: Multi-threaded scanning and analysis
- **Intelligent Caching**: Smart caching reduces API calls and improves speed
- **Resource Management**: Automatic cleanup and optimization routines  
- **Scalable Architecture**: Designed to handle large codebases and many projects
- **Efficient Storage**: Optimized database schema with proper indexing

## 🔧 Advanced Configuration

### Custom Project Scanning
```python
# Customize project scanner
scanner = ProjectScanner()
scanner.base_paths.append(Path('/custom/path'))
scanner.ignore_patterns.add('custom_ignore')
projects = scanner.scan_projects(max_depth=5)
```

### Custom Installation Validators
```python
# Add custom package manager
validator = SecurityValidator()
validator.safe_managers['custom'] = ['install', 'update']
```

### Web API Customization
```python
# Extend web API
@app.route('/api/custom', methods=['GET'])
def custom_endpoint():
    return jsonify({'custom': 'data'})
```

## 📝 API Documentation

### Installation Management

**POST /api/install**
```json
{
  "items": [
    {
      "id": "unique_id",
      "name": "package_name", 
      "package_manager": "brew|npm|pip|cargo",
      "install_command": "validated_command",
      "category": "cli_tools|dev_tools|...",
      "description": "Package description"
    }
  ]
}
```

**Response:**
```json
{
  "batch_id": "installation_batch_id",
  "queued_count": 3,
  "rejected_items": [],
  "status": "queued"
}
```

### Project Analysis

**GET /api/projects**
```json
{
  "projects": [
    {
      "path": "/path/to/project",
      "name": "project_name",
      "type": "python|javascript|rust|...",
      "health_score": 85,
      "last_modified": "2024-01-01T12:00:00",
      "git_info": {
        "is_repo": true,
        "branch": "main", 
        "uncommitted_changes": false
      },
      "recommendations": [
        {
          "priority": "high|medium|low",
          "category": "security|performance|maintenance",
          "title": "Recommendation title",
          "description": "Detailed description",
          "action": "Specific action to take"
        }
      ]
    }
  ]
}
```

## 🔄 Automation & Scheduling

### macOS (LaunchAgent)
```xml
<!-- ~/Library/LaunchAgents/com.intelligence-briefing.plist -->
<key>ProgramArguments</key>
<array>
    <string>/path/to/venv/bin/python</string>
    <string>/path/to/run_briefing.py</string>
    <string>--enhanced</string>
</array>
```

### Linux (Cron)
```bash
# Daily at 5:00 AM
0 5 * * * /path/to/venv/bin/python /path/to/run_briefing.py --enhanced
```

### Windows (Task Scheduler)
```powershell
# Create scheduled task for daily execution
schtasks /create /sc daily /st 05:00 /tn "AI Intelligence Briefing" /tr "python.exe run_briefing.py --enhanced"
```

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
pytest tests/

# Test specific components
pytest tests/test_project_scanner.py
pytest tests/test_installation_manager.py
pytest tests/test_web_api.py
```

### Integration Tests
```bash
# Test complete workflow
python3 tests/integration_test.py

# Test API endpoints
python3 tests/api_integration_test.py
```

### Manual Testing
```bash
# Test project scanning
python3 -c "from src.project_scanner import ProjectScanner; print(len(ProjectScanner().scan_projects()))"

# Test installation detection
python3 -c "from src.installation_manager import InstallationManager; print(len(InstallationManager().detect_installable_items([])))"
```

## 🔍 Troubleshooting

### Common Issues

**Web API not starting:**
```bash
# Check port availability
lsof -i :5000

# Check logs
tail -f logs/web_api.log
```

**Project scanning too slow:**
```bash
# Reduce scan depth
python3 run_briefing.py --scan-depth 2

# Add ignore patterns
# Edit config to add more ignore_patterns
```

**Installation failures:**
```bash
# Check security validator
python3 -c "from src.installation_manager import SecurityValidator; print(SecurityValidator().validate_command('brew install jq'))"

# Check installation logs  
tail -f logs/installations.log
```

### Debug Mode
```bash
# Enable debug logging
python3 run_briefing.py --enhanced --debug

# Check all logs
find logs/ -name "*.log" -exec tail -f {} +
```

## 📊 Monitoring & Metrics

### System Health Dashboard
- **Uptime**: System availability and reliability metrics
- **Performance**: Response times, throughput, resource utilization  
- **Error Rates**: Failed installations, API errors, scan failures
- **Data Quality**: Intelligence collection rates, source availability

### Alerting
- **Email Notifications**: Critical system issues and failures
- **Desktop Notifications**: Report completion, installation status  
- **Log Monitoring**: Automated log analysis and anomaly detection

## 🚀 Future Enhancements

### Planned Features
- **Machine Learning**: Enhanced project recommendations using ML models
- **Multi-User Support**: Team collaboration and shared intelligence
- **Mobile Interface**: Mobile-responsive web interface
- **Plugin Architecture**: Extensible plugin system for custom features
- **Cloud Sync**: Backup and sync across multiple machines

### Contributing
```bash
# Development setup
git clone <repository>
cd daily-intelligence-briefing
python3 enhanced_install.py --dev

# Create feature branch
git checkout -b feature/new-enhancement

# Run tests before commit
pytest && flake8 src/ && black src/
```

## 📄 License

This enhanced system is provided under the same license as the original project. See LICENSE file for details.

## 🔧 Uninstallation

### Complete Removal
```bash
# Run enhanced uninstaller
python3 enhanced_uninstall.py

# Manual cleanup if needed
rm -rf ~/intelligence_briefing_backup
crontab -e  # Remove any remaining cron jobs
```

### Backup Before Removal
The uninstaller automatically offers to backup:
- Configuration files (config.json)
- Database with collected intelligence
- Recent reports (last 7 days)  
- System logs (last 30 days)

---

**Built with ❤️ using the meta-agent-architect framework**

For support, feature requests, or contributions, please see the project repository.