# VS Code Terminal Status Extension - Implementation Plan

**Session**: 17 (2025-11-18)
**Purpose**: Visual status indicators for multi-branch Claude workflow
**Status**: Research Complete → Design Phase

---

## Problem Statement

**Current Workflow Pain Points**:
- Multiple Claude branches running in parallel terminals
- Sound notifications indicate completion, but can't identify WHICH terminal
- Manual clicking through terminals to find the finished one
- Relying on cognitive memory to track active branches

**Desired Solution**:
- Visual status indicators showing working vs idle terminals
- Quick access to switch between terminals
- Compact UI that doesn't clutter workspace

---

## Solution Design

### MVP (Phase 1): Two-State Detection

**Status Bar Item**:
- Location: Right side of status bar
- Display: `🔄 3 | ⏸️ 2` (working count | idle count)
- Click action: Opens quick pick menu

**Quick Pick Menu**:
- Lists all open terminals with status icons
- Format: `🔄 BACKUP_SYSTEM` or `⏸️ API`
- Select terminal → switches focus to that terminal
- Supports type-to-filter for quick navigation

**Two States**:
- 🔄 **Working**: Terminal is actively running a command
- ⏸️ **Idle**: Terminal is waiting at prompt

### Future Enhancements (Phase 2)

**Additional States**:
- ✅ **Just Completed**: Finished in last 30 seconds
- 💤 **Not Activated**: Terminal open but never interacted with
- ❌ **Error State**: Process crashed or exited with error code

**Enhanced Features**:
- Time since last activity
- Last command executed
- Error code display
- Customizable state timeouts

---

## Technical Architecture

### Core Components

#### 1. Terminal State Tracker

**Purpose**: Maintain real-time state of all terminals

**Implementation Pattern**:
```typescript
class TerminalStateTracker {
  private busyTerminals = new Set<vscode.Terminal>();
  private disposables: vscode.Disposable[] = [];

  activate(context: vscode.ExtensionContext) {
    // Track when commands start
    const startListener = vscode.window.onDidStartTerminalShellExecution((event) => {
      this.busyTerminals.add(event.execution.terminal);
      this.notifyStateChange();
    });

    // Track when commands end
    const endListener = vscode.window.onDidEndTerminalShellExecution((event) => {
      this.busyTerminals.delete(event.execution.terminal);
      this.notifyStateChange();
    });

    this.disposables.push(startListener, endListener);
  }

  isTerminalBusy(terminal: vscode.Terminal): boolean {
    return this.busyTerminals.has(terminal);
  }

  getWorkingCount(): number {
    return this.busyTerminals.size;
  }

  getIdleCount(): number {
    return vscode.window.terminals.length - this.busyTerminals.size;
  }

  dispose() {
    this.disposables.forEach(d => d.dispose());
  }
}
```

**Key APIs**:
- `vscode.window.onDidStartTerminalShellExecution` - Fires when command starts
- `vscode.window.onDidEndTerminalShellExecution` - Fires when command completes
- Requires Shell Integration enabled (v1.88+)

**Known Issues**:
- 80% race condition failure on fast commands
- Must call `execution.read()` immediately to capture output (if needed)
- Never call `executeCommand()` inside end event handler (causes PTY crash)

#### 2. Status Bar UI Manager

**Purpose**: Display compact terminal status summary

**Implementation Pattern**:
```typescript
class StatusBarManager {
  private statusBarItem: vscode.StatusBarItem;

  constructor() {
    this.statusBarItem = vscode.window.createStatusBarItem(
      'terminal-status.summary',
      vscode.StatusBarAlignment.Right,
      100  // Priority
    );

    this.statusBarItem.command = 'terminal-status.showQuickPick';
    this.statusBarItem.tooltip = 'Click to view terminal status';
    this.statusBarItem.show();
  }

  update(workingCount: number, idleCount: number) {
    this.statusBarItem.text = `$(sync~spin) ${workingCount} | $(debug-pause) ${idleCount}`;
  }

  dispose() {
    this.statusBarItem.dispose();
  }
}
```

