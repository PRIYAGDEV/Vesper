# Contributing to Vesper 🌙

Thank you for considering contributing to Vesper! We welcome community contributions, bug reports, feature requests, and documentation improvements.

---

## 🛠️ Local Development Setup

1. **Fork and Clone the Repository**:
   ```powershell
   git clone https://github.com/YOUR-USERNAME/Vesper.git
   cd Vesper
   ```

2. **Create a Virtual Environment**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Download Local Model**:
   ```powershell
   python download_small.py
   ```

5. **Run the App**:
   ```powershell
   python main.py
   ```

---

## 🧪 Testing

Before submitting a pull request, ensure all tests pass:

```powershell
python tests/test_hotkey.py
python tests/test_cleanup.py
python tests/test_injector.py
python tests/test_audio.py
python tests/test_full_pipeline.py
```

---

## 📝 Pull Request Guidelines

1. Create a focused branch (`git checkout -b feature/my-feature` or `fix/my-fix`).
2. Adhere to PEP 8 Python conventions and maintain clean code readability.
3. If introducing new dependencies, verify licenses and explain the rationale in your PR description.
4. Ensure all existing tests pass and add new tests when adding functionality.
5. Submit your PR against the `main` branch.

---

## 💬 Community & Code of Conduct

Please be respectful, kind, and constructive in all discussions, issues, and code reviews. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details.
