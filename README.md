![Automathemely icon](https://git.redpie.nl/EmperorAndFoolICT-Mediaproductie/automathemely12v2/raw/branch/main/share/icons/hicolor/scalable/apps/automathemely.svg)

# AutomaThemely (fork)

**A fork of** [https://github.com/C2N14/AutomaThemely](https://github.com/C2N14/AutomaThemely) — a small utility to switch desktop themes at sunrise/sunset and run small user scripts.  
This fork packages development conveniences, a split repo/venv workflow, improved scheduler restart handling, and a more robust logging/restart behavior.

tested on Ubuntu Studio 24.04

---

## Improvements

- One-click theme change from management UI.
    
- Robust restart and logging for scheduler process.
    
- Rotating log handler to limit log growth.
    
- Desktop launchers and systemd user timers included for easy user install.
    
- Better diagnostics: parent env markers, PID logging, immediate-crash detection.

---    
![GUI show](https://git.redpie.nl/EmperorAndFoolICT-Mediaproductie/automathemely12v2/raw/branch/main/share/AutothGUI2026.png)
---
## Install as a *user* (development-friendly)

> All commands below assume you run them as your user (no sudo) and adapt the paths if needed.

### 1) Create venv & install deps

```bash
python3 -m venv {VENV_DIR}
{VENV_DIR}/bin/pip install --upgrade pip
cd {REPO_DIR}
{VENV_DIR}/bin/pip install -r requirements.txt
# optional, to use repo as editable package (recommended for dev)
HOME_VENV={VENV_DIR}
$HOME_VENV/bin/pip uninstall -y automathemely || true   # remove stray installed copies if present
$HOME_VENV/bin/pip install -e .
````

### 2) Make sure repo package exists

Ensure repo contains a package at:

```
{REPO_DIR}/automathemely/
# that directory must contain __init__.py and bin/, autoth_tools/, lib/, etc.
```

If not present, copy the repo tree contents into `automathemely/` so `import automathemely` resolves to the repo.

### 3) Desktop launchers (user install)

Copy the packaged `.desktop` files and icons to user locations:

```bash
mkdir -p ~/.local/bin ~/.local/share/applications ~/.local/share/icons/hicolor/48x48/apps
# (make your DevOp executable readable/executable)
chmod +x {DEV_EXEC}
cp -a {DEV_EXEC} ~/.local/bin/automathemely
# desktop
cp -a {REPO_DIR}/share/installation_files/*.desktop ~/.local/share/applications/
# icons: put svg/png into hicolor dirs
cp -a {REPO_DIR}/automathemely/lib/automathemely_large.svg \
     ~/.local/share/icons/hicolor/48x48/apps/automathemely.svg
# refresh caches (optional)
gtk-update-icon-cache ~/.local/share/icons/hicolor || true
update-desktop-database ~/.local/share/applications || true
hash -r
```


### 4) systemd user units (timers)

Install and enable the provided user units:

```bash
mkdir -p ~/.config/systemd/user
cp -a share/installation_files/autothscheduler-start.service ~/.config/systemd/user/
cp -a share/installation_files/sun-times.service share/installation_files/sun-times.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now sun-times.timer
systemctl --user enable --now autothscheduler-start.service
# view status:
systemctl --user status sun-times.timer autothscheduler-start.service
journalctl --user -u sun-times.service -n 200 --no-pager
```

---

## How to run manually (dev)

Activate venv and run scheduler from repo:

```bash
source {VENV_DIR}/bin/activate
cd {REPO_DIR}
export PYTHONPATH="$PWD"
# start scheduler via run module:
python -m bin.run --restart
# or run scheduler script directly:
python -u bin/autothscheduler.py
```

Verify:

```bash
pgrep -af autothscheduler.py
tail -n 200 ~/.config/automathemely/.autothscheduler.log
```

---

## Status (current)

* Local development repo layout: `{REPO_DIR}`
* Virtualenv (example): `{VENV_DIR}`
* The scheduler runs via `bin/run.py` → spawns `bin/autothscheduler.py`.
* Improvements added:

  * Robust `Restart` block with atomic child stdout/stderr, pid logging, immediate-crash detection.
  * `RotatingFileHandler` for `.autothscheduler.log` (1 MB, 7 backups by default).
  * Desktop `.desktop` launchers for dev (activate venv, `PYTHONPATH`), and portable packaged variants.
  * Installable `systemd` user units / timers under `share/installation_files/`.
  * One-click theme change in management UI.
* Known: `tzlocal` warns if system timezone config is ambiguous. We left TZ handling to the environment (recommended to set `TZ` for deterministic behavior).

---

## Quick goals

* Keep **code** inside repo (`automathemely/`), keep **environment** in the venv.  
* Keep `share/installation_files/` for packaging (desktop files, systemd units, icons).

---


## Notes about restart/logging behavior

- Restart now spawns a detached child with stdout/stderr atomically redirected into `~/.config/automathemely/.autothscheduler.log`.
    
- The restart logic writes a small `=== parent spawn attempt` marker to the log for diagnostics and logs child PID.
    
- `__init__.py` now configures a `RotatingFileHandler` for `.autothscheduler.log` (default: 1MB, 7 backups). Change these values in `automathemely/__init__.py` if desired.
    
- Immediate-crash detection writes an exit marker if the child dies immediately.
    

---

## Known issues / caveats

- `tzlocal` may warn if `/etc/timezone` and `/etc/localtime` disagree; you can set `TZ='Europe/Berlin'` in your environment or in the launcher to avoid warnings.
    
- If an installed `automathemely` package exists in the venv `site-packages`, Python may import that copy — remove or uninstall it during dev.
    
- Dev `.desktop` files contain absolute paths and venv activation for convenience; packaged files should use `automathemely` on `$PATH` and theme icons.
    

---

## Contributing / packaging notes

- Keep `share/installation_files/` as the source for systemd units and desktop files. The installer should copy these into proper system/user locations.
    
- Keep `DevOp/` for development helpers (executable wrappers). Packaged executables should be separate and installed into `/usr/bin` or `~/.local/bin`.
    

---

## References

- Original project: [https://github.com/C2N14/AutomaThemely](https://github.com/C2N14/AutomaThemely)
    
- This repo: `{REPO_DIR}`
    

---

