#!/usr/bin/env bash
set -euo pipefail

foundrygate_repo_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd
}

foundrygate_platform() {
  uname -s
}

foundrygate_mac_label() {
  printf '%s\n' "com.typelicious.foundrygate"
}

foundrygate_mac_gui_domain() {
  printf 'gui/%s\n' "$(id -u)"
}

foundrygate_mac_agent_dir() {
  printf '%s\n' "${FOUNDRYGATE_MAC_AGENT_DIR:-$HOME/Library/LaunchAgents}"
}

foundrygate_mac_plist_path() {
  printf '%s/%s.plist\n' "$(foundrygate_mac_agent_dir)" "$(foundrygate_mac_label)"
}

foundrygate_mac_config_dir() {
  printf '%s\n' "${FOUNDRYGATE_MAC_CONFIG_DIR:-$HOME/Library/Application Support/FoundryGate}"
}

foundrygate_mac_logs_dir() {
  printf '%s\n' "${FOUNDRYGATE_MAC_LOGS_DIR:-$HOME/Library/Logs/FoundryGate}"
}

foundrygate_mac_db_path() {
  printf '%s/foundrygate.db\n' "$(foundrygate_mac_config_dir)"
}

foundrygate_mac_python() {
  printf '%s/.venv/bin/python\n' "$(foundrygate_repo_root)"
}

foundrygate_mac_config_path() {
  printf '%s/config.yaml\n' "$(foundrygate_mac_config_dir)"
}

foundrygate_bin_dir() {
  case "$(foundrygate_platform)" in
    Darwin)
      printf '%s\n' "${FOUNDRYGATE_BIN_DIR:-$HOME/.local/bin}"
      ;;
    *)
      printf '%s\n' "${FOUNDRYGATE_BIN_DIR:-/usr/local/bin}"
      ;;
  esac
}

foundrygate_install_helper_links() {
  local repo_root target_bin helper
  repo_root="$(foundrygate_repo_root)"
  target_bin="$(foundrygate_bin_dir)"
  mkdir -p "$target_bin"
  for helper in "$@"; do
    ln -sf "$repo_root/scripts/$helper" "$target_bin/$helper"
  done
  printf 'helper links installed in: %s\n' "$target_bin"
}

foundrygate_remove_helper_links() {
  local target_bin helper
  target_bin="$(foundrygate_bin_dir)"
  for helper in "$@"; do
    rm -f "$target_bin/$helper"
  done
  printf 'removed helper links from: %s\n' "$target_bin"
}

foundrygate_render_mac_plist() {
  local repo_root template target config_dir logs_dir
  repo_root="$(foundrygate_repo_root)"
  template="$repo_root/docs/examples/com.typelicious.foundrygate.plist"
  target="$(foundrygate_mac_plist_path)"
  config_dir="$(foundrygate_mac_config_dir)"
  logs_dir="$(foundrygate_mac_logs_dir)"
  mkdir -p "$(foundrygate_mac_agent_dir)" "$config_dir" "$logs_dir"
  sed "s|/Users/REPLACE_ME|$HOME|g" "$template" >"$target"
  printf 'launchd plist written to: %s\n' "$target"
}

foundrygate_launchctl_bootout() {
  local domain label plist
  domain="$(foundrygate_mac_gui_domain)"
  label="$(foundrygate_mac_label)"
  plist="$(foundrygate_mac_plist_path)"
  launchctl bootout "$domain/$label" >/dev/null 2>&1 || launchctl bootout "$domain" "$plist" >/dev/null 2>&1 || true
}

foundrygate_launchctl_start() {
  local domain label plist
  domain="$(foundrygate_mac_gui_domain)"
  label="$(foundrygate_mac_label)"
  plist="$(foundrygate_mac_plist_path)"
  foundrygate_launchctl_bootout
  launchctl bootstrap "$domain" "$plist"
  launchctl kickstart -k "$domain/$label"
}

foundrygate_launchctl_stop() {
  foundrygate_launchctl_bootout
}

foundrygate_launchctl_status() {
  local domain label
  domain="$(foundrygate_mac_gui_domain)"
  label="$(foundrygate_mac_label)"
  launchctl print "$domain/$label"
}
