#!/usr/bin/bash

qbraid_config="$HOME/.qbraid/config"
qbraid_rc="$HOME/.qbraid/qbraidrc"

# filepath=$(grep ibmq_session "${qbraid_config}" | cut -b 16- )
site_pkgs=$(pip show qiskit | grep -i "Location" | cut -b 11-)
file="qiskit/providers/ibmq/api/session.py"
filepath=$site_pkgs/$file

if [[ ! -f "$qbraid_config" ]]; then
    >&2 echo "File \"$qbraid_config\" not found"
    exit 1
fi

if [[ ! -f "$qbraid_rc" ]]; then
    >&2 echo "File \"$qbraid_rc\" not found"
    exit 1
fi

user_email=$(grep user "${qbraid_rc}" | cut -b 8- )
refresh_token=$(grep token "${qbraid_rc}" | cut -b 9- )

if [[ ! -f "$filepath" ]]; then
    >&2 echo "File \"$filepath\" not found"
    exit 1
fi

mark="headers.update(kwargs.pop('headers', {}))"
mark_line_n=$(grep -n "${mark}" "${filepath}" | cut -d : -f 1)
mark_line_n_expected=273
if [ "$mark_line_n" != "$mark_line_n_expected" ]; then
    >&2 echo "Mark \"$mark\" not found on line $mark_line_n_expected"
    exit 1
fi

wspace=$(grep "${mark}" "${filepath}")
wospace=$(echo "${wspace}" | sed -e 's/[[:space:]]*//')
wc0=$(echo "${wspace}" | awk '{ print length }')
wc1=$(echo "${wospace}" | awk '{ print length }')
nspace=$(( $wc0 - $wc1 ))

code="headers.update({\'email\':\'"${user_email}"\',\'refresh-token\':\'"${refresh_token}"\'})"
spaces=$(for i in $(seq 1 $nspace); do printf " "; done)
add=$spaces$code

add_line_n=$(grep -n "${add}" "${filepath}" | cut -d : -f 1)
add_line_n_target=$(( $mark_line_n_expected + 1 ))
if [ "$add_line_n" == "$add_line_n_target" ]; then
    exit 0
fi

sed -i '' ''"${mark_line_n}"' a\
'"${add}"'\
' "${filepath}"