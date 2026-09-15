# Anvil Reactive

Automatic client-side updates for Anvil apps.

## Install

Add third-party dependency `N7KFE4YBWMGWJ5OX` to your Anvil app, then import
from `anvil_reactive.main`.

See the [installation guide](https://anvilistas.github.io/reactive/installation/)
and [quick start](https://anvilistas.github.io/reactive/quick-start/).

## Documentation

The [documentation site](https://anvilistas.github.io/reactive/) covers tracking,
signals and reactive classes, computed values and effects, reactive collections,
component bindings, server calls inside effects, and the complete API.

## Examples

See the [quick start](https://anvilistas.github.io/reactive/quick-start/) and the original
[Anvil Community Forum post](https://anvil.works/forum/t/anvil-reactive-add-reactivity-to-your-anvil-apps/19526).

## Develop

Use `uv` to run the pinned development tools and install Chromium:

```shell
uv run --isolated --with-requirements requirements-dev.txt \
  playwright install chromium
```

Run the CPython tests, real App Server client suite, and documentation build:

```shell
PYTHONPATH=. uv run --isolated --with-requirements requirements-dev.txt \
  pytest -q tests
PYTHONPATH=. uv run --isolated --with-requirements requirements-dev.txt \
  pytest -q client_tests/test_client.py
uv run --isolated --with-requirements requirements-dev.txt \
  mkdocs build --strict
```

The client suite requires Java 21 and starts `anvil-app-server==1.17.0` in a
temporary workspace. On Apple Silicon it also uses Docker for PostgreSQL.

## Publish documentation

GitHub Pages publishes the MkDocs site at
<https://anvilistas.github.io/reactive/>. The repository uses **Settings > Pages >
Build and deployment > Source: GitHub Actions**.

Merge documentation changes into `main` to deploy automatically. Once the
deployment workflow is on `main`, you can also start it with the GitHub CLI:

```shell
gh workflow run deploy-docs.yml --ref main
gh run list --workflow deploy-docs.yml --limit 1
```

Use `gh run watch <run-id> --exit-status` to follow that deployment. The built
site includes `llms.txt` at its root; contributor plans and research notes are
excluded from publication.
