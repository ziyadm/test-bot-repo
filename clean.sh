#!/bin/bash

black .
isort .
flake8 . --max-line-length=88
