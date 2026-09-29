import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "compressed_output.json"
SAMPLE_PATH = PROJECT_ROOT / "sample.txt"


@pytest.fixture(scope="session", autouse=True)
def ensure_compressed_corpus():
    """Generate the real compressed corpus when a clean checkout lacks it."""
    if OUTPUT_PATH.exists():
        yield
        return

    if not SAMPLE_PATH.exists():
        pytest.fail(f"Required pipeline input is missing: {SAMPLE_PATH}")

    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    from main import ContextualCompressionEngine

    engine = ContextualCompressionEngine(
        importance_threshold=0.5,
        use_combined_score=True,
        min_confidence=0.4,
        auto_tune_threshold=False,
    )
    engine.process_document(
        file_path=str(SAMPLE_PATH),
        output_path=str(OUTPUT_PATH),
    )

    if not OUTPUT_PATH.exists():
        pytest.fail("The compression pipeline did not create compressed_output.json")

    try:
        yield
    finally:
        OUTPUT_PATH.unlink(missing_ok=True)
        try:
            sys.path.remove(str(PROJECT_ROOT / "src"))
        except ValueError:
            pass


__all__ = ["ensure_compressed_corpus"]
