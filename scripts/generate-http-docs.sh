#!/bin/bash -eu

# This script generates an HTML page containing all of the client-server API docs.
# It takes all of the swagger YAML files for the client-server API, and turns
# them into API docs, with none of the narrative found in the rst files which
# normally wrap these API docs.
#
# Optionally takes one positional argument, the label of the release, e.g. r1.2.
# This falls back to "unstable" if unspecified.

if [[ $# == 1 ]]; then
  client_release=$1
else
  client_release="unstable"
fi

client_major_version="$(echo "${client_release}" | perl -pe 's/^(r\d+)\..*$/$1/g')"

cd "$(dirname $0)"

mkdir -p tmp gen

cat >tmp/http_apis <<EOF
Matrix Client-Server API Reference
==================================

This contains the client-server API for the reference implementation of the home server.


EOF

for f in ../api/client-server/*.yaml; do
  f="$(basename "${f/.yaml/_http_api}")"
  echo "{{${f/-/_}}}" >> tmp/http_apis
done

cat >>tmp/http_apis <<EOF

.. |initialSync| replace:: ``/initialSync``_
.. _initialSync: https://matrix.org/docs/spec/client_server.html#get-matrix-client-%CLIENT_MAJOR_VERSION%-initialsync


.. _\`user-interactive authentication\`: https://matrix.org/docs/spec/client_server.html#user-interactive-authentication-api

.. _pushers: https://matrix.org/docs/spec/client_server.html#def-pushers

.. _\`room events\`: https://matrix.org/docs/spec/client_server.html#room-events


EOF

(cd ../templating ; python build.py -i matrix_templates -o ../scripts/gen ../scripts/tmp/http_apis --substitution=%CLIENT_RELEASE_LABEL%="${client_release}" --substitution=%CLIENT_MAJOR_VERSION%="${client_major_version}")
rst2html.py --stylesheet-path=$(echo css/*.css | tr ' ' ',') gen/http_apis > gen/http_apis.html
