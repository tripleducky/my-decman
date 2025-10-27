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

import os
import shutil

import decman
from decman import File  # Add Directory, Module later if needed
import decman.config as conf
import decman.lib as l

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
    "ly",
]

decman.aur_packages += ["decman", "protonvpn"]

# Packages you want decman to ignore (won't install or remove).
# Useful for tools you prefer to manage manually.
decman.ignored_packages += [
     "yay",
]

# --- Optional: Use yay for AUR packages ---
# If yay is available, offer to use it for AUR installs/upgrades instead of decman's
# chroot builder. This keeps decman's pacman/file/systemd features intact.
if shutil.which("yay") and decman.aur_packages:
  l.print_summary("AUR helper 'yay' detected.")
  if l.prompt_confirm(
    "Would you like to install AUR packages using yay instead of decman's builder?",
    default=True,
  ):
    # Disable decman's foreign package manager for this run
    conf.enable_fpm = False

    # Figure out a non-root user to run yay under (yay refuses root). Prefer SUDO_USER.
    sudo_user = os.environ.get("SUDO_USER")
    if not sudo_user:
      l.print_warning(
        "SUDO_USER not set; cannot run yay as a regular user. Falling back to decman's builder."
      )
      conf.enable_fpm = True
    else:
      class YayAurInstaller(decman.Module):
        """Runs yay to ensure declared AUR packages are installed/upgraded.

        Executed at the end (after_update), so normal pacman steps and file changes
        complete first. Uses --needed to avoid reinstalling already up-to-date packages.
        """

        def __init__(self, user: str):
          super().__init__(name="yay-aur", enabled=True, version="1")
          self._user = user

        def after_update(self):
          pkgs = list(decman.aur_packages)
          if not pkgs:
            return
          l.print_summary(
            "Installing/upgrading AUR packages with yay (skips up-to-date):"
          )
          l.print_list("AUR packages:", pkgs)
          # Run yay as the invoking sudo user to avoid root. Interactive by default.
          # Users can control yay behavior via their config; we keep it safe and promptful.
          decman.prg(["yay", "-S", "--needed"] + pkgs, user=self._user)

      # Register the module so it runs in this decman invocation
      decman.modules.append(YayAurInstaller(sudo_user))

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
    "ly.service",
]

# --- Modules ---
# You can keep things simple at first and add modules later.
# decman.modules += [MyModule()]
