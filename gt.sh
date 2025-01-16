#!/usr/bin/env bash

set -e -u -o pipefail

# 获取脚本所在目录
SCRIPT_DIR=$(cd $(dirname $0); pwd)

# pass rest arguments to run.sh

$SCRIPT_DIR/run.sh git-tool.py  $@