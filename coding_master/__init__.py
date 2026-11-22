"""ULTIMATE CODING MASTER engine - local, dependency-free code intelligence.

QANOON: Python standard library only. No network calls, no external AI
platforms, no FFmpeg, no cloud services. Everything runs on the local disk.

Public modules
--------------
util       shared filesystem/text helpers
indexer    AST + regex symbol index and dependency map
analyzer   metrics, complexity, smells and duplicate detection
security   secrets, unsafe-call and injection scanner
generator  real multi-language code generation
tests_gen  runnable unit-test generation from Python AST
docs       API documentation and README generation
refactor   import organisation, unused-import removal, safe rename
scaffold   complete project scaffolding for several stacks
cli        command line interface (``python -m coding_master``)
"""

__version__ = "2.0.0"
