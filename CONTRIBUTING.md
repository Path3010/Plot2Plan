# Contributing Guide

## Branching Strategy

This project uses a Git Flow-like branching strategy:

```
master (production)
  │
  └── develop (integration)
        │
        ├── feature/dxf-parser
        ├── feature/setback-engine
        ├── feature/room-generator
        └── ...
```

### Branches

| Branch | Purpose |
|--------|---------|
| `master` | Production-ready code only |
| `develop` | Integration branch for features |
| `feature/*` | New feature development |
| `bugfix/*` | Bug fixes |
| `release/*` | Release preparation |

### Workflow

1. **Start a new feature:**
   ```bash
   git checkout develop
   git checkout -b feature/your-feature-name
   ```

2. **Work on your feature:**
   ```bash
   # Make changes
   git add .
   git commit -m "feat: description of change"
   ```

3. **Merge back to develop:**
   ```bash
   git checkout develop
   git merge feature/your-feature-name
   git branch -d feature/your-feature-name
   ```

4. **Create a release:**
   ```bash
   git checkout develop
   git checkout -b release/v1.0.0
   # Final testing and version bumps
   git checkout master
   git merge release/v1.0.0
   git tag v1.0.0
   ```

## Commit Messages

Use conventional commits format:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Formatting
- `refactor:` Code restructuring
- `test:` Tests
- `chore:` Maintenance

## Code Formatting

### Python (Backend)
```bash
cd backend
black .
isort .
```

### TypeScript (Frontend)
```bash
cd frontend
npm run lint
npx prettier --write .
```

## Running Tests

### Backend
```bash
cd backend
pytest
```

### Frontend
```bash
cd frontend
npm test
```
