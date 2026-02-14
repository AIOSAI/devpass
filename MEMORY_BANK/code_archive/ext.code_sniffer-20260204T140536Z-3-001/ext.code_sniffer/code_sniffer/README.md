# Research Code Review Space

This directory is designed for tracking and analyzing research codebases with the AIPass-Code-Sniffer.

## Directory Structure

```,
research_review/
├── pending/          # Drop new research code here for analysis
├── analyzed/         # Completed analyses with ability cards
├── tracking.md       # Analysis tracking log
└── README.md         # This file
```

## Workflow

### 1. Add Research Code

Drop research codebases into `pending/` directory:

```bash
# Example: Clone a research project
cd research_review/pending
git clone https://github.com/example/research-project
```

### 2. Analyze with AI

Run comprehensive analysis:

```bash
# Analyze specific research project
python src/cli/main.py analyze research_review/pending/project-name --level premium

# Quick analysis
python src/cli/main.py analyze research_review/pending/project-name --level enhanced
```

### 3. Move to Analyzed

After analysis, move to `analyzed/` directory:

```bash
mv research_review/pending/project-name research_review/analyzed/
```

### 4. Track Progress

Update `tracking.md` with analysis results and insights.

## Analysis Levels

- **`basic`** - Fast syntax analysis for quick overview
- **`enhanced`** - AI summaries and key insights
- **`premium`** - Full AI analysis with quality scoring and business context

## Output Location

All ability cards are generated in `output/ability_cards/` with timestamped folders for each analysis session.

## Tips

- Use descriptive folder names for research projects
- Run premium analysis for detailed insights
- Check `tracking.md` for analysis history
- Archive old projects periodically
