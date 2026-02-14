# Research Code Analysis Tracking

Track all research code analyses and key insights here.

## Analysis Log

| Date | Project | Analysis Level | Key Insights | Quality Score | Status |
|------|---------|---------------|--------------|---------------|---------|
| YYYY-MM-DD | project-name | premium | Brief summary of findings | X.X/10 | ✅ Complete |

## Template Entry

```markdown
### [Project Name] - [Date]
- **Analysis Level**: basic/enhanced/premium
- **Files Analyzed**: X Python, Y TypeScript
- **Quality Score**: X.X/10
- **Key Insights**: 
  - Main finding 1
  - Main finding 2
  - Main finding 3
- **Business Context**: Domain/purpose identified
- **Patterns Found**: Architectural patterns, frameworks used
- **Recommendations**: Key improvement suggestions
- **Location**: `research_review/analyzed/project-name`
- **Ability Cards**: `output/ability_cards/project-name_YYYYMMDD_HHMMSS/`
```

## Quick Analysis Commands

```bash
# Full project analysis
python src/cli/main.py analyze research_review/pending/PROJECT_NAME --level premium

# Single file analysis  
python src/cli/main.py analyze research_review/pending/PROJECT_NAME/specific_file.py --level enhanced

# Move after analysis
mv research_review/pending/PROJECT_NAME research_review/analyzed/
```

## Analysis History

<!-- Add your analysis entries below this line -->
