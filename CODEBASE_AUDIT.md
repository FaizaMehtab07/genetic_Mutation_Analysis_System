# Current Codebase Audit

## PHASE 1: FOUNDATION - COMPLETED ✅

### ✅ Directory Structure
- ✅ `core/` - LangGraph components (state, graph, config, constants)
- ✅ `services/` - Business logic layer (analysis service)
- ✅ `models/` - Pydantic models and ML models
- ✅ `utils/` - Helper functions (logging, validators)
- ✅ `config/` - Configuration files (logging.yaml)
- ✅ `tests/` - Test suite with pytest fixtures
- ✅ `notebooks/` - Jupyter notebooks for analysis
- ✅ `logs/` - Application logging (with .gitkeep)
- ✅ `data/clinvar_indexed/` - Vector store (with .gitkeep)

### ✅ Core Module Files
- ✅ `core/__init__.py` - Module exports
- ✅ `core/state.py` - Shared LangGraph state definition
- ✅ `core/graph.py` - LangGraph workflow skeleton
- ✅ `core/config.py` - Pydantic settings from environment
- ✅ `core/constants.py` - Application constants and gene info

### ✅ Service Layer
- ✅ `services/__init__.py` - Service module
- ✅ `services/analysis_service.py` - Main analysis orchestrator skeleton

### ✅ Models Layer
- ✅ `models/__init__.py` - Models module
- ✅ `models/pydantic_models.py` - Request/response validation skeletons

### ✅ Utils Layer
- ✅ `utils/__init__.py` - Utils module
- ✅ `utils/logger.py` - Structured logging setup
- ✅ `utils/validators.py` - Custom validation functions

### ✅ Configuration
- ✅ `config/__init__.py` - Config module
- ✅ `config/logging.yaml` - Advanced logging configuration

### ✅ Testing Infrastructure
- ✅ `tests/__init__.py` - Tests module
- ✅ `tests/conftest.py` - Pytest fixtures and configuration

### ✅ Environment Configuration
- ✅ `.env` - Production environment variables
- ✅ `.env.example` - Template for team members
- ✅ `.gitignore` - Comprehensive exclusions (env files, logs, sensitive data)

### ✅ Dependencies
- ✅ `requirements.txt` - Updated with LangGraph, LlamaIndex, FAISS
- ✅ `requirements.txt.backup` - Backup of original requirements

### ✅ Documentation
- ✅ `CODEBASE_AUDIT.md` - Complete audit and migration roadmap

## Agents Summary

### 1. ValidationAgent
- File: backend/agents/validation_agent.py
- Main Method: validate(sequence: str)
- Input: DNA sequence string
- Output: {is_valid, cleaned_sequence, errors, warnings}
- Status: READY FOR REFACTOR

### 2. AlignmentAgent
- File: backend/agents/alignment_agent.py
- Main Method: align(query_sequence: str)
- Input: Cleaned DNA sequence
- Output: {success, aligned_reference, aligned_query, identity_percent, score, matches, mismatches, gaps, alignment_visual}
- Dependency: Biopython
- Status: READY FOR REFACTOR

### 3. MutationDetectionAgent
- File: backend/agents/mutation_detection_agent.py
- Main Method: detect(aligned_reference, aligned_query)
- Input: Aligned sequences
- Output: {total_mutations, mutations[], mutation_counts, has_mutations}
- Status: READY FOR REFACTOR

### 4. AnnotationAgent
- File: backend/agents/annotation_agent.py
- Main Method: annotate(mutations, reference_sequence, query_sequence)
- Input: Mutations list + sequences
- Output: {annotated_mutations, impact_summary}
- Status: READY FOR REFACTOR

### 5. ClassificationAgent
- File: backend/agents/classification_agent.py
- Main Method: classify(annotated_mutations)
- Input: Annotated mutations
- Output: {overall_classification, risk_level, confidence, rationale, classified_mutations, summary, recommendation}
- Status: READY FOR REFACTOR + ML INTEGRATION

### 6. RetrievalAgent
- File: backend/agents/retrieval_agent.py
- Main Method: retrieve(mutations, gene)
- Input: Mutations + gene name
- Output: {success, total_evidence, evidence[], database, gene}
- Data Source: CSV (clinvar_database.csv)
- Status: NEEDS MIGRATION TO LLAMAINDEX

## Current Data Flow

User Input ↓ Validation ↓ Alignment (Biopython) ↓ Mutation Detection ↓ Annotation (Genetic Code) ↓ Classification (Rule-based + ML) ↓ Retrieval (CSV filtering) ↓ Output

## Issues Found

1. **No state management** - Sequential pipeline only
2. **No error recovery** - Fails entire pipeline on single error
3. **Hard-coded file paths** - Not configurable
4. **No type hints** - Difficult to understand contracts
5. **CSV-based retrieval** - Inefficient for large datasets
6. **No validation framework** - Manual checking

## Dependencies Currently Used

Core:

fastapi==0.110.1
biopython==1.83
Data Processing:

pandas==2.0.3
numpy==1.24.3
ML:

scikit-learn==1.3.0
joblib==1.3.1
Config:

python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0

## Dependencies Added (LangGraph Migration)

LangGraph & Orchestration:

langgraph==0.0.39
langchain==0.1.0
langchain-community==0.0.10
LlamaIndex & RAG:

llama-index==0.9.40
llama-index-embeddings-openai==0.1.5
llama-index-vector-stores-faiss==0.1.0
Vector Databases:

faiss-cpu==1.7.4
Utilities:

python-json-logger==2.0.7
colorama==0.4.6

## Files That Need Updates

