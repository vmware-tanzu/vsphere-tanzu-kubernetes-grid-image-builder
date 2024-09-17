#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail
set -x

add_panic_mount_option() {
    # Adding disk mount option errors=panic to root disk mount options
    # so that if there was a disk failure, a panic will be triggered,
    # and we also set kernel.panic to 10 which will cause the VM to restart
    # automatically after disk failure after 10 seconds.
    # More specifically, this function makes changes to /etc/fstab where
    # PARTUUID=47c08993-cc75-4650-b36d-b2c3c5738d66	/	ext4	defaults,barrier,noatime,noacl,data=ordered	1	1
    # becomes
    # PARTUUID=47c08993-cc75-4650-b36d-b2c3c5738d66	/	ext4	defaults,barrier,noatime,noacl,data=ordered,errors=panic	1	1
    panic_option="errors=panic"
    # grep for "/{tab}ext4"
    current_options=$(cat /etc/fstab | grep -G "/[ $(printf '\t')]*ext4" | head -1 | awk -F' ' '{print $4}')
    # somehow there is no root disk mounted
    [[ "$current_options" == "" ]] && return
    # if panic_option already exists, return
    echo $current_options | grep $panic_option >/dev/null 2>&1 && [[ "$?" == "0" ]] && return
    new_options="$current_options,$panic_option"
    sed -i "s/$current_options/$new_options/g" /etc/fstab
}

add_panic_mount_option