**Codicons Available**:
- `$(sync~spin)` - Spinning animation for working state
- `$(debug-pause)` - Pause icon for idle state
- `$(terminal)` - Terminal icon for general use
- `$(check)` - Future: Just completed
- `$(error)` - Future: Error state
- `$(circle-slash)` - Future: Not activated

**Properties**:
- `text` - Display text with icon support
- `tooltip` - Hover text
- `command` - Command ID to execute on click
- `color` - Optional text color
- `backgroundColor` - Optional background (use sparingly)

#### 3. Quick Pick Terminal Selector

**Purpose**: Show full terminal list with status and allow switching

**Implementation Pattern**:
```typescript
interface TerminalQuickPickItem extends vscode.QuickPickItem {
  terminal: vscode.Terminal;
}

async function showTerminalQuickPick(tracker: TerminalStateTracker): Promise<void> {
  const terminals = vscode.window.terminals;

  const items: TerminalQuickPickItem[] = terminals.map(terminal => {
    const isBusy = tracker.isTerminalBusy(terminal);
    const icon = isBusy ? '$(sync~spin)' : '$(debug-pause)';
    const status = isBusy ? 'Working' : 'Idle';

    return {
      label: `${icon} ${terminal.name}`,
      description: status,
      detail: `Click to switch to this terminal`,
      terminal: terminal
    };
  });

  const selected = await vscode.window.showQuickPick(items, {
    placeHolder: 'Select a terminal to view',
    matchOnDescription: true,
    matchOnDetail: false
  });

  if (selected) {
    selected.terminal.show();  // Switch focus to terminal
  }
}
```

**QuickPickItem Properties**:
- `label` - Main text (supports codicons)
- `description` - Right-aligned secondary text
- `detail` - Below label in smaller text
- `picked` - Pre-selected state
- `alwaysShow` - Keep in list even if filtered out

**QuickPickOptions**:
- `placeHolder` - Prompt text
- `matchOnDescription` - Enable filtering on description
- `canPickMany` - Multi-select (not needed for MVP)

#### 4. Terminal Lifecycle Monitor

**Purpose**: Handle terminal creation/closure events

**Implementation Pattern**:
```typescript
class TerminalLifecycleMonitor {
  activate(context: vscode.ExtensionContext, tracker: TerminalStateTracker) {
    vscode.window.onDidOpenTerminal((terminal) => {
      // New terminal opened - already in idle state
      tracker.notifyStateChange();
    });

    vscode.window.onDidCloseTerminal((terminal) => {
      // Terminal closed - remove from tracking
      tracker.removeTerminal(terminal);
      tracker.notifyStateChange();
    });
  }
}
```

---

## Extension Project Structure

### Directory Layout

```
/home/aipass/.vscode/extensions/terminal-status/
├── src/
│   ├── extension.ts           # Entry point (activate/deactivate)
│   ├── terminalTracker.ts     # State tracking logic
│   ├── statusBar.ts           # Status bar UI management
│   ├── quickPick.ts           # Terminal selector UI
│   └── types.ts               # Shared interfaces
├── package.json               # Extension manifest
├── tsconfig.json              # TypeScript configuration
├── .vscodeignore              # Files to exclude from package
└── README.md                  # Extension documentation
```

### package.json Manifest

```json
{
  "name": "terminal-status",
  "displayName": "Terminal Status Indicator",
  "description": "Visual status indicators for multi-branch workflows",
  "version": "0.1.0",
  "engines": {
    "vscode": "^1.88.0"
  },
  "categories": ["Other"],
  "activationEvents": ["onStartupFinished"],
  "main": "./out/extension.js",
  "contributes": {
    "commands": [
      {
        "command": "terminal-status.showQuickPick",
        "title": "Show Terminal Status"
      },
      {
        "command": "terminal-status.refresh",
        "title": "Refresh Terminal Status"
      }
    ]
  },
  "scripts": {
    "compile": "tsc -p ./",
    "watch": "tsc -watch -p ./",
    "pretest": "npm run compile",
    "lint": "eslint src --ext ts"
  },
  "devDependencies": {
    "@types/vscode": "^1.88.0",
    "@types/node": "^20.x",
    "typescript": "^5.8.2",
    "eslint": "^9.x",
    "@typescript-eslint/parser": "^8.x",
    "@typescript-eslint/eslint-plugin": "^8.x"
  }
}
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "module": "Node16",
    "target": "ES2022",
    "outDir": "out",
    "lib": ["ES2022"],
    "sourceMap": true,
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "moduleResolution": "Node16"
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", ".vscode-test"]
}
```