**Phase 1 (Foundation) - COMPLETED:**
- ✅ backend/requirements.txt [UPDATED with LangGraph/LlamaIndex deps]
- ✅ New directory structure created
- ✅ Core module skeletons created
- ✅ Service layer skeletons created
- ✅ Model definitions started
- ✅ Utility functions created
- ✅ Environment configuration (.env, .env.example)
- ✅ .gitignore updated
- ✅ Logs and vector store directories created
- ✅ Import paths fixed for relative imports

**Phase 2 (Models & State):**
- ✅ backend/models/pydantic_models.py [COMPLETE - All models with validation]
- ✅ backend/server.py [COMPLETE - FastAPI with Pydantic validation at API boundary]
- ✅ backend/agents/base_agent.py [COMPLETE - Agent interface contracts defined]
- ✅ backend/agents/__init__.py [COMPLETE - Agent module exports]
- ✅ backend/utils/type_hints.py [COMPLETE - Type hints and custom types]
- ✅ backend/utils/__init__.py [COMPLETE - Updated exports with type hints]
- ✅ backend/core/constants.py [COMPLETE - Type hints and complete gene metadata]
- ✅ backend/tests/test_pydantic_models.py [COMPLETE - Model validation tests]
- ✅ backend/core/state.py [COMPLETE - Type hints and complete state definition]

**Phase 3 (LangGraph Implementation):**
- backend/core/graph.py [BUILD WORKFLOW - Orchestrate agents]
- backend/agents/validation_agent.py [REFACTOR - Implement ValidationAgent]
- backend/agents/alignment_agent.py [REFACTOR - Implement AlignmentAgent]
- backend/agents/mutation_detection_agent.py [REFACTOR - Implement MutationDetectionAgent]
- backend/agents/annotation_agent.py [REFACTOR - Implement AnnotationAgent]
- backend/agents/classification_agent.py [REFACTOR - Implement ClassificationAgent]
- backend/services/analysis_service.py [INTEGRATE - Connect LangGraph workflow]

**Phase 4 (LlamaIndex Migration):**
- backend/agents/retrieval_agent.py [MIGRATE TO LLAMAINDEX]
- backend/core/config.py [ADD VECTOR DB CONFIG]

**Phase 5 (Server Refactor):**
- backend/server.py [MAJOR REFACTOR FOR LANGGRAPH]
- backend/.env [UPDATE CONFIGURATION]

**Phase 6 (Testing & Validation):**
- backend/tests/ [ADD COMPREHENSIVE TESTS]
- backend/utils/ [ADD MORE VALIDATORS]

## Next Steps

1. ✅ Add new directory structure
2. ✅ Add LangGraph dependencies
3. ✅ Add LlamaIndex dependencies
4. ✅ Create Pydantic models
5. ✅ Implement FastAPI server with request/response validation
6. ✅ Define inter-agent contracts with base Agent interface
7. ✅ Add comprehensive type hints throughout codebase
8. ✅ Complete Phase 2: Models & State (All components ready)
9. **START Phase 3: LangGraph Implementation**
10. Refactor agents to use new base class
11. Build LangGraph workflow orchestration
12. Integrate LangGraph into analysis service
13. Migrate retrieval to LlamaIndex
14. Add comprehensive testing
9. Add error recovery
10. Add type hints throughout

## New Directory Structure (Post-Restructuring)

```
backend/
├── agents/                    # Original agents (to be refactored)
├── config/                    # Configuration files
│   ├── __init__.py
│   └── logging.yaml          # Logging configuration
├── core/                      # Core LangGraph components
│   ├── __init__.py
│   ├── config.py             # Pydantic settings
│   ├── constants.py          # Application constants
│   ├── graph.py              # LangGraph workflow (skeleton)
│   └── state.py              # Shared state definition
├── data/                      # Reference sequences, ClinVar data
├── models/                    # Pydantic models & ML models
│   ├── __init__.py
│   └── pydantic_models.py    # Request/response models (skeleton)
├── notebooks/                 # Jupyter notebooks for analysis
│   └── .gitkeep
├── services/                  # Business logic layer
│   ├── __init__.py
│   └── analysis_service.py   # Main analysis service (skeleton)
├── tests/                     # Test suite
│   ├── __init__.py
│   └── conftest.py           # Pytest fixtures
├── utils/                     # Helper functions
│   ├── __init__.py
│   ├── logger.py             # Logging setup
│   └── validators.py         # Custom validation functions
├── requirements.txt           # Updated with LangGraph/LlamaIndex
├── server.py                  # FastAPI server (to be refactored)
└── .env                       # Environment variables (to be updated)
```

## server.py Analysis

### Current Flow
1. FastAPI receives request
2. Agents execute in sequence (validation → alignment → mutation detection → annotation → classification → retrieval)
3. Results compiled
4. JSON response sent

### Entry Point
@app.post("/analyze")
async def analyze_sequence(request: AnalysisRequest):
    # Current implementation here

### Issues to Fix
- No state management
- Sequential only
- No conditional routing
- Basic error handling (validation fails entire pipeline)
- Agents instantiated per request (inefficient)
- Hard-coded reference sequences loaded at startup
- No partial results on failure

### What Stays the Same
- FastAPI framework
- Basic endpoint structure
- Response format (mostly)
- Reference sequence loading logic

### What Changes
- Orchestration (LangGraph StateGraph)
- Data flow (State-based with shared state)
- Error handling (Per-node with recovery)
- Retrieval (LlamaIndex instead of CSV)
- Agent lifecycle (persistent vs per-request)</content>
<parameter name="filePath">c:\Users\faiza\OneDrive\Desktop\geneMutation\geneMutationDetection\CODEBASE_AUDIT.md