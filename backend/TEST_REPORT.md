# Test Report - Gene Mutation Detection System

Last Updated: 2026-04-09
Test Framework: `pytest`
Environment: Windows / Python 3.12.9

## Executive Summary

The backend test suite was expanded with Phase 6 coverage across:
- unit tests for agents, models, and utilities
- integration tests for workflow, API, cache, and service behavior
- performance-oriented smoke tests
- error and graceful-degradation scenarios

Verified full-suite result:
- `137 passed`
- `1 skipped`
- `10 warnings`

The skipped test is the live NCBI search test, which remains intentionally skipped because it depends on external network/API availability.

## Phase 6 Additions

New Phase 6 files:
- `tests/test_agents_unit.py`
- `tests/test_models_unit.py`
- `tests/test_utils_unit.py`
- `tests/test_integration_complete.py`
- `tests/test_performance.py`
- `tests/test_error_scenarios.py`
- `run_all_tests.py`

Supporting robustness update:
- `utils/validators.py`

## Results By Category

### Unit Tests

- `tests/test_agents_unit.py` -> `24 passed`
- `tests/test_models_unit.py` -> `18 passed`
- `tests/test_utils_unit.py` -> `11 passed`

Focus areas covered:
- validation behavior
- alignment failure handling
- mutation detection
- annotation logic
- classification rules
- model validation and serialization
- validator helper safety on bad inputs

### Integration Tests

- `tests/test_integration_complete.py` -> `13 passed`

Focus areas covered:
- LangGraph workflow progression
- AnalysisService end-to-end execution
- cache integration
- Gemini status integration
- API health/reference/cache endpoints

### Performance Tests

- `tests/test_performance.py` -> `9 passed`

Focus areas covered:
- validation speed
- workflow speed
- service speed
- allocation-focused memory smoke tests with `tracemalloc`
- cache responsiveness
- concurrent requests
- moderately large sequence handling

### Error Scenario Tests

- `tests/test_error_scenarios.py` -> `17 passed`

Focus areas covered:
- invalid request payloads
- NCBI failure behavior
- Gemini non-blocking behavior
- long input handling
- concurrent request handling
- degraded modes without optional services
- recovery after earlier failures

## Full Suite Verification

Executed:

```bash
venv\Scripts\python.exe -m pytest tests -q
```

Observed output summary:

```text
137 passed, 1 skipped, 10 warnings in 10.04s
```

Additional smoke checks:

```bash
backend\venv\Scripts\python.exe - <<import backend.server>>
backend\venv\Scripts\python.exe - <<import services and graph>>
```

Validated:
- server imports successfully
- analysis service initializes
- Gemini service object initializes
- SQLite cache initializes
- LangGraph graph initializes

## Warnings Observed

Current warnings are non-blocking and already known:

1. Biopython deprecation warning for `Bio.pairwise2`
2. Pydantic v2 deprecation warnings for older config/field patterns
3. FastAPI `on_event` deprecation warnings
4. Windows `.pytest_cache` permission warning in this workspace
5. Gemini library unavailable warning when `google-generativeai` is not installed in the active environment

## Notes

- Coverage reporting was not generated in this execution, so no coverage percentage is claimed here.
- Gemini remains optional and non-blocking by design.
- ClinVar retrieval is still functional through local fallback when live NCBI is unavailable.

## Conclusion

Phase 6 testing is implemented and passing for the current codebase.

Status:
- comprehensive automated testing added
- full regression suite passing
- production-readiness improved

Remaining follow-up work is mostly cleanup:
- migrate off `pairwise2`
- modernize Pydantic config usage
- replace FastAPI startup/shutdown decorators with lifespan handlers