### Main Extension Entry Point

```typescript
// src/extension.ts
import * as vscode from 'vscode';
import { TerminalStateTracker } from './terminalTracker';
import { StatusBarManager } from './statusBar';
import { showTerminalQuickPick } from './quickPick';

let tracker: TerminalStateTracker;
let statusBar: StatusBarManager;

export function activate(context: vscode.ExtensionContext) {
  console.log('Terminal Status extension activating...');

  // Initialize state tracker
  tracker = new TerminalStateTracker();
  tracker.activate(context);

  // Initialize status bar
  statusBar = new StatusBarManager();

  // Connect tracker updates to status bar
  tracker.onStateChange(() => {
    const workingCount = tracker.getWorkingCount();
    const idleCount = tracker.getIdleCount();
    statusBar.update(workingCount, idleCount);
  });

  // Register quick pick command
  const quickPickCommand = vscode.commands.registerCommand(
    'terminal-status.showQuickPick',
    () => showTerminalQuickPick(tracker)
  );

  // Register refresh command
  const refreshCommand = vscode.commands.registerCommand(
    'terminal-status.refresh',
    () => tracker.forceRefresh()
  );

  // Add to disposables
  context.subscriptions.push(quickPickCommand, refreshCommand);
  context.subscriptions.push(tracker, statusBar);

  console.log('Terminal Status extension activated');
}

export function deactivate() {
  if (tracker) tracker.dispose();
  if (statusBar) statusBar.dispose();
}
```

---

## Implementation Roadmap

### Phase 1: MVP (Two-State Detection)

**Tasks**:
1. ✅ Research complete - APIs validated
2. ⏳ Set up extension project structure
3. ⏳ Implement TerminalStateTracker with Set-based tracking
4. ⏳ Build StatusBarManager with click handler
5. ⏳ Create QuickPick selector with terminal switching
6. ⏳ Wire up event listeners and state updates
7. ⏳ Test with real multi-branch workflow
8. ⏳ Package as local extension (.vsix)

**Success Criteria**:
- Status bar shows accurate working/idle counts in real-time
- Clicking status bar opens terminal list with status icons
- Selecting terminal switches focus correctly
- No performance degradation with 10+ open terminals
- Works reliably with Claude branches running in parallel

### Phase 2: Enhanced States (Future)

**Additions**:
- Just completed state (time-based tracking)
- Not activated state (interaction tracking)
- Error state (exit code monitoring)
- Last command display in quick pick
- Time since last activity
- Configurable state timeouts

**Research Needed**:
- How to detect terminal interaction vs just being open
- Reliable exit code tracking pattern
- State transition timing tuning

---

## Technical References

### Shell Integration API

**Minimum VS Code Version**: 1.88.0 (March 2024)

**Key Events**:
```typescript
// Command execution lifecycle
vscode.window.onDidStartTerminalShellExecution: Event<TerminalShellExecutionStartEvent>
vscode.window.onDidEndTerminalShellExecution: Event<TerminalShellExecutionEndEvent>

// Terminal lifecycle
vscode.window.onDidOpenTerminal: Event<Terminal>
vscode.window.onDidCloseTerminal: Event<Terminal>
vscode.window.onDidChangeActiveTerminal: Event<Terminal | undefined>

// Terminal state
vscode.window.terminals: readonly Terminal[]
vscode.window.activeTerminal: Terminal | undefined
```

