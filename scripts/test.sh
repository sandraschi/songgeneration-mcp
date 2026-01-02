#!/bin/bash
# Test runner script

echo "Running tests..."
pytest

echo "Running linter..."
ruff check .

echo "✅ All checks passed!"
