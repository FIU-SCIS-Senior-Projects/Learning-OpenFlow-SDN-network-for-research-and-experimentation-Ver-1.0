#!/bin/bash

PYTHON_SCRIPT_NAME="oft_parser.py"
SAMPLE_OUTPUT_DIR="dat/"
JSON_PATH="sample_log.json"

echo "Running Unit Test for OFTParser"
python $PYTHON_SCRIPT_NAME $SAMPLE_OUTPUT_DIR $JSON_PATH
echo "Done! Check output in $JSON_PATH"