**TerminalShellExecution Interface**:
```typescript
interface TerminalShellExecution {
  readonly terminal: Terminal;
  readonly command: TerminalShellExecutionCommand;
  readonly cwd: vscode.Uri | undefined;
  read(): AsyncIterable<string>;  // Output stream
}

interface TerminalShellExecutionEndEvent {
  readonly execution: TerminalShellExecution;
  readonly exitCode: number | undefined;
}
```

**Reading Output** (if needed for future enhancements):
```typescript
vscode.window.onDidStartTerminalShellExecution(async (event) => {
  const stream = event.execution.read();
  for await (const data of stream) {
    console.log('Terminal output:', data);
  }
});
```

**Critical Performance Notes**:
- Race condition: ~80% failure rate on commands that complete <100ms
- Workaround: Call `execution.read()` immediately, even if not processing output
- PTY crash: Never execute commands inside `onDidEndTerminalShellExecution`
- Overhead: Use Set/Map for tracking, avoid creating objects in event handlers

### Status Bar API

**Creation**:
```typescript
vscode.window.createStatusBarItem(
  id?: string,  // Optional unique ID
  alignment?: StatusBarAlignment,  // Left or Right
  priority?: number  // Higher = more left/right
): StatusBarItem
```

**StatusBarItem Properties**:
- `text: string` - Display text with codicon support
- `tooltip: string | MarkdownString` - Hover text
- `command: string | Command` - Command to execute on click
- `color: string | ThemeColor` - Text color
- `backgroundColor: ThemeColor` - Background (use for warnings/errors only)
- `name: string` - Accessible name for screen readers

**Methods**:
- `show(): void` - Make visible
- `hide(): void` - Hide from status bar
- `dispose(): void` - Remove completely

### Quick Pick API

**Basic Usage**:
```typescript
const result = await vscode.window.showQuickPick(
  items: T[] | Thenable<T[]>,
  options?: QuickPickOptions,
  token?: CancellationToken
): Thenable<T | undefined>
```

**Advanced Usage** (for real-time updates):
```typescript
const quickPick = vscode.window.createQuickPick();
quickPick.items = [...];
quickPick.placeholder = 'Select...';
quickPick.onDidChangeSelection(selection => {
  // Handle selection
});
quickPick.show();
```

### Terminal API

**Switching Focus**:
```typescript
terminal.show(preserveFocus?: boolean): void
// preserveFocus: true = don't steal focus from editor
// preserveFocus: false (default) = focus terminal
```

**Finding Terminals**:
```typescript
// By name
const terminal = vscode.window.terminals.find(t => t.name === 'BACKUP_SYSTEM');

// All terminals
const allTerminals = vscode.window.terminals;

// Active terminal
const active = vscode.window.activeTerminal;
```

---

## Current System Configuration

### VS Code Settings (/home/aipass/.vscode/settings.json)

**Shell Integration**: ✅ Enabled
```json
{
  "terminal.integrated.shellIntegration.enabled": true
}
```

**Performance Optimizations**:
```json
{
  "files.watcherExclude": {
    "**/backup_system/backups/**": true,
    "**/MEMORY_BANK/**": true,
    "**/node_modules/**": true
  }
}
```

### Installed Extensions

Relevant to terminal workflows:
- Claude Code
- GitLens
- Code Spell Checker
- ESLint
- Prettier

### Existing Infrastructure

**Modular Python Orchestrator**: `/home/aipass/.vscode/apps/.vscode.py`
- Auto-discovers modules in subdirectories
- Ready for custom extensions

**Empty Directories Ready**:
- `/home/aipass/.vscode/apps/extensions/`
- `/home/aipass/.vscode/apps/handlers/`
- `/home/aipass/.vscode/apps/modules/`

**Extension Installation Path**:
- Local development: `/home/aipass/.vscode/extensions/terminal-status/`
- Production: Package as .vsix and install via Extensions panel

---

## Installation & Testing

### Local Development Setup

```bash
# Create extension directory
mkdir -p /home/aipass/.vscode/extensions/terminal-status
cd /home/aipass/.vscode/extensions/terminal-status

# Initialize npm project
npm init -y

# Install dependencies
npm install --save-dev @types/vscode@^1.88.0 typescript@^5.8.2

# Create source directory
mkdir src

# Compile TypeScript
npx tsc -p .

# Test in Extension Development Host
# Press F5 in VS Code with extension folder open
```

