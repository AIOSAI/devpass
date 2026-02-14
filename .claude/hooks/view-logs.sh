#!/bin/bash
"""
Log Viewer - View Claude Code hook logs easily

Usage:
  view-logs.sh                 # Show recent activity
  view-logs.sh last 10         # Show last 10 entries
  view-logs.sh search "git"    # Search for specific commands
  view-logs.sh stats           # Show statistics
  view-logs.sh follow          # Follow logs in real-time
  view-logs.sh clear           # Clear all logs

Author: SuperClaude
Created: 2025-11-12
"""

LOG_DIR="$HOME/.claude/logs/hooks"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
RESET='\033[0m'

# Ensure log directory exists
mkdir -p "$LOG_DIR"

show_recent() {
    local count=${1:-20}
    echo -e "${CYAN}=== Recent Tool Executions (last $count) ===${RESET}"
    if [ -f "$LOG_DIR/current-session.log" ]; then
        tail -n "$count" "$LOG_DIR/current-session.log"
    else
        echo "No logs found yet."
    fi
}

show_last() {
    local count=${1:-10}
    echo -e "${CYAN}=== Last $count Full Executions ===${RESET}"
    if [ -f "$LOG_DIR/hook-execution.log" ]; then
        tail -n $((count * 20)) "$LOG_DIR/hook-execution.log"
    else
        echo "No execution logs found yet."
    fi
}

search_logs() {
    local query="$1"
    echo -e "${CYAN}=== Searching for: $query ===${RESET}"

    if [ -f "$LOG_DIR/hook-execution.log" ]; then
        grep -i "$query" "$LOG_DIR/hook-execution.log" --color=always -B 2 -A 5
    else
        echo "No logs to search."
    fi
}

show_stats() {
    echo -e "${CYAN}=== Log Statistics ===${RESET}\n"

    if [ -f "$LOG_DIR/current-session.log" ]; then
        local total=$(wc -l < "$LOG_DIR/current-session.log")
        echo -e "${GREEN}Total tool calls:${RESET} $total"

        echo -e "\n${YELLOW}Top tools used:${RESET}"
        awk '{print $3}' "$LOG_DIR/current-session.log" | sort | uniq -c | sort -rn | head -10
    fi

    if [ -f "$LOG_DIR/command_history.log" ]; then
        local bash_count=$(wc -l < "$LOG_DIR/command_history.log")
        echo -e "\n${GREEN}Total bash commands:${RESET} $bash_count"
    fi

    if [ -f "$LOG_DIR/truncation.log" ]; then
        local truncations=$(wc -l < "$LOG_DIR/truncation.log")
        echo -e "\n${YELLOW}Output truncations:${RESET} $truncations"
    fi

    echo -e "\n${BLUE}Log file sizes:${RESET}"
    du -h "$LOG_DIR"/* 2>/dev/null | sort -h
}

follow_logs() {
    echo -e "${CYAN}=== Following logs (Ctrl+C to stop) ===${RESET}\n"

    if [ -f "$LOG_DIR/current-session.log" ]; then
        tail -f "$LOG_DIR/current-session.log"
    else
        echo "No logs to follow yet. Waiting..."
        touch "$LOG_DIR/current-session.log"
        tail -f "$LOG_DIR/current-session.log"
    fi
}

clear_logs() {
    echo -e "${YELLOW}Are you sure you want to clear all logs? (y/N)${RESET}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        rm -f "$LOG_DIR"/*.log
        rm -f "$LOG_DIR"/*.json
        echo -e "${GREEN}All logs cleared.${RESET}"
    else
        echo "Cancelled."
    fi
}

show_help() {
    echo -e "${CYAN}Claude Code Hook Log Viewer${RESET}\n"
    echo "Usage:"
    echo "  view-logs.sh                 # Show recent activity"
    echo "  view-logs.sh last [N]        # Show last N full executions (default: 10)"
    echo "  view-logs.sh search <query>  # Search for specific commands or tools"
    echo "  view-logs.sh stats           # Show statistics"
    echo "  view-logs.sh follow          # Follow logs in real-time"
    echo "  view-logs.sh clear           # Clear all logs"
    echo "  view-logs.sh help            # Show this help"
}

# Main script logic
case "$1" in
    last)
        show_last "${2:-10}"
        ;;
    search)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Please provide a search query${RESET}"
            exit 1
        fi
        search_logs "$2"
        ;;
    stats)
        show_stats
        ;;
    follow)
        follow_logs
        ;;
    clear)
        clear_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        show_recent
        ;;
    *)
        echo -e "${RED}Unknown command: $1${RESET}"
        echo "Use 'view-logs.sh help' for usage information"
        exit 1
        ;;
esac
