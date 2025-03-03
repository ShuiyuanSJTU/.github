#!/bin/bash

ROOT_DIR=$(dirname "$(dirname "$(realpath "$0")")")
WORKING_DIR=$ROOT_DIR/tmp
UPSTREAM_DIR=$WORKING_DIR/upstream

mkdir -p $WORKING_DIR

git clone https://github.com/discourse/.github.git $UPSTREAM_DIR

pip install -r $ROOT_DIR/scripts/requirements.txt

python $ROOT_DIR/scripts/generate_discourse_plugin_yml.py $UPSTREAM_DIR/.github/workflows/discourse-plugin.yml $ROOT_DIR/.github/workflows/discourse-plugin.yml

python $ROOT_DIR/scripts/generate_plugin_compacity_yml.py $UPSTREAM_DIR/.github/workflows/discourse-plugin.yml $ROOT_DIR/.github/workflows/plugin-compacity.yml

UPSTREAM_SHA=$(git -C $UPSTREAM_DIR rev-parse HEAD)
GENERATOR_SHA=$(git -C $ROOT_DIR log -1 --pretty=format:"%H" -- scripts/generate_*_yml.py scripts/generate.sh)
MESSAGE="# Generated from https://github.com/discourse/.github/blob/$UPSTREAM_SHA/.github/workflows/discourse-plugin.yml\n# Generator version: $GENERATOR_SHA\n\n"
printf "%s\n\n%s" "$(echo -e $MESSAGE)" "$(cat $ROOT_DIR/.github/workflows/discourse-plugin.yml)" > $ROOT_DIR/.github/workflows/discourse-plugin.yml
printf "%s\n\n%s" "$(echo -e $MESSAGE)" "$(cat $ROOT_DIR/.github/workflows/plugin-compacity.yml)" > $ROOT_DIR/.github/workflows/plugin-compacity.yml

rm -rf $WORKING_DIR