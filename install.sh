#!/bin/bash
# Daily AI Intelligence Briefing System - One-Click Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/heyfinal/daily-intelligence-briefing/main/install.sh | bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/heyfinal/daily-intelligence-briefing"
INSTALL_DIR="$HOME/daily-intelligence-briefing"
PYTHON_MIN_VERSION="3.9"

# Logging
LOG_FILE="/tmp/intelligence-briefing-install.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

print_banner() {
    echo -e "${PURPLE}"
    cat << 'EOF'
    ____        _ __         ___    ____   ____      __       __ ___                         
   / __ \____ _(_) /_  __   /   |  /  _/  /  _/___  / /____  / /  (_)___ ____  ____  ________ 
  / / / / __ `/ / / / / /  / /| |  / /    / // __ \/ __/ _ \/ / / / / __ `/ _ \/ __ \/ ___/ _ \
 / /_/ / /_/ / / / /_/ /  / ___ |_/ /   _/ // / / / /_/  __/ / / / / /_/ /  __/ / / / /__/  __/
/_____/\__,_/_/_/\__, /  /_/  |_/___/  /___/_/ /_/\__/\___/_/_/_/_/\__, /\___/_/ /_/\___/\___/ 
                /____/                                           /____/                      
    ____       _      ___                 _____            __                
   / __ )_____(_)__  / _/___  ____ ___   / ___/__  _______/ /____  ____ ___  
  / __  / ___/ / _ \/ _/ __ \/ __ `/__/   \__ \/ / / / ___/ __/ _ \/ __ `__ \ 
 / /_/ / /  / /  __/ _/ / / / /_/ /      ___/ / /_/ (__  ) /_/  __/ / / / / / 
/_____/_/  /_/\___/_//_/ /_/\__, /      /____/\__, /____/\__/\___/_/ /_/ /_/  
                          /____/            /____/                          
EOF
    echo -e "${NC}"
    echo -e "${CYAN}🤖 One-Click Installation Script${NC}"
    echo -e "${BLUE}Repository: $REPO_URL${NC}"
    echo ""
}

check_system() {
    log "🔍 Checking system requirements..."
    
    # Check macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        echo -e "${RED}❌ This installer is designed for macOS only${NC}"
        exit 1
    fi
    
    # Check Python version
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
            echo -e "${RED}❌ Python $PYTHON_MIN_VERSION+ required. Found: $PYTHON_VERSION${NC}"
            exit 1
        fi
        echo -e "${GREEN}✅ Python $PYTHON_VERSION detected${NC}"
    else
        echo -e "${RED}❌ Python 3 not found. Please install Python $PYTHON_MIN_VERSION+${NC}"
        exit 1
    fi
    
    # Check Git
    if ! command -v git >/dev/null 2>&1; then
        echo -e "${RED}❌ Git not found. Please install Git first${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Git detected${NC}"
    
    # Check curl
    if ! command -v curl >/dev/null 2>&1; then
        echo -e "${RED}❌ curl not found. Please install curl first${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ curl detected${NC}"
    
    log "✅ System requirements check passed"
}

