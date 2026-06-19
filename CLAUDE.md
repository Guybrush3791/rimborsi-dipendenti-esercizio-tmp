# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Flask web app for HR expense reimbursement management (normativa 2025, Circolare MEF n. 41/2024). On each submission the app validates the request, computes the IRPEF-exempt and taxable split, enforces the employee's monthly exemption cap (€1 200), and persists everything to a flat JSON file.

## Documentation

- [doc/playbook-nixos.md](doc/playbook-nixos.md) — how to install dependencies, run the app, and execute tests on NixOS (nix-shell, optional shell.nix)
- [doc/architecture.md](doc/architecture.md) — module breakdown, dependency graph, Flask routes, and the write pipeline in `app._registra()`
- [doc/data.md](doc/data.md) — full record schema for `data/richieste.json`, field semantics, and storage constraints (immutability, derived cap state)
- [doc/tests.md](doc/tests.md) — test file responsibilities, fixture strategy, and coverage gaps