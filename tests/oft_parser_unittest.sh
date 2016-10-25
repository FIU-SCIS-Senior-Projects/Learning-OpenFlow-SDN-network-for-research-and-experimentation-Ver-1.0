#!/bin/bash

SAMPLE_OUTPUT_DIR="dat/"
JSON_PATH="sample_log.json"

echo "Running Unit Test for OFTParser"
python $(SAMPLE_OUTPUT_DIR) $(JSON_PATH)
