"""
Minimal decman configuration for a fresh Arch Linux install.

Safe defaults:
- Only a small set of core packages is declared
- NetworkManager is enabled but not started automatically
- One simple config file is managed as an example

Notes:
- Decman removes explicitly installed packages that are NOT listed here (unless added to ignored_packages).
  Make sure to add everything you want to keep to decman.packages or decman.ignored_packages.
- Files created by decman are removed if you later delete them from this source.
- Decman runs this file as root and executes it from the directory where this file resides.
  Relative paths below are relative to this file.
- For AUR packages (if you add any), ensure /tmp has enough space; building happens in a chroot.
"""

import decman
from decman import File  # Add Directory, Module later if needed

# --- Packages ---
# Pacman packages you want explicitly installed on this system.
# Keep this minimal at first; add more as you go.
decman.packages += [
    "git",
    "networkmanager",
    "msedit",      # editor example; change/remove as you like
    "curl",
    # Required for building AUR packages in a clean chroot via devtools
    "devtools",
]

decman.aur_packages += ["decman", "protonvpn"]

# Packages you want decman to ignore (won't install or remove).
# Useful for tools you prefer to manage manually.
decman.ignored_packages += [
     "yay",
]

# --- AUR packages ---
# To let decman manage itself from AUR after it's installed:
# decman.aur_packages += ["decman"]

# If you add AUR packages that require PGP verification and you have custom keys,
# you can configure the build user and GPG home like this:
# import os, decman.config
# os.environ["GNUPGHOME"] = "/home/youruser/.gnupg"
# decman.config.makepkg_user = "youruser"

# --- Files ---
# Example: ensure console keymap
# Tip: If you later add more files, relative paths are resolved from this file's directory.
decman.files["/etc/vconsole.conf"] = File(content="KEYMAP=us", encoding="utf-8")

# --- Directories ---
# Example (uncomment and adjust) to copy a dotfiles dir recursively to target:
# from decman import Directory
# decman.directories["/home/youruser/.config/app/"] = Directory(
#     source_directory="./files/app-config", owner="youruser"
# )

# --- Pacman guard (reminder to use decman) ---
# This pre-transaction pacman hook blocks manual installs (pacman -S / -U) unless
# explicitly bypassed. It reminds you to update your decman source instead.
# Decman-triggered installs are allowed automatically.
decman.files["/etc/pacman.d/hooks/decman-guard.hook"] = File(
  content=(
    "[Trigger]\n"
    "Operation = Install\n"
    "Operation = Remove\n"
    "Type = Package\n"
    "Target = *\n"
    "\n"
    "[Action]\n"
    "Description = Block manual pacman installs/removals (use decman)\n"
    "When = PreTransaction\n"
    "Exec = /usr/local/bin/decman-guard\n"
  ),
  encoding="utf-8",
)

decman.files["/usr/local/bin/decman-guard"] = File(
  content=(
    "#!/usr/bin/env bash\n"
    "set -euo pipefail\n"
    "\n"
    "check_tree() {\n"
    "  local p=$PPID\n"
    "  local depth=0\n"
    "  while [[ $p -gt 1 && $depth -lt 10 ]]; do\n"
    "    if grep -qa 'decman' \"/proc/$p/cmdline\" 2>/dev/null; then\n"
    "      return 0\n"
    "    fi\n"
    "    p=$(awk '{print $4}' \"/proc/$p/stat\" 2>/dev/null || echo 1)\n"
    "    depth=$((depth+1))\n"
    "  done\n"
    "  return 1\n"
    "}\n"
    "\n"
    "# Allow explicit one-off bypass\n"
    "if [[ \"${DECMAN_ALLOW:-}\" == \"1\" ]]; then\n"
    "  exit 0\n"
    "fi\n"
    "\n"
    "# Allow when pacman was invoked by decman itself\n"
    "if check_tree; then\n"
    "  exit 0\n"
    "fi\n"
    "\n"
    "cat >&2 <<'EOF'\n"
    "Manual pacman install/removal blocked by decman guard.\n"
    "\n"
    "Please add/remove the package via your decman source (for example: example/my_source.py) and run:\n"
    "  sudo decman\n"
    "\n"
    "To bypass once (not recommended):\n"
    "  sudo DECMAN_ALLOW=1 pacman -S <package>\n"
    "  sudo DECMAN_ALLOW=1 pacman -R <package>\n"
    "EOF\n"
    "exit 1\n"
  ),
  encoding="utf-8",
  permissions=0o755,
)

# --- systemd units ---
# Decman will enable these units if not already enabled. It does NOT start them automatically.
# Start them once manually or reboot.
decman.enabled_systemd_units += [
    "NetworkManager.service",
]

# --- Modules ---
# You can keep things simple at first and add modules later.
# decman.modules += [MyModule()]
