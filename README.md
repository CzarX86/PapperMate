# PapperMate 🚀

**Intelligent Contract Entity Extraction System**

PapperMate is an advanced system for extracting entities from contracts using local NLP processing, intelligent PDF conversion, and Google Cloud Translation API for multilingual support.

## ✨ Features

- **PDF to JSON/Markdown conversion** using Marker
- **Multilingual filename support** with Google Cloud Translation API v3
- **Local NLP processing** for entity extraction
- **Contract hierarchy management** and relationship detection
- **Duplicate detection** and incremental learning
- **Demand/obligation extraction** from contract text
- **Annotation interface** for manual corrections

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Poetry (dependency management)
- Google Cloud account with Translation API enabled

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/PapperMate.git
cd PapperMate
```

2. **Install dependencies:**
```bash
poetry install
```

3. **Setup Google Cloud Translation API:**
```bash
# Follow the detailed setup guide in TRANSLATION_SETUP.md
# Or run the quick setup script:
./setup_google_quotas.sh
```

4. **Configure environment:**
```bash
# Set your Google Cloud project ID
export GOOGLE_CLOUD_PROJECT="your-project-id"

# Set the service account key path
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/pappermate-translate-key.json"
```

### Testing the System

1. **Run the translation system test:**
```bash
poetry run python test_translation_system.py
```

2. **Run all tests:**
```bash
poetry run pytest tests/
```

3. **Run integration tests (with real PDFs):**
```bash
poetry run pytest tests/ -m integration
```

## 🔧 Configuration

### Google Cloud Translation API Setup

The system uses Google Cloud Translation API v3 with OAuth2 authentication via Service Account.

**Required quotas:**
- `Number of v2 default requests per minute per user`: 1,000
- `v2 and v3 general model characters per minute per user`: 50,000
- `v2 and v3 general model characters per day`: 100,000

**Service Account permissions:**
- `roles/cloudtranslate.user`

See `TRANSLATION_SETUP.md` for detailed configuration steps.

### Environment Variables

```bash
# Required
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json

# Optional
PAPPERMATE_SKIP_TABLES=1  # Skip table processing if needed
```

## 📁 Project Structure

```
PapperMate/
├── src/pappermate/
│   ├── config/          # Configuration management
│   ├── services/        # Core services (PDF, translation, NLP)
│   ├── models/          # Data models and schemas
│   └── utils/           # Utility functions
├── tests/               # Test suite
├── Marker_PapperMate/   # Modified Marker library
└── docs/                # Documentation
```

## 🧪 Testing Strategy

### Test Categories

1. **Unit Tests** (`tests/`): Individual component testing
2. **Integration Tests** (`tests/`): End-to-end workflow testing
3. **Translation Tests** (`test_translation_system.py`): API integration validation

### Running Tests

```bash
# All tests
poetry run pytest

# Specific test category
poetry run pytest tests/ -m unit
poetry run pytest tests/ -m integration

# With coverage
poetry run pytest --cov=src tests/
```

## 🔍 Troubleshooting

### Common Issues

1. **Google Cloud API errors:**
   - Verify quotas are set correctly
   - Check service account permissions
   - Ensure API is enabled

2. **Translation failures:**
   - Check network connectivity
   - Verify API key configuration
   - Review error logs in reprocessing queue

3. **PDF processing errors:**
   - Check file permissions
   - Verify PDF integrity
   - Review Marker library configuration

### Debug Mode

```bash
# Enable debug logging
export PAPPERMATE_DEBUG=1

# Run tests with verbose output
poetry run pytest -v -s
```

## 📊 Milestones

### ✅ Milestone 1: Core Infrastructure (COMPLETED)
- [x] PDF conversion with Marker
- [x] Google Cloud Translation API v3 integration
- [x] Multilingual filename support
- [x] Basic testing framework
- [x] Service account authentication

### 🚧 Milestone 2: Contract Processing (IN PROGRESS)
- [ ] Contract entity extraction
- [ ] NLP pipeline implementation
- [ ] Contract hierarchy detection
- [ ] Duplicate detection system

### 📋 Milestone 3: Advanced Features
- [ ] Incremental learning
- [ ] Demand/obligation extraction
- [ ] Annotation interface
- [ ] Performance optimization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Marker PDF](https://github.com/datalab-to/marker) for PDF conversion
- [Google Cloud Translation API](https://cloud.google.com/translate) for multilingual support
- [spaCy](https://spacy.io/) for NLP processing

---

**Made with ❤️ for intelligent contract management**




