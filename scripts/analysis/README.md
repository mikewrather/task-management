# Analysis Scripts

This directory contains scripts for analyzing system performance, logs, and usage patterns.

## Available Scripts

### `analyze-voice-runs.py`
Analyzes voice processing runs from logs to provide statistics on:
- Success rates
- Processing times
- Common errors
- File processing patterns

### `quick-summary.sh`
Provides a quick summary of system status including:
- Recent processing activity
- Current file counts
- Error summaries

## Usage

```bash
# Analyze recent voice processing runs
python scripts/analysis/analyze-voice-runs.py

# Get quick system summary
./scripts/analysis/quick-summary.sh
```

## Output

Analysis results are typically displayed in the terminal with rich formatting for easy reading.