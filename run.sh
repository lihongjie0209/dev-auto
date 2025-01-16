#!/usr/bin/env bash

set -e -u -o pipefail

# run python script use venv interpreter


# get current script dir path
SCRIPT_DIR=$(cd $(dirname $0); pwd)

echo $SCRIPT_DIR

# get python path

PYTHON_PATH=$SCRIPT_DIR/.venv/Scripts/python.exe

# run python script, pass $2 $3 $4 ... to script

$PYTHON_PATH $SCRIPT_DIR/$1  ${@:2}


