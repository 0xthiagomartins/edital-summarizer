# Developer Guide

## Project Structure

```
edital_summarizer/
├── docs/                    # Documentation
│   ├── DEVELOPERS.md       # This file
│   └── demos/              # Demo scripts
├── samples/                # Sample bidding documents
│   └── edital-xxx/        # Sample files
├── src/                    # Source code
│   └── edital_summarizer/
│       ├── config/         # YAML configurations
│       │   ├── agents.yaml # Agent definitions
│       │   └── tasks.yaml  # Task definitions
│       ├── tools/          # Custom tools
│       │   └── document_extractor.py
│       ├── crew.py        # CrewAI implementation
│       └── main.py        # CLI entry point
└── pyproject.toml         # Project configuration
```

## Development Setup

1. Install UV (recommended package manager):
```bash
pip install uv
```

2. Create and activate virtual environment:
```bash
uv venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
uv pip install -r requirements.txt
```

4. Set up your environment variables in `.env`:
```env
MODEL=gemini/gemini-1.5-flash
GEMINI_API_KEY=your_api_key_here
```

## Key Components

### 1. Document Extractor
- Located in `tools/document_extractor.py`
- Handles extraction from PDF, TXT, MD files and ZIP archives
- Processes directories recursively

### 2. CrewAI Agents
- Configured in `config/agents.yaml`
- Three main agents:
  - Metadata Extractor
  - Executive Summary Generator
  - Technical Summary Generator
- Supports multiple languages (pt-br, en)

### 3. Tasks
- Configured in `config/tasks.yaml`
- Main tasks:
  - Metadata extraction
  - Executive summary generation
  - Technical summary generation
- Language-specific prompts

### 4. CLI Interface
- Implemented in `main.py`
- Uses Typer for CLI argument parsing
- Supports various options:
  - Input directory
  - Output file
  - Summary types
  - Language selection
  - Verbose mode

## Running Tests

```bash
pytest tests/
```

## Adding New Features

### Adding a New Agent
1. Add configuration to `config/agents.yaml`:
```yaml
new_agent:
  role: "Role Name"
  goal:
    en: "Goal in English"
    pt-br: "Goal in Portuguese"
  backstory:
    en: "Backstory in English"
    pt-br: "Backstory in Portuguese"
  verbose: true
```

2. Update `DocumentSummarizerCrew` in `crew.py` if needed

### Adding a New Task
1. Add configuration to `config/tasks.yaml`:
```yaml
new_task:
  description:
    en: "Task description in English"
    pt-br: "Task description in Portuguese"
```

2. Update task handling in `crew.py`

### Supporting a New File Type
1. Add extraction method to `DocumentExtractor` class
2. Update `process_directory()` method to handle the new type

## Common Issues & Solutions

1. **PDF Extraction Issues**
   - Ensure PDF is not encrypted
   - Check if text is extractable (not scanned)
   - Consider using OCR for scanned documents

2. **Memory Usage**
   - Process large files in chunks
   - Monitor RAM usage with large directories

3. **API Rate Limits**
   - Implement retry mechanism
   - Add delay between API calls

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Run tests
5. Submit pull request

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release tag
4. Build and publish package 