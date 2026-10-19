#!/bin/sh
# Reproduce the tested local category override, preserving packaged translations.
set -eu
src=/usr/share/applications/blueman-manager.desktop
dst=/usr/local/share/applications/blueman-manager.desktop
test -f "$src"
mkdir -p /usr/local/share/applications
sed 's|^Categories=.*|Categories=XFCE;GTK;Settings;HardwareSettings;X-XFCE-SettingsDialog;X-XFCE-HardwareSettings;Network;|' "$src" > "$dst"
chmod 644 "$dst"
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/local/share/applications
fi
