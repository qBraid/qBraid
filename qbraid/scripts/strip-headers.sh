#!/bin/bash

qbraid_config="$HOME/.qbraid/config"
qbraid_rc="$HOME/.qbraid/qbraidrc"

# filepath=$(grep ibmq_session "${qbraid_config}" | cut -b 16- )
site_pkgs=$(pip show qiskit | grep -i "Location" | cut -b 11-)
file="qiskit/providers/ibmq/api/session.py"
filepath=$site_pkgs/$file
user_email=$(grep user "${qbraid_rc}" | cut -b 8- )
refresh_token=$(grep token "${qbraid_rc}" | cut -b 9- )

if [[ ! -f "$filepath" ]]; then
    >&2 echo "File \"$filepath\" not found"
    exit 1
fi

mark="headers.update({\'email\':\'"${user_email}"\',\'refresh-token\':\'"${refresh_token}"\'})"
mark_line_n=$(grep -n "${mark}" "${filepath}" | cut -d : -f 1)
mark_line_n_expected=274
if [ "$mark_line_n" != "$mark_line_n_expected" ]; then
    >&2 echo "Mark \"$mark\" not found on line $mark_line_n_expected"
    exit 0
fi

sed -i '' '274d' "$filepath"