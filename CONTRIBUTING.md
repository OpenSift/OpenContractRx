# Contributing to OpenContractRx

- Thanks for contributing 💙

## Ground rules
- Be kind, professional, and constructive.
- Prefer small PRs.
- Add tests for new behavior when reasonable.
- Keep security + privacy in mind (hospitals have strict requirements).

## Dev setup
```bash
cp .env.example .env
docker compose up --build
```

## Code style
- Python: ruff + black (to be added in CI)
- Type hints required for public functions
- Prefer pydantic schemas in packages/core

## PR checklist
- Clear description and rationale
- Tests updated/added (if applicable)
- Docs updated (if behavior changes)
- No secrets in code or logs

## Reporting security issues

- See SECURITY.md.