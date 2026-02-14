#!/bin/bash
# Nexus Launcher - Run GPT-4.1 through Claude Code
# Usage: ./launch_nexus.sh [model]
# Default model: gpt-4.1

set -e

MODEL="${1:-gpt-4.1}"
PROXY_PORT=8082
PROXY_PID=""
NEXUS_DIR="/home/aipass/Nexus"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}╔═══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║       N E X U S   L A U N C H E R        ║${NC}"
echo -e "${GREEN}║   GPT-4.1 via Claude Code Infrastructure  ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}"
echo ""

# Load environment
if [ -f /home/aipass/.env ]; then
    set -a
    source /home/aipass/.env
    set +a
    echo -e "${GREEN}✓${NC} Environment loaded"
else
    echo -e "${RED}Error: /home/aipass/.env not found${NC}"
    exit 1
fi

# Check prerequisites
echo -n "Checking prerequisites..."

if ! command -v claude &> /dev/null; then
    echo -e " ${RED}FAILED${NC}"
    echo -e "${RED}Error: claude CLI not found. Install Claude Code first.${NC}"
    exit 1
fi

if ! command -v claude-code-proxy &> /dev/null; then
    echo -e " ${RED}FAILED${NC}"
    echo -e "${RED}Error: claude-code-proxy not found. Run: pip install claude-code-proxy${NC}"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo -e " ${RED}FAILED${NC}"
    echo -e "${RED}Error: OPENAI_API_KEY not set in .env${NC}"
    exit 1
fi

echo -e " ${GREEN}OK${NC}"

# Check if port is already in use
if lsof -Pi :$PROXY_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}Warning: Port $PROXY_PORT already in use${NC}"
    echo -n "Attempting to free port..."
    # Kill existing process on port
    lsof -ti:$PROXY_PORT | xargs kill -9 2>/dev/null || true
    sleep 1
    echo -e " ${GREEN}OK${NC}"
fi

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down Nexus proxy...${NC}"
    if [ -n "$PROXY_PID" ] && kill -0 "$PROXY_PID" 2>/dev/null; then
        kill "$PROXY_PID" 2>/dev/null
        wait "$PROXY_PID" 2>/dev/null
        echo -e "${GREEN}✓${NC} Proxy stopped"
    fi
}
trap cleanup EXIT INT TERM

# Start proxy
echo -e "${YELLOW}Starting claude-code-proxy on port ${PROXY_PORT}...${NC}"

# Need to run from venv to access server module
cd /home/aipass/.venv
source bin/activate
python -m uvicorn server.fastapi:app --host 127.0.0.1 --port $PROXY_PORT --log-level warning > /tmp/nexus-proxy.log 2>&1 &
PROXY_PID=$!

# Wait for proxy to be ready
echo -n "Waiting for proxy"
READY=false
for i in {1..30}; do
    if curl -s http://localhost:$PROXY_PORT/health > /dev/null 2>&1 || curl -s http://localhost:$PROXY_PORT/ > /dev/null 2>&1; then
        echo -e " ${GREEN}ready!${NC}"
        READY=true
        break
    fi
    echo -n "."
    sleep 0.5
done

if [ "$READY" = false ]; then
    echo -e " ${RED}FAILED${NC}"
    echo -e "${RED}Proxy did not start. Check logs at /tmp/nexus-proxy.log${NC}"
    if [ -f /tmp/nexus-proxy.log ]; then
        echo -e "${YELLOW}Last 10 lines of proxy log:${NC}"
        tail -10 /tmp/nexus-proxy.log
    fi
    exit 1
fi

# Launch Claude Code with Nexus identity
echo -e "${GREEN}Launching Nexus (${MODEL}) via Claude Code...${NC}"
echo ""

# Export environment for Claude Code
export ANTHROPIC_BASE_URL="http://localhost:$PROXY_PORT"
export ANTHROPIC_API_KEY=""
export OPENAI_API_KEY="$OPENAI_API_KEY"
export CLAUDE_MODEL="$MODEL"

cd "$NEXUS_DIR"
claude

echo ""
echo -e "${GREEN}✓${NC} Nexus session ended"
