# Contributing to StudyMind

🎉 Thank you for considering contributing to this project! We welcome contributions from everyone.

## 🤝 How to Contribute

### Reporting Bugs

1. **Check existing issues**: Ensure the bug hasn't already been reported
2. **Create new issue**: Use the bug report template
3. **Provide details**: 
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots if applicable
   - Environment information

### Suggesting Features

1. **Check existing features**: Ensure the feature hasn't been suggested
2. **Create new issue**: Use the feature request template
3. **Explain benefits**: Describe how this feature would help users

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Follow coding standards**: See [AGENTS.md](AGENTS.md) for detailed guidelines
4. **Write tests**: Ensure all new code is tested
5. **Commit changes**: Use descriptive commit messages
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Open Pull Request**: Link to relevant issues

## 🛠️ Development Setup

### Prerequisites

- Python 3.10+
- Ollama installed locally
- Node.js (for frontend development)

### Local Development

1. **Clone repository**
   ```bash
   git clone https://极github.com/ravikumarve/studymind.git
   cd studymind
   ```

2. **Set up Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

### Docker Development

```bash
# Build and start containers
docker-compose up -d --build

# View logs
docker-compose logs -f
```

## 📝 Code Standards

### Python Code
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use descriptive variable and function names

### JavaScript Code
- Use ES6+ features
- Follow consistent naming conventions
- Use comments for complex logic

### Documentation
- Update README.md for new features
- Keep AGENTS.md updated with architectural changes
- Comment complex code sections

## 🧪 Testing

- Write tests for all new functionality
- Ensure existing tests pass
- Use pytest for Python tests
- Test both success and error cases

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=app --cov-report=term-missing tests/

# Run specific test file
pytest tests/test_explain.py -v
```

## 🔄 Pull Request Process

1. **Ensure tests pass**: All tests must pass
2. **Update documentation**: Include relevant documentation updates
3. **Follow coding standards**: Adhere to project guidelines
4. **Describe changes**: Provide clear description of changes
5. **Reference issues**: Link to any related issues

## 🎯 Good First Issues

Look for issues labeled `good first issue` if you're new to the project:

- Documentation improvements
- Bug fixes with clear reproduction steps
- Small feature enhancements
- Test coverage improvements

## 📞 Communication

- Use GitHub issues for bug reports and feature requests
- Be respectful and inclusive in all communications
- Ask questions if you're unsure about anything

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.