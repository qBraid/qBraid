#!/bin/bash

site_pkgs=$(pip show qiskit | grep -i "Location" | cut -b 11-)
file="qiskit/providers/ibmq/api/session.py"
file_path=$site_pkgs/$file
if [[ ! -f "$file_path" ]]; then
    >&2 echo "File \"$file_path\" not found"
    exit 1
fi

mark="headers.update(kwargs.pop('headers', {}))"
line=$(grep -n "${mark}" "${file_path}" | cut -d : -f 1)
line_expected=273
if [ "$line" != "$line_expected" ]; then
    >&2 echo "Mark \"$mark\" not found on line $line_expected"
    exit 1
fi

wspace=$(grep "${mark}" "${file_path}")
wospace=$(echo "${wspace}" | sed -e 's/[[:space:]]*//')
wc0=$(echo "${wspace}" | awk '{ print length }')
wc1=$(echo "${wospace}" | awk '{ print length }')
nspace=$(expr $wc0 - $wc1)

code="headers.update({\'email\':os.getenv(\'JUPYTERHUB_USER\'),\'refresh-token\':os.getenv(\'REFRESH\')})"
spaces=$(for i in $(seq 1 $nspace); do printf " "; done)
add_line=$spaces$code

sed -i '' ''"${line}"' a\
'"${add_line}"'\
' $file_path

# sed -i '' '/'"${MARK}"'/ a\
# '"${ADDLINE}"'\
# ' $FILE

# sed -i '' ''"${LINEM1}"'i\
# '"${ADDLINE}"'' $FILE
