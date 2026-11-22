#!/usr/bin/env python3
"""Performance Profiler for Code Analysis (QANOON-Compliant).

Measure function call counts, hotspots.
No external dependencies.
"""

import cProfile
import json
import pstats
import io
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

class PerformanceProfiler:
    """Profile Python code execution."""
    
    def profile_function(self, func, *args, **kwargs) -> Dict[str, Any]:
        """Profile a single function call."""
        profiler = cProfile.Profile()
        profiler.enable()
        
        result = func(*args, **kwargs)
        
        profiler.disable()
        
        # Extract stats
        stream = io.StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.sort_stats("cumulative")
        stats.print_stats(20)  # Top 20
        
        return {
            "function": func.__name__,
            "result": result,
            "profile_data": stream.getvalue(),
            "total_time": sum(item[2] for item in profiler.stats.values()) / 1e6,  # seconds
            "calls": sum(item[1] for item in profiler.stats.values()),
            "qanoon_compliance": {
                "local_only": True,
                "no_external_ai": True
            }
        }
    
    def profile_file(self, file_path: Path) -> Dict[str, Any]:
        """Profile a Python file."""
        profiler = cProfile.Profile()
        profiler.enable()
        
        try:
            # Execute the file in a controlled namespace
            namespace = {"__name__": "__profiled__"}
            with open(file_path, "r", encoding="utf-8") as f:
                code = compile(f.read(), str(file_path), "exec")
            exec(code, namespace)
        except Exception as e:
            profiler.disable()
            return {
                "file": str(file_path),
                "error": str(e),
                "qanoon_compliance": {
                    "local_only": True
                }
            }
        
        profiler.disable()
        
        # Extract stats
        stream = io.StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.sort_stats("cumulative")
        stats.print_stats(30)  # Top 30
        
        return {
            "file": str(file_path),
            "total_time": sum(item[2] for item in profiler.stats.values()) / 1e6,  # seconds
            "calls": sum(item[1] for item in profiler.stats.values()),
            "profile_data": stream.getvalue(),
            "top_functions": self._extract_top_functions(stats),
            "qanoon_compliance": {
                "local_only": True
            }
        }
    
    def _extract_top_functions(self, stats: pstats.Stats) -> List[Dict[str, Any]]:
        """Extract top function call counts."""
        top_functions = []
        for func in sorted(stats.stats.items(), key=lambda x: x[1].total_calls, reverse=True)[:10]:
            top_functions.append({
                "function": func[0][2],
                "calls": func[1].total_calls,
                "total_time": func[1].total_tt
            })
        return top_functions

def main():
    """Run profiler on DigitalBrain files."""
    profiler = PerformanceProfiler()
    
    # Profile ULTIMATE_CODING_MASTER.py
    print("📊 Profiling ULTIMATE_CODING_MASTER.py...")
    result = profiler.profile_file(Path(r"D:\DigitalBrain\ULTIMATE_CODING_MASTER.py"))
    
    print(f"   - Total time: {result.get('total_time', 0):.3f}s")
    print(f"   - Calls: {result.get('calls', 0)}")
    print(f"   - Top functions:")
    for func in result.get("top_functions", [])[:5]:
        print(f"      * {func['function']}: {func['calls']} calls, {func['total_time']:.3f}s")

if __name__ == "__main__":
    main()
