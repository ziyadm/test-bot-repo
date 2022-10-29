#!/bin/bash

python3 -m poetry lock --no-update
python3 -m poetry install
python3 -m poetry run python3 main.py