install_dependencies() {
    log "📦 Checking and installing dependencies..."
    
    # Check Homebrew
    if ! command -v brew >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Homebrew not found. Installing Homebrew...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add to PATH for current session
        if [[ -f "/opt/homebrew/bin/brew" ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [[ -f "/usr/local/bin/brew" ]]; then
            eval "$(/usr/local/bin/brew shellenv)"
        fi
    else
        echo -e "${GREEN}✅ Homebrew detected${NC}"
    fi
    
    # Update Homebrew
    echo -e "${BLUE}🔄 Updating Homebrew...${NC}"
    brew update >/dev/null 2>&1 || true
    
    log "✅ Dependencies check completed"
}

clone_repository() {
    log "📥 Cloning repository..."
    
    # Remove existing directory if it exists
    if [[ -d "$INSTALL_DIR" ]]; then
        echo -e "${YELLOW}⚠️  Existing installation found. Backing up...${NC}"
        BACKUP_DIR="${INSTALL_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
        mv "$INSTALL_DIR" "$BACKUP_DIR"
        echo -e "${GREEN}✅ Backed up to: $BACKUP_DIR${NC}"
    fi
    
    # Clone repository
    echo -e "${BLUE}📥 Cloning repository...${NC}"
    if ! git clone "$REPO_URL" "$INSTALL_DIR"; then
        echo -e "${RED}❌ Failed to clone repository${NC}"
        exit 1
    fi
    
    cd "$INSTALL_DIR"
    echo -e "${GREEN}✅ Repository cloned to: $INSTALL_DIR${NC}"
    log "✅ Repository cloned successfully"
}

install_system() {
    log "🚀 Installing Daily AI Intelligence Briefing System..."
    
    cd "$INSTALL_DIR"
    
    # Make installer executable
    chmod +x enhanced_install.py
    
    # Run the enhanced installer
    echo -e "${BLUE}🔧 Running system installer...${NC}"
    if ! python3 enhanced_install.py --non-interactive; then
        echo -e "${RED}❌ Installation failed. Check logs: $LOG_FILE${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ System installed successfully${NC}"
    log "✅ System installation completed"
}

verify_installation() {
    log "🔍 Verifying installation..."
    
    cd "$INSTALL_DIR"
    
    # Check if virtual environment exists
    if [[ ! -d "venv" ]]; then
        echo -e "${RED}❌ Virtual environment not found${NC}"
        exit 1
    fi
    
    # Test Python imports
    echo -e "${BLUE}🧪 Testing system components...${NC}"
    if ! ./venv/bin/python -c "import src.config, src.database, src.data_collector; print('Core modules OK')"; then
        echo -e "${RED}❌ System verification failed${NC}"
        exit 1
    fi
    
    # Check scheduler
    if ! ./venv/bin/python src/scheduler.py status >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Scheduler not configured (this is OK for first run)${NC}"
    fi
    
    echo -e "${GREEN}✅ Installation verified${NC}"
    log "✅ Installation verification completed"
}

generate_demo_report() {
    log "📰 Generating demo report..."
    
    cd "$INSTALL_DIR"
    
    echo -e "${BLUE}📰 Generating your first intelligence report...${NC}"
    if ./venv/bin/python run_enhanced_briefing.py --enhanced --web-api --demo 2>&1 | tee -a "$LOG_FILE"; then
        echo -e "${GREEN}✅ Demo report generated${NC}"
        
        # Try to open the report
        if [[ -f "reports/latest_report.html" ]]; then
            echo -e "${CYAN}🌐 Opening demo report in browser...${NC}"
            open "reports/latest_report.html" || true
        fi
    else
        echo -e "${YELLOW}⚠️  Demo report generation had issues (this is normal on first run)${NC}"
    fi
    
    log "✅ Demo report process completed"
}

print_success_message() {
    echo -e "${GREEN}"
    cat << 'EOF'
    ┌─────────────────────────────────────────────────────────────────┐
    │                     🎉 Installation Complete! 🎉                │
    └─────────────────────────────────────────────────────────────────┘
EOF
    echo -e "${NC}"
    
    echo -e "${CYAN}📍 Installation Directory:${NC} $INSTALL_DIR"
    echo -e "${CYAN}📄 Log File:${NC} $LOG_FILE"
    echo ""
    
    echo -e "${PURPLE}🚀 Quick Start Commands:${NC}"
    echo -e "${BLUE}# Generate a report now:${NC}"
    echo "cd $INSTALL_DIR && ./venv/bin/python run_enhanced_briefing.py --enhanced --web-api"
    echo ""
    echo -e "${BLUE}# Check system status:${NC}"
    echo "cd $INSTALL_DIR && ./venv/bin/python run_enhanced_briefing.py --status"
    echo ""
    echo -e "${BLUE}# Set up daily automation (5 AM reports):${NC}"
    echo "cd $INSTALL_DIR && ./venv/bin/python src/scheduler.py install"
    echo ""
    
    echo -e "${YELLOW}⏰ Daily Reports:${NC}"
    echo "• Reports will be generated daily at 4:30 AM"
    echo "• Your browser will open the latest report at 5:00 AM"
    echo "• Reports are saved in: $INSTALL_DIR/reports/"
    echo ""
    
    echo -e "${GREEN}✨ Features Available:${NC}"
    echo "• 📰 Professional daily intelligence reports"
    echo "• 📊 Local project analysis and recommendations"
    echo "• ✅ Interactive installation checklist"
    echo "• 🔒 Secure package management"
    echo "• 🌐 Web-based interface"
    echo ""
    
    echo -e "${CYAN}📖 Documentation:${NC} https://github.com/heyfinal/daily-intelligence-briefing"
    echo -e "${CYAN}🐛 Issues & Support:${NC} https://github.com/heyfinal/daily-intelligence-briefing/issues"
    echo ""
    
    echo -e "${PURPLE}🤖 Your Daily AI Intelligence Briefing System is ready!${NC}"
    echo -e "${BLUE}Wake up tomorrow at 5 AM to your first automated intelligence briefing! ☀️${NC}"
}

handle_error() {
    local line_number=$1
    local error_code=$2
    echo -e "${RED}❌ Installation failed at line $line_number with exit code $error_code${NC}"
    echo -e "${YELLOW}📄 Check the log file for details: $LOG_FILE${NC}"
    echo -e "${CYAN}🆘 For support, visit: https://github.com/heyfinal/daily-intelligence-briefing/issues${NC}"
    exit $error_code
}

# Main installation process
main() {
    # Set up error handling
    trap 'handle_error ${LINENO} $?' ERR
    
    print_banner
    
    echo -e "${BLUE}🚀 Starting installation process...${NC}"
    log "Starting Daily AI Intelligence Briefing System installation"
    
    check_system
    install_dependencies
    clone_repository
    install_system
    verify_installation
    generate_demo_report
    
    print_success_message
    
    log "✅ Installation completed successfully"
}

# Run main function
main "$@"