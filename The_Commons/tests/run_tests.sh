#!/bin/bash

# The Commons - Test Runner
# Runs integration tests with summary output

cd /home/aipass/The_Commons

echo "========================================"
echo "The Commons - Integration Test Suite"
echo "========================================"
echo ""

# Run tests
python3 tests/test_commons.py -v

# Capture exit code
EXIT_CODE=$?

echo ""
echo "========================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ All tests passed!"
else
    echo "✗ Some tests failed (exit code: $EXIT_CODE)"
fi
echo "========================================"

exit $EXIT_CODE
