# sz_simple_redoer

Ported Senzing simple redoer for the Senzing v4 beta

# Overview
Simple parallel redo processor using the Senzing SDK and is meant to provide developers with a simple starting point for a simple, scalable redo processor.  This took 15minutes to adapt from the sz_sqs_consumer project.

# API demonstrated
### Core
* get_redo_record: Retrieve redo record produced by the engine, if any waiting to be processed
* process_redo_record: Processes the JSON redo record
### Supporting
* senzing_core.SzAbstractFactory: To initialize the Sz environment
* get_stats: To retrieve internal engine diagnostic information as to what is going on in the engine


For more details on the Senzing SDK go to https://docs.senzing.com

# Details

### Required parameter (environment)
```
SENZING_ENGINE_CONFIGURATION_JSON
```

### Optional parameters (environment)
```
SENZING_LOG_LEVEL (default: info)
SENZING_THREADS_PER_PROCESS (default: based on whatever concurrent.futures.ThreadPoolExecutor chooses automatically)
SENZING_REDO_SLEEP_TIME_IN_SECONDS (default: 60 seconds)
LONG_RECORD: (default: 300 seconds)
```

## Building/Running
```
docker build -t brian/sz_simple_redoer .
docker run --user $UID -it -e SENZING_ENGINE_CONFIGURATION_JSON brian/sz_simple_redoer
```

## 🔍 Troubleshooting

### Common Issues
- **"No module named 'senzing'"**: Set `PYTHONPATH=/opt/senzing/er/sdk/python`
- **"No redo records available"**: This is normal - the processor waits for work
- **High memory usage**: Reduce `SENZING_THREADS_PER_PROCESS`
- **Configuration errors**: Check your `SENZING_ENGINE_CONFIGURATION_JSON` format

### Getting Started
1. Copy `.env.example` to `.env` and modify the values
2. Ensure Senzing SDK is installed and accessible
3. Run with: `python3 sz_simple_redoer.py`

## 📚 Educational Features

### What This Code Demonstrates
- **ThreadPoolExecutor**: Parallel processing with Python's built-in threading
- **Graceful Shutdown**: Proper signal handling for CTRL+C and container stops
- **Error Handling**: Robust exception handling with educational context
- **Configuration**: Environment-based configuration with validation
- **Monitoring**: Real-time statistics and long-running record detection

### Command Line Options
- `-i, --info`: Enable WithInfo output (shows additional processing data)
- `-t, --debugTrace`: Enable debug tracing (verbose Senzing SDK logs)

## Additional items to note
 * Will exit gracefully on CTRL+C or SIGTERM after processing current records in flight
 * If a record takes more than 5min to process (LONG_RECORD), it will alert you with timing information
 * Uses simple `print()` statements with emojis for clear, educational logging
 * Supports "WithInfo" output via the `-i` command line option for educational purposes
 * Code is PEP8 compliant and heavily commented for learning
