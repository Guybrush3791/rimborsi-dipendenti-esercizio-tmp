# NixOS Playbook

Common operations for developing and running this project on NixOS. The login shell is **fish**. All commands run on the **host** — not inside the AI cage.

## 1. Enter a development shell

The project has no `shell.nix` or `flake.nix`. Use an ad-hoc `nix-shell` that provides Python 3.12 and the two runtime dependencies:

```fish
# from the project root
nix-shell -p python312 python312Packages.flask python312Packages.pytest
```

`nix-shell` drops you into bash by default. To stay in fish:

```fish
nix-shell -p python312 python312Packages.flask python312Packages.pytest --run fish
```

Alternatively, declare a permanent `shell.nix` in the project root (one-time setup — see §6).

---

## 2. Install Python dependencies

Inside the nix-shell all packages are already available via the Nix-provided wheels; `pip install` is not needed. If you prefer a virtualenv for editor tooling (LSP, type checkers):

```fish
python -m venv .venv
source .venv/bin/activate.fish   # fish activation script, not activate
pip install -r requirements.txt
```

> The virtualenv approach pins exact wheel versions; the nix-shell approach tracks nixpkgs. Either works for day-to-day development.

---

## 3. Run the application

```fish
flask --app src.app run
```

The app starts on <http://127.0.0.1:5000>. `data/richieste.json` is created automatically on the first request if it does not exist.

To enable auto-reload during development:

```fish
flask --app src.app run --debug
```

---

## 4. Run the test suite

```fish
pytest
```

Run a single test file:

```fish
pytest tests/test_calculator.py
```

Run a single test by node ID:

```fish
pytest tests/test_calculator.py::TestCalcola::test_plafond_incapiente_limita_la_quota_esente
```

Verbose output:

```fish
pytest -v
```

`pyproject.toml` already sets `pythonpath = ["."]` and `testpaths = ["tests"]`, so no extra flags are needed for import resolution.

---

## 5. Reset data

All state lives in a single file. Delete it to start fresh:

```fish
rm data/richieste.json
```

---

## 6. Permanent `shell.nix` (optional, recommended)

Drop this file in the project root to avoid repeating the `nix-shell -p` invocation. Include `shellHook` to automatically relaunch as fish:

```nix
# shell.nix
{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  packages = [
    pkgs.python312
    pkgs.python312Packages.flask
    pkgs.python312Packages.pytest
  ];

  shellHook = ''
    exec ${pkgs.fish}/bin/fish
  '';
}
```

Then just run:

```fish
nix-shell   # from the project root — drops you into fish
```

If the repo uses Nix flakes, the equivalent `devShell` goes in `flake.nix` under `outputs.devShells.default`.

---

## 7. CI (GitHub Actions)

The workflow at `.github/workflows/ci.yml` runs on every push to `main` and on all pull requests. It uses `actions/setup-python@v5` with Python 3.12, installs `requirements.txt`, then runs `pytest -v`. No NixOS-specific steps are needed in CI.
