#!/bin/bash
BASE_PATH=$(dirname "${BASH_SOURCE}")
BASE_PATH=$(cd "${BASE_PATH}"; pwd)
export PYTHONPATH=$BASE_PATH/..:$PYTHONPATH

# install ops and dev templates
$BASE_PATH/install_es_template.py
PROVES_ENV=dev $BASE_PATH/install_es_template.py
