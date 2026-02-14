# Code Sniffer

Advanced AI-powered codebase analysis system for understanding and documenting large software projects. Provides multi-level analysis with semantic search capabilities.

## What It Is

A comprehensive toolkit for analyzing codebases using AI, combining automated file scanning with intelligent semantic search. Originally designed for research code review but evolved into a powerful development tool.

**Core Components:**

- **code_sniffer.py** - Main analysis engine with progress tracking
- **code_search.py** - AI-powered semantic search through analyzed codebases  
- **Research workflow** - Organized system for analyzing external projects

## Features

### Multi-Level Analysis

- **Basic**: Syntax analysis and dependency detection
- **Enhanced**: AI summaries and key insights  
- **Premium**: Full semantic analysis, pattern detection, quality assessment

### AI-Powered Analysis

- Uses cost-effective models (gpt-4.1-nano) for bulk processing
- Configurable prompts for different analysis types
- Semantic understanding and business context recognition
- Design pattern detection and architectural analysis
- Code quality scoring with recommendations

### Smart Processing

- Progress tracking with resume capability
- Configurable file filtering and size limits
- Stratified sampling for balanced results
- Integration with AIPass ecosystem (prax logging, API monitoring)

## Project Structure

```,
code_sniffer/
├── code_sniffer.py          # Main analysis engine
├── code_search.py           # Semantic search functionality  
├── cleanup_outputs.py       # Maintenance utilities
├── config/
│   ├── ai_config.json      # AI service configuration
│   ├── default.json        # Default settings
│   └── templates/          # Analysis templates
├── code_sniffer_json/      # Generated config and progress
├── research_review/        # Research project workflow
│   ├── pending/           # New projects to analyze
│   ├── analyzed/          # Completed analyses
│   └── tracking.md        # Analysis history
├── scanning/              # Target directory for analysis
└── search_results/        # Search output location
```

## Analysis Levels

### Basic Analysis

```bash
python code_sniffer.py --level basic
```

- File structure analysis
- Dependency mapping
- Syntax validation
- No AI processing (fast)

### Enhanced Analysis  

```bash
python code_sniffer.py --level enhanced
```

- Everything in basic
- AI-generated file summaries
- Key insight extraction
- Technology stack identification

### Premium Analysis

```bash
python code_sniffer.py --level premium
```

- Everything in enhanced  
- Semantic analysis and business context
- Design pattern detection
- Code quality assessment with scoring
- Architectural pattern recognition
- Detailed recommendations

## Configuration

### Main Config (code_sniffer_json/code_sniffer_config.json)

```json
{
  "model": "gpt-4.1-nano",
  "base_path": "./scanning",
  "code_extensions": [".py", ".ts", ".js", ".tsx", ".jsx"],
  "ignore_dirs": ["node_modules", "__pycache__", ".git"],
  "max_file_size_kb": 500,
  "temperature": 0.1,
  "max_description_words": 50
}
```

### AI Services (config/ai_config.json)

```json
{
  "ai_services": {
    "openai": {
      "models": {
        "summarization": "gpt-4.1-nano",
        "analysis": "gpt-4.1-nano"
      }
    }
  },
  "analysis_levels": {
    "premium": {
      "enabled_features": ["semantic_analysis", "pattern_detection", "quality_assessment"]
    }
  }
}
```

## Research Workflow

**For analyzing external codebases:**

1. **Add Research Project**

   ```bash
   cd research_review/pending
   git clone https://github.com/example/research-project
   ```

2. **Run Analysis**

   ```bash
   python code_sniffer.py --level premium
   ```

3. **Search Results**

   ```bash
   python code_search.py "authentication patterns"
   python code_search.py "React components state management"
   ```

4. **Archive**

   ```bash
   mv research_review/pending/project research_review/analyzed/
   # Update tracking.md with insights
   ```

## Semantic Search

The `code_search.py` component provides AI-powered search across analyzed codebases:

```bash
# Search for specific patterns
python code_search.py "error handling patterns"

# Find architectural concepts  
python code_search.py "dependency injection implementation"

# Business logic search
python code_search.py "user authentication workflow"
```

**Features:**

- Semantic understanding (not just keyword matching)
- Stratified sampling for balanced results across projects
- Context-aware responses with file locations
- Integration with analysis results

## Example Output

### File Analysis

```markdown
## src/components/UserDashboard.tsx

React component implementing user dashboard with real-time data updates, 
authentication state management, and responsive design. Uses React hooks 
for state management, TypeScript for type safety, and integrates with 
REST API for data fetching. Quality score: 8.2/10.

**Patterns Detected:** Container/Presentational, Custom Hooks, Error Boundaries
**Business Context:** User management interface for SaaS platform
**Recommendations:** Consider memoization for expensive computations
```

### Search Results

```markdown
# Search Results: "authentication patterns"

## Relevance Score: 9.2
**File:** auth/TokenManager.ts
**Pattern:** JWT token management with refresh logic
**Context:** Implements secure token storage with automatic renewal

## Relevance Score: 8.7  
**File:** middleware/AuthMiddleware.py
**Pattern:** Flask authentication middleware with role-based access
**Context:** Route protection with granular permission system
```

## Integration

**AIPass Ecosystem:**

- Uses prax logging system for comprehensive logging
- Integrates with API usage monitoring
- Follows 3-file JSON pattern (config, data, progress)
- Compatible with existing skill architecture

**External Tools:**

- Works with any codebase (Python, TypeScript, JavaScript, etc.)
- Outputs markdown for easy integration with documentation systems
- JSON APIs for programmatic access to results

## Use Cases

**Research & Learning:**

- Quickly understand new codebases and technologies
- Identify best practices and design patterns
- Generate documentation for complex systems

**Code Review:**

- Pre-analysis before detailed reviews
- Quality assessment and improvement recommendations  
- Pattern detection for consistency checking

**Architecture Analysis:**

- Understand system design and component relationships
- Identify technical debt and improvement opportunities
- Document legacy systems

**Team Onboarding:**

- Generate codebase overviews for new developers
- Create searchable knowledge base of project components
- Provide context-aware code exploration

## Technical Details

- **Languages**: Python 3.x with AI API integration
- **Dependencies**: requests, prax modules, AIPass ecosystem
- **AI Models**: OpenAI GPT models (configurable)
- **Output Formats**: Markdown, JSON, structured reports
- **Storage**: File-based with JSON configuration and progress tracking

The system demonstrates practical AI integration - using cost-effective models for bulk analysis while maintaining quality through intelligent prompting and structured workflows. Perfect for teams needing to understand and document complex codebases efficiently.
