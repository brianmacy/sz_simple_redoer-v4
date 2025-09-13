# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **simple demonstration** Python-based Senzing v4 beta redo processor designed as a starting point for developers. It provides a minimal, clear example of parallel redo record processing using the Senzing entity resolution engine. The entire implementation is intentionally contained in a single script to serve as an educational reference - adapted from sz_sqs_consumer in just 15 minutes to show simplicity.

## Architecture

**Core Components:**
- `sz_simple_redoer.py` - Main application script that implements a multithreaded redo processor
- Uses `concurrent.futures.ThreadPoolExecutor` for parallel processing
- Integrates with Senzing SDK v4 beta through the `senzing` and `senzing_core` modules

**Key APIs Used:**
- `get_redo_record()` - Retrieves redo records from the engine
- `process_redo_record()` - Processes JSON redo records
- `get_stats()` - Retrieves engine diagnostic information
- `SzAbstractFactory` - Initializes the Senzing environment

**Threading Model:**
- Uses ThreadPoolExecutor with configurable worker threads
- Implements timeout handling for long-running records (>5 minutes)
- Handles retries and bad input gracefully
- Includes governor-like behavior to prevent thread pool overflow

## Environment Configuration

**Required:**
```bash
SENZING_ENGINE_CONFIGURATION_JSON  # JSON configuration for Senzing engine
```

**Optional:**
```bash
SENZING_LOG_LEVEL=info  # Log level (default: info)
SENZING_THREADS_PER_PROCESS=4  # Thread pool size (default: auto-detected)
SENZING_REDO_SLEEP_TIME_IN_SECONDS=60  # Pause when no records (default: 60)
LONG_RECORD=300  # Threshold for long-running record warnings (default: 300)
```

## Common Commands

**Build and Run with Docker:**
```bash
docker build -t brian/sz_simple_redoer .
docker run --user $UID -it -e SENZING_ENGINE_CONFIGURATION_JSON brian/sz_simple_redoer
```

**Run locally (requires Senzing SDK):**
```bash
# Set Python path for Senzing SDK
export PYTHONPATH=/opt/senzing/er/sdk/python

# Basic run
python3 sz_simple_redoer.py

# With educational options
python3 sz_simple_redoer.py -i  # Enable WithInfo output printing
python3 sz_simple_redoer.py -t  # Enable debug trace
python3 sz_simple_redoer.py -i -t  # Both options
```

**Development Commands:**
```bash
# Check PEP8 compliance (if flake8 available)
python3 -m flake8 sz_simple_redoer.py

# Validate configuration
python3 -c "import os, orjson; orjson.loads(os.getenv('SENZING_ENGINE_CONFIGURATION_JSON', '{}'))"
```

## Dependencies

- Python 3 with standard libraries
- `orjson` for JSON processing
- Senzing SDK v4 beta (`senzing`, `senzing_core` modules)
- Docker base image: `senzing/senzingsdk-runtime:latest`

## Development Notes

**Keep It Simple Philosophy:**
- Single-file implementation for clarity and ease of understanding
- No complex frameworks or dependencies beyond essential Senzing SDK
- Uses `print()` statements with emojis for clear, educational feedback
- Comprehensive error handling with educational context
- PEP8 compliant code with educational comments throughout

**Educational Design Choices:**
- No traditional test framework - focus on demonstrating core concepts
- Graceful shutdown handling (CTRL+C, SIGTERM) for real-world scenarios
- Real-time statistics and monitoring for learning about performance
- Configuration validation with helpful error messages
- Clear separation of concerns with well-documented functions

**Key Learning Areas Demonstrated:**
- **Threading**: `concurrent.futures.ThreadPoolExecutor` usage patterns
- **Signal Handling**: Graceful shutdown with `signal.signal()`
- **Configuration**: Environment variable handling and validation
- **Error Handling**: Different exception types and recovery strategies
- **Monitoring**: Performance metrics and long-running task detection

**When Extending This Code:**
- Maintain the simple, readable structure for other developers to learn from
- Add complexity only when necessary, document reasoning clearly
- Consider this a template rather than production-ready code
- Keep educational comments when adding new features

**Code Quality:**
- Follows PEP8 style guidelines strictly
- Snake_case naming conventions throughout
- Proper docstrings and inline comments
- Line length kept under 79 characters
- Imports organized alphabetically by category

## File Structure

**Intentionally Minimal:**
- `sz_simple_redoer.py` - **Single main script containing all logic** (keep it this way!)
- `Dockerfile` - Educational containerization with security best practices
- `README.md` - Comprehensive usage documentation with troubleshooting
- `.env.example` - Configuration template with explanations
- `CLAUDE.md` - This development guide
- `.gitignore` - Standard Python exclusions

This deliberately simple structure helps developers quickly understand the complete flow without navigating multiple files or complex module hierarchies. The educational comments and examples make it an ideal learning resource.