# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Local & Offline Privacy Guarantee

**Vesper** is built around a 100% offline-first architecture:
- Zero audio recordings or transcriptions are transmitted over the internet.
- Speech recognition runs locally using quantized CTranslate2 Whisper models.
- No third-party telemetry, remote analytics, or cloud APIs are used.

## Verifying Prebuilt Binaries

To ensure your copy of `Vesper.exe` is authentic and unmodified, always verify its SHA-256 checksum against the official release hashes:

```powershell
Get-FileHash .\Vesper.exe -Algorithm SHA256
```

Compare the output hash with the one published in [`checksums.txt`](https://github.com/PRIYAGDEV/Vesper/releases/latest).

## Reporting a Vulnerability

If you discover a potential security vulnerability in Vesper, please responsibly disclose it by opening a private security advisory on GitHub or sending an email to the repository maintainer rather than opening a public issue.

We will review, patch, and release an update as promptly as possible.
