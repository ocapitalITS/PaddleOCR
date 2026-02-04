#!/usr/bin/env python3
"""Test fastapi_app split_malay_words directly"""
import sys
sys.path.insert(0, 'c:\\laragon\\www\\PaddleOCR')

from fastapi_app import split_malay_words

# Test cases
test_cases = [
    "NIKAMINBIN MATZIN",
    "NIKAMIN BIN MATZIN",
    "ALORSETAR",
]

print("Testing split_malay_words from fastapi_app:")
for test in test_cases:
    result = split_malay_words(test)
    print(f"  '{test}' → '{result}'")
