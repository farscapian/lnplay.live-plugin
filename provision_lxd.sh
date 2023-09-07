#!/bin/bash

set -exu

if ! lxc remote list | grep -q lnplaylive; then
    lxc remote add lnplaylive "$LNPLAY_LXD_FQDN_PORT" --password "$LNPLAY_LXD_PASSWORD" --accept-certificate >> /dev/null
# else
#     echo "INFO: remote 'lnplaylive' already exists."
fi

if ! lxc remote get-default | grep -q lnplaylive; then
    lxc remote switch lnplaylive  >> /dev/null
# else
#     echo "INFO: lxc remote already on remote lnplaylive"
fi

if ! lxc project list | grep -q lnplaylivemvp; then
    lxc project create lnplaylivemvp
fi

if ! lxc project list | grep -q "default (current)"; then
    lxc project switch lnplaylivemvp
fi

cd /sovereign-stack
bash -c "$(pwd)/deployment/up.sh"

