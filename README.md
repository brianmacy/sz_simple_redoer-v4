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

## Additional items to note
 * Will exit on non-data related exceptions after processing or failing to process the current records in flight
 * If a record takes more than 5min to process (LONG_RECORD), it will let you know which record it is and how long it has been processing
 * Does not use the senzing-###### format for log messages (unlike the senzing/redoer) and simply uses python `print` with strings.  It does use the standard senzing governor-postgresql-transaction-id module so you will see some messages using the standard format.
 * Does not support "WithInfo" output to queues but you can provide a "-i" command line option that will enable printing the WithInfo responses out.  It is simple enough to code in whatever you want done with WithInfo messages in your solution.
