#!/usr/bin/env bash

set -euo pipefail

if [[ ${EUID} -eq 0 ]]; then
	echo "Run this script as your regular user, not root." >&2
	exit 1
fi

if ! command -v sudo >/dev/null 2>&1 || ! command -v snap >/dev/null 2>&1; then
	echo "This script requires sudo and snap on Ubuntu." >&2
	exit 1
fi

install_snap() {
	local name=$1
	shift

	if snap list "$name" >/dev/null 2>&1; then
		echo "$name is already installed."
	else
		sudo snap install "$name" "$@"
	fi
}

install_snap astral-uv --classic
install_snap docker
install_snap gh --classic

if getent group docker >/dev/null 2>&1; then
	echo "The docker group already exists."
else
	sudo groupadd docker
fi

if id -nG "$USER" | tr ' ' '\n' | grep -qx docker; then
	echo "$USER is already in the docker group."
else
	sudo usermod -aG docker "$USER"
	echo "Added $USER to the docker group."
fi

if ! command -v curl >/dev/null 2>&1; then
	echo "curl is required to install the Render CLI." >&2
	exit 1
fi

if command -v render >/dev/null 2>&1; then
	echo "The Render CLI is already installed."
else
	curl --fail --silent --show-error --location \
		https://raw.githubusercontent.com/render-oss/cli/refs/heads/main/bin/install.sh | sh
fi

echo "Setup complete. Log out and back in before using Docker without sudo."
