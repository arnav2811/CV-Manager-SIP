# Platform Audit: CV Normalization Engine

## Overview
This document serves as an audit of the newly overhauled CV Normalization Engine (v3.0.0). It outlines the architecture, components, and current status of the pipeline.

## System Architecture

### Master Orchestrator (`engine_orchestrator.py`)
- **Status:** Active
- **Description:** Controls the full 3-layer pipeline.
- **Features:** Supports 'fast', 'standard', and 'full' modes with comprehensive per-layer audit trails.

### Layer 3: Heuristic NLP Engine (`engine_l3.py`)
- **Status:** Active
- **Description:** Pure-Python engine for processing unstructured and conversational text.
- **Strategies:**
  1. Sentence Extraction
  2. Shortcode Expansion
  3. Level Keyword Detection
  4. Field-Only Inference

### Layer 2 Combined: Consensus Voting Engine (`engine_l2_combined.py`)
- **Status:** Active
- **Description:** Executes multiple sub-engines in parallel and fuses outputs via weighted voting.
- **Sub-engines:** RapidFuzz, TF-IDF, Dense Embeddings.
- **Enhancements:** Eradicated superset bias using bespoke combined scorer (`token_set_ratio * 0.65 + token_sort_ratio * 0.35`).

## User Interfaces

### Interactive CLI Proof of Concept (`app.py`)
- **Status:** Active
- **Description:** Unified CLI for all pipeline interactions, replacing previous FastAPI/Uvicorn REST dependencies for improved stability.

## Known Issues & Action Items
- Monitor the recent 'field-extraction regex' modifications (`\s+in\s+`) for any unexpected edge cases.
- Perform continuous evaluation of the weighted voting thresholds in Layer 2 Combined.
- Finalize evaluation metrics for the Growth Grids handoff.

## Security & Dependencies
- All REST server dependencies (FastAPI, Uvicorn) have been successfully removed, reducing the attack surface.
- Dependencies tracked and updated in `requirements.txt`.

---
*Audit generated automatically. Please update as the platform evolves.*
