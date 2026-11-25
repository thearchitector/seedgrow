#!/usr/bin/env bash
# Provision only on an ephemeral *GitHub-hosted* Ubuntu VM, before loading the private fixture.
# Never run this on a local, shared or self-hosted machine. No change to CPU or VM memory policy.
set -euo pipefail
[[ ${GITHUB_ACTIONS:-} == true && ${RUNNER_ENVIRONMENT:-} == github-hosted && ${RUNNER_OS:-} == Linux && $(id -un) == runner ]]
[[ ${GITHUB_REPOSITORY:-} == thearchitector/seedgrow && ${GITHUB_REF:-} == refs/heads/ci/runner-isa-smoke && -z ${ACT:-} ]]
[[ $(realpath -e "$RUNNER_TEMP") == /home/runner/work/_temp ]]
[[ $(. /etc/os-release; printf %s "$VERSION_ID") == 24.04 ]]
umask 077
free_b() { df -B1 --output=avail -- "$1" | tail -1 | tr -d ' '; }
# Keep a margin over the actual >32 GiB check, applied again to the work filesystem by each native launch.
min=$((34*1024*1024*1024)); base=$RUNNER_TEMP
if (( $(free_b "$base") < min )); then
  # Some runner images mount a large ephemeral data disk. Prefer creating a new private directory there.
  if mountpoint -q /mnt && [[ ,$(findmnt -no OPTIONS -T /mnt), != *,noexec,* ]] && (( $(free_b /mnt) >= min )); then
    if [[ -w /mnt ]]; then base=$(mktemp -d /mnt/seedgrow.XXXXXXXX)
    else base=$(sudo -n /usr/bin/mktemp -d /mnt/seedgrow.XXXXXXXX); [[ $base == /mnt/seedgrow.* ]]; sudo -n /usr/bin/chown "$(id -u):$(id -g)" -- "$base"; fi
  fi
fi
if (( $(free_b "$base") < min )); then
  # Only unused, image-supplied SDKs on THIS disposable test filesystem. No user files, cache restores or checkout.
  for sdk in /usr/local/lib/android/sdk /usr/share/dotnet /opt/ghc; do
    [[ -d "$sdk" && $(realpath -e "$sdk") == "$sdk" ]] || continue
    [[ $(stat -c %d "$sdk") == "$(stat -c %d "$base")" ]] || continue
    if findmnt --raw --noheadings --output TARGET | awk -v p="$sdk" '$0==p || index($0,p"/")==1 {found=1} END {exit !found}'; then continue; fi
    echo "Reclaiming unused disposable-image SDK $sdk for bounded sparse scratch"
    sudo -n /usr/bin/rm -rf --one-file-system -- "$sdk"
    if (( $(free_b "$base") >= min )); then break; fi
  done
fi
# If capacity is still insufficient, the guarded worker records a terminal refusal. Do not shop for a higher score.
printf 'SG_GUEST_SCRATCH=%s\n' "$base" >> "$GITHUB_ENV"
printf 'Scratch volume free bytes: %s\n' "$(free_b "$base")"
