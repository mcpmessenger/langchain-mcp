# Documentation

This directory contains the documentation for the LangChain Agent MCP Server.

## Building Locally

### Install MkDocs

```bash
pip install mkdocs-material
pip install mkdocs-git-revision-date-localized-plugin
```

### Serve Locally

```bash
mkdocs serve
```

Visit: http://127.0.0.1:8000

### Build Static Site

```bash
mkdocs build
```

Output will be in the `site/` directory.

## Publishing

Documentation is automatically published to GitHub Pages when changes are pushed to the `main` branch.

Manual publish:
```bash
mkdocs gh-deploy
```

## Structure

- `index.md` - Homepage
- `getting-started.md` - Setup guide
- `examples.md` - Code examples and tutorials
- `deployment.md` - Deployment instructions
- `api-reference.md` - API documentation
- `troubleshooting.md` - Common issues and solutions

