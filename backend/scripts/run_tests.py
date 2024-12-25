#!/usr/bin/env python3
import subprocess
import sys
import os
import time
from pathlib import Path
import json
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directory di progetto
PROJECT_DIR = Path(__file__).parent.parent
TESTS_DIR = PROJECT_DIR / "tests"
REPORTS_DIR = PROJECT_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

def run_tests(coverage=True, benchmark=True):
    """
    Esegue la suite completa di test con coverage e benchmark.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Prepara comando pytest
    cmd = [
        "pytest",
        str(TESTS_DIR),
        "-v",
        "--log-cli-level=INFO"
    ]
    
    if coverage:
        cmd.extend([
            "--cov=app",
            "--cov-report=term-missing",
            f"--cov-report=html:{REPORTS_DIR}/coverage_{timestamp}"
        ])
    
    if benchmark:
        cmd.extend([
            "--benchmark-only",
            "--benchmark-json", f"{REPORTS_DIR}/benchmark_{timestamp}.json"
        ])
    
    # Esegui test
    start_time = time.time()
    logger.info("Avvio esecuzione test...")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True
        )
        
        execution_time = time.time() - start_time
        
        # Salva output
        output_file = REPORTS_DIR / f"test_output_{timestamp}.txt"
        with output_file.open("w") as f:
            f.write(result.stdout)
            if result.stderr:
                f.write("\n\nERRORS:\n")
                f.write(result.stderr)
        
        # Genera report
        report = {
            "timestamp": timestamp,
            "execution_time": execution_time,
            "exit_code": result.returncode,
            "coverage_report": f"coverage_{timestamp}" if coverage else None,
            "benchmark_report": f"benchmark_{timestamp}.json" if benchmark else None,
            "output_file": str(output_file)
        }
        
        report_file = REPORTS_DIR / f"test_report_{timestamp}.json"
        with report_file.open("w") as f:
            json.dump(report, f, indent=2)
        
        # Log risultati
        logger.info(f"Test completati in {execution_time:.2f} secondi")
        logger.info(f"Exit code: {result.returncode}")
        logger.info(f"Report salvato in: {report_file}")
        
        if coverage:
            logger.info(f"Coverage report: {REPORTS_DIR}/coverage_{timestamp}")
        
        if benchmark:
            logger.info(f"Benchmark report: {REPORTS_DIR}/benchmark_{timestamp}.json")
        
        return result.returncode == 0
        
    except Exception as e:
        logger.error(f"Errore nell'esecuzione dei test: {str(e)}")
        return False

def analyze_benchmark(benchmark_file):
    """
    Analizza i risultati del benchmark.
    """
    try:
        with open(benchmark_file) as f:
            data = json.load(f)
        
        benchmarks = data["benchmarks"]
        
        # Analisi per test
        test_stats = {}
        for bench in benchmarks:
            name = bench["name"]
            stats = bench["stats"]
            test_stats[name] = {
                "mean": stats["mean"],
                "min": stats["min"],
                "max": stats["max"],
                "stddev": stats["stddev"]
            }
        
        # Salva analisi
        analysis_file = benchmark_file.replace(".json", "_analysis.json")
        with open(analysis_file, "w") as f:
            json.dump(test_stats, f, indent=2)
            
        logger.info(f"Analisi benchmark salvata in: {analysis_file}")
        
    except Exception as e:
        logger.error(f"Errore nell'analisi del benchmark: {str(e)}")

def main():
    """
    Entry point principale.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Esegue la suite di test automatizzati")
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Disabilita report coverage"
    )
    parser.add_argument(
        "--no-benchmark",
        action="store_true",
        help="Disabilita benchmark"
    )
    parser.add_argument(
        "--analyze-benchmark",
        help="Analizza un file di benchmark esistente"
    )
    
    args = parser.parse_args()
    
    if args.analyze_benchmark:
        analyze_benchmark(args.analyze_benchmark)
        return
    
    success = run_tests(
        coverage=not args.no_coverage,
        benchmark=not args.no_benchmark
    )
    
    # Analizza ultimo benchmark se presente
    if not args.no_benchmark:
        benchmark_files = sorted(
            REPORTS_DIR.glob("benchmark_*.json"),
            key=os.path.getmtime
        )
        if benchmark_files:
            analyze_benchmark(benchmark_files[-1])
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 