### Debug Configuration (.vscode/launch.json)

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run Extension",
      "type": "extensionHost",
      "request": "launch",
      "args": [
        "--extensionDevelopmentPath=${workspaceFolder}"
      ],
      "outFiles": [
        "${workspaceFolder}/out/**/*.js"
      ],
      "preLaunchTask": "${defaultBuildTask}"
    }
  ]
}
```

### Testing Checklist

**Basic Functionality**:
- [ ] Extension activates on VS Code startup
- [ ] Status bar item appears on right side
- [ ] Counts update when opening new terminal
- [ ] Counts update when running commands
- [ ] Clicking status bar opens quick pick menu
- [ ] Terminal list shows all open terminals
- [ ] Status icons match actual terminal state
- [ ] Selecting terminal switches focus correctly

**Multi-Branch Workflow**:
- [ ] Open 5+ Claude branches in separate terminals
- [ ] Run long-running command in one terminal
- [ ] Status bar shows 1 working, 4 idle
- [ ] Quick pick shows correct status for each
- [ ] Complete command → status updates to idle
- [ ] Start multiple commands → all show working
- [ ] Close terminal → counts update correctly

**Edge Cases**:
- [ ] Very fast commands (<100ms) - may miss due to race condition
- [ ] Opening 20+ terminals - performance test
- [ ] Closing active terminal while command running
- [ ] VS Code restart - state correctly initialized
- [ ] No terminals open - graceful handling

**Performance**:
- [ ] No noticeable lag with 10+ terminals
- [ ] Status bar updates feel instant
- [ ] Quick pick opens without delay
- [ ] No memory leaks after extended use

---

## Known Issues & Workarounds

### Shell Integration Race Condition

**Issue**: 80% failure rate detecting fast commands (<100ms)

**Workaround**:
- Accept limitation for MVP
- Most Claude commands take >1s, so not a problem for target workflow
- Future: Could implement polling backup for terminals that never fire events

### Terminal Icon Limitation

**Issue**: Cannot dynamically change terminal icons in dropdown

**Impact**: Original user request not feasible with current VS Code API

**Workaround**: Status bar + quick pick approach (user approved)

### PTY Crash Risk

**Issue**: Calling `vscode.commands.executeCommand()` inside `onDidEndTerminalShellExecution` crashes PTY

**Prevention**: Never execute commands in end event handler, only update state

### State Persistence

**Issue**: Extension state lost on VS Code restart

**Impact**: No history of which terminals were working before restart

**Future Enhancement**: Persist state to workspace storage or global state

---

## Documentation Links

**VS Code API**:
- Extension API: https://code.visualstudio.com/api
- Terminal API: https://code.visualstudio.com/api/references/vscode-api#Terminal
- Status Bar: https://code.visualstudio.com/api/references/vscode-api#StatusBarItem
- Quick Pick: https://code.visualstudio.com/api/references/vscode-api#QuickPick

**Shell Integration**:
- Overview: https://code.visualstudio.com/docs/terminal/shell-integration
- OSC 633 Sequences: https://code.visualstudio.com/docs/terminal/shell-integration#_vs-code-custom-sequences-osc-633

**Extension Development**:
- Getting Started: https://code.visualstudio.com/api/get-started/your-first-extension
- Publishing: https://code.visualstudio.com/api/working-with-extensions/publishing-extension

**Codicons**:
- Icon Reference: https://microsoft.github.io/vscode-codicons/dist/codicon.html

---

## Next Steps

1. **Review this plan with user** - Confirm architecture approach
2. **Set up extension project** - Create directory structure, package.json
3. **Implement core tracking** - TerminalStateTracker with event listeners
4. **Build UI components** - StatusBarManager and QuickPick selector
5. **Wire everything together** - Extension entry point and state management
6. **Test with real workflow** - Multi-branch Claude terminals
7. **Iterate based on feedback** - Refine detection logic and UI

**Estimated MVP Timeline**: Foundation ready for testing within this session
