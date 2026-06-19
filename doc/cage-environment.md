# Cage environment

Read this once when you start a **new project** inside the ai-cage. It is the
same sandbox for every repo, so its limits never change project to project —
this note is the standing answer so the operator doesn't re-explain them.

It is a *reference* (what exists, what runs, what's absent). The *rules* for
how to behave live in [[llm-rules]]; the *why* lives in [[architecture/cages]].
When this note and [[llm-rules]] disagree, [[llm-rules]] wins.

> [!summary] One line
> You are a `systemd-nspawn` container with no privileges, a slim toolset, and
> exactly one writable surface: the project repos under `/projects/`. Anything
> requiring the host — `sudo`, `nixos-rebuild`, `systemctl`, builds, commits on
> a locked `.git` — you hand back to the operator as text.

## Filesystem — what you can touch

Only paths under `/projects/` exist for you. They are bind-mounts of real host
repos, re-presented through the user namespace (`:idmap`) so your `ai` user
owns them.

| Surface | Access | Notes |
|---|---|---|
| `/projects/<repo>` | **read-write** | The audited project repos. Edit freely. |
| `/projects/<repo>/<subtree>` | **read-only** | Refactor *source* subtrees — read FROM, never write. Writes fail with `EROFS`. |
| `/projects/<repo>/.git` | **read-only** | A host ACL denies write to your UID — see below. |
| `/home/ai` | read-write | Your container home (`0750`). Holds Claude Code config + memory. Persists, but is **not** a project surface — don't stash work here. |

The exact repo list (which are RW, which subtrees are RO) is declared in
`modules/ai-cage/default.nix` — `sharedProjects` (rw) and `readonlySources`
(ro). Treat that file as the source of truth; it changes as projects are
added, this note does not.

**What is simply not there:** there is no host filesystem behind the mounts.
`/home/guybrush`, `/etc/nixos`, `/run/secrets`, `/var/lib/*`, vault mounts, key
material — none of it exists in the cage. Don't search for it, don't ask the
operator to bind it in; that absence *is* the security model
([[architecture/cages]]). If a task seems to need a host path, surface that —
don't try to reach it.

### `.git` is read-only

A host-side ACL lets you **read** git history but not mutate `.git`:

- Reads work: `git status`, `log`, `diff`, `show`, `blame`, `branch`, etc.
  (`GIT_OPTIONAL_LOCKS=0` is set so `git status` won't try to take
  `.git/index.lock`).
- Writes may fail: `git add`, `commit`, `tag`, `stash`, branch creation. On
  some hosts even `git add` is blocked.
- `git push` / `git pull` / `git fetch` are **forbidden** regardless of the ACL
  (network + host credentials).

When a git write fails, **don't work around it** — print the exact commands for
the operator to run on the host. Commits come from the host, by design.

## Commands you have

Standard NixOS base userland is present — `coreutils` (ls, cat, cp, mv, rm,
mkdir, …), `findutils`, `grep`, `sed`, `gawk`, `tar`, `gzip`, `which`, `less`,
and the like — plus this explicitly-provisioned toolset (from
`modules/ai-cage/container.nix`, `environment.systemPackages`):

| Tool | Use |
|---|---|
| `fish` | Your interactive login shell (you start in `/projects`). |
| `bashInteractive` (`bash`) | The shell Claude Code invokes for command execution; scripting language. |
| `git` | Version control — **reads only** (see `.git` note above). |
| `gh` | GitHub CLI — read operations. Anything that mutates a remote needs auth/network policy; prefer handing PR/push steps to the operator. |
| `curl` | HTTP client (egress is open — see Network). |
| `openssl` | TLS/crypto CLI. |
| `cacert` | CA bundle (makes TLS work for curl/git/node). |
| `jq` | JSON query/transform. |
| `yq` | YAML query/transform. |
| `nodejs_22` | Node.js 22 — provides `node`, `npm`, `npx`. The only language runtime present. |
| `tree` | Directory tree view. |
| `claude-code` | You. |
| `mcp-nixos` | Backs the `nixos` MCP server for nixpkgs/option lookups — see Network. |

That is the whole specialized inventory. **Nothing else is installed**: no
Python, Go, Rust, Ruby, or other language runtime; no compilers/build
toolchains beyond what Node ships; no Docker/Podman/`machinectl`; no editors
beyond what you drive through your own tools. If a task needs a tool that
isn't here, say so — don't assume it exists, and don't try to install one
system-wide (you can't; see below).

## Commands and actions you do NOT have

These either don't exist in the cage or are deliberately disabled. **Never
invoke them via a tool call.** When a task needs one, print it in a fenced
block prefaced with **"Run on the host:"** and, if you need its output, ask the
operator to paste it back.

| Forbidden / absent | Why |
|---|---|
| `sudo`, `sudo-rs` | Disabled (`security.sudo.enable = false`). No privilege escalation exists in the cage. |
| `nixos-rebuild`, flakes-enabled `nix` | Builds/activation are host-only. You can't build — you verify by reading. |
| `systemctl`, `machinectl`, `journalctl` | Service/unit/log control is host-only; the host paths aren't reachable from here anyway. |
| `git push` / `pull` / `fetch`, and `.git` writes | Commits and remote sync come from the host (see `.git` note). |
| Installing packages (`nix-env`, global `npm -g`, etc.) | The system closure is declarative; you can't add to it. Need a tool? Ask for a module change, run on the host. |
| Reading/writing anything outside `/projects/*` | Those paths don't exist in the cage. |
| Entering or driving the **danger-cage** | The foreign-code VM is the operator's tool. Route un-audited code to `danger run`/`danger review` — never into `/projects/`. |

> [!warning] Verify, don't build
> You cannot compile or activate this config. Verification is by reading:
> options are real, no double-assignment, import graph intact. End a change by
> printing the operator-run gates from [[llm-rules]] §6.

## Network

Egress is **open and unrestricted**, leaving on the ISP link (not the VPN) —
enough for `git`, `gh`, `npm`, the Anthropic API, and the `nixos` MCP. There is
**no outbound filtering**; the protection model is filesystem scoping, not
network policy ([[architecture/cages]]).

Inbound is **default-deny**: the cage runs no listening services, and anything
you might start (a dev server, `python -m http.server`) is unreachable from the
host or beyond. Don't rely on inbound connectivity.

During a security incident the operator can run `lockdown panic`, which clamps
cage egress to the Anthropic API only ([[custom-scripts/lockdown]]) — if network
calls suddenly fail, that may be why; surface it rather than retrying blindly.

### The `nixos` MCP

For any nixpkgs package, NixOS/home-manager option, channel, or store-path
question, use the `nixos` MCP server (backed by `mcp-nixos`). It queries live
APIs and is more current than your training data — prefer it over guessing or
over running `nix search` (which you can't build with anyway).