#! /usr/bin/env python3

import argparse
import concurrent.futures
import logging
import orjson
import os
import signal
import sys
import time
import traceback

from senzing import (
    SzBadInputError,
    SzConfig,
    SzConfigManager,
    SzEngine,
    SzEngineFlags,
    SzRetryTimeoutExceededError,
)

import senzing_core

# Educational constants with explanations
STATS_INTERVAL = 1000  # Report progress every N messages
LONG_RECORD = int(os.getenv("LONG_RECORD", "300"))  # Seconds before record is considered long-running
EMPTY_PAUSE_TIME = int(os.getenv("SENZING_REDO_SLEEP_TIME_IN_SECONDS", "60"))  # Pause when no records available
THREAD_POLL_TIMEOUT = 10  # Seconds to wait for thread completion
EMPTY_QUEUE_SLEEP = 1  # Seconds to sleep when thread pool full

TUPLE_MSG = 0
TUPLE_STARTTIME = 1

# Define missing constants used in logging_id function
PARAMS = "PARAMS"
PARAM = "PARAM"
VALUE = "VALUE"

log_format = "%(asctime)s %(message)s"

# Global shutdown flag for graceful termination
shutdown_requested = False


def signal_handler(sig, frame):
    """Handle graceful shutdown signals."""
    global shutdown_requested
    print('\n🛑 Graceful shutdown requested...')
    shutdown_requested = True


def validate_config():
    """Simple validation for educational purposes."""
    required_env = "SENZING_ENGINE_CONFIGURATION_JSON"
    config = os.getenv(required_env)
    if not config:
        print(f"❌ Missing required environment variable: {required_env}")
        print("💡 This tells Senzing how to connect to your data store")
        print("📖 See: https://docs.senzing.com for configuration examples")
        return False

    # Basic JSON validation for educational purposes
    try:
        orjson.loads(config)
        print(f"✅ Configuration validated: {len(config)} characters")
        return True
    except orjson.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {required_env}: {e}")
        return False


def print_simple_stats(messages, start_time, active_threads, max_threads):
    """Educational metrics display."""
    elapsed = time.time() - start_time
    rate = messages / elapsed if elapsed > 0 else 0
    print(f"📈 Stats: {messages} processed, {rate:.1f}/sec, "
          f"{active_threads}/{max_threads} threads active, "
          f"runtime: {elapsed:.0f}s")


def logging_id(rec):
    """Generate a logging ID for the record."""
    dsrc = rec.get("DATA_SOURCE")
    rec_id = rec.get("RECORD_ID")
    if dsrc and rec_id:
        return f'{dsrc} : {rec_id}'
    umf_proc = rec.get("UMF_PROC")  # repair messages
    if umf_proc:
        try:
            return f'{umf_proc[PARAMS][0][PARAM][VALUE]} : REPAIR_ENTITY'
        except (KeyError, IndexError, TypeError):
            return 'UMF_PROC : REPAIR_ENTITY'
    return "UNKNOWN RECORD"

def process_msg(engine, msg, info):
    """Process a redo message using the Senzing engine."""
    try:
        if info:
            response = engine.process_redo_record(
                msg, SzEngineFlags.SZ_WITH_INFO
            )
            return response
        else:
            engine.process_redo_record(msg)
            return None
    except Exception as err:
        print(f"{err} [{msg}]", file=sys.stderr)
        raise


try:
    # Educational: Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)   # CTRL+C
    signal.signal(signal.SIGTERM, signal_handler)  # Container stop

    # Educational: Configure Python logging
    log_level_map = {
        "notset": logging.NOTSET,
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "fatal": logging.FATAL,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    log_level_parameter = os.getenv("SENZING_LOG_LEVEL", "info").lower()
    log_level = log_level_map.get(log_level_parameter, logging.INFO)
    logging.basicConfig(format=log_format, level=log_level)

    # Educational: Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Simple Senzing redo processor for educational purposes"
    )
    parser.add_argument(
        "-i",
        "--info",
        dest="info",
        action="store_true",
        default=False,
        help="produce withinfo messages (educational: shows additional data)",
    )
    parser.add_argument(
        "-t",
        "--debugTrace",
        dest="debugTrace",
        action="store_true",
        default=False,
        help="output debug trace information (educational: verbose Senzing logs)",
    )
    args = parser.parse_args()

    # Educational: Validate configuration before proceeding
    if not validate_config():
        exit(1)

    # Educational: Initialize Senzing SDK
    engine_config = os.getenv("SENZING_ENGINE_CONFIGURATION_JSON")
    factory = senzing_core.SzAbstractFactoryCore(
        "sz_simple_redoer", engine_config, verbose_logging=args.debugTrace
    )
    g2 = factory.create_engine()
    start_time = log_check_time = prev_time = time.time()

    # Educational: Configure thread pool size
    max_workers = int(os.getenv("SENZING_THREADS_PER_PROCESS", "0"))
    if not max_workers:  # Let Python choose optimal thread count
        max_workers = None
    print(f"🔧 Thread pool configured: {max_workers or 'auto-detected'} workers")

    messages = 0

    # Educational: ThreadPoolExecutor automatically manages worker threads
    with concurrent.futures.ThreadPoolExecutor(max_workers) as executor:
        print(f"🚀 Started with {executor._max_workers} worker threads")
        # Educational: futures dict maps {future_object: (message, start_time)}
        futures = {}
        empty_pause = 0
        try:
            # Educational: Main processing loop - this is the "heart" of the processor
            while not shutdown_requested:

                now_time = time.time()
                if futures:
                    # Educational: Wait for any thread to complete work
                    timeout = min(THREAD_POLL_TIMEOUT, max(1, len(futures)))
                    done, _ = concurrent.futures.wait(
                        futures,
                        timeout=timeout,
                        return_when=concurrent.futures.FIRST_COMPLETED,
                    )

                    # Educational: Process completed futures (finished work)
                    for fut in done:
                        msg = futures.pop(fut)
                        try:
                            result = fut.result()
                            if result:
                                print(
                                    result
                                )  # would handle pushing to withinfo queues here
                        except (SzRetryTimeoutExceededError, SzBadInputError) as err:
                            record = orjson.loads(msg[TUPLE_MSG])
                            print(
                                f'⚠️ FAILED due to bad data or timeout: '
                                f'{record["DATA_SOURCE"]} : {record["RECORD_ID"]}'
                            )

                        messages += 1

                        # Educational: Display progress statistics
                        if messages % STATS_INTERVAL == 0:
                            diff = now_time - prev_time
                            active_threads = sum(1 for f in futures if not f.done())
                            print_simple_stats(messages, start_time, active_threads, executor._max_workers)
                            prev_time = now_time

                    # Educational: Monitor for long-running records
                    if now_time > log_check_time + (LONG_RECORD / 2):
                        log_check_time = now_time

                        response = g2.get_stats()
                        print(f"\n{response}\n")

                        # Educational: Check for stuck threads
                        num_stuck = 0
                        for fut, msg in futures.items():
                            if not fut.done():
                                duration = now_time - msg[TUPLE_STARTTIME]
                                if duration > LONG_RECORD * 2:
                                    num_stuck += 1
                                    record = orjson.loads(msg[TUPLE_MSG])
                                    print(
                                        f'⏱️ Long record ({duration/60:.1f} min): {logging_id(record)}'
                                    )
                        if num_stuck >= executor._max_workers:
                            print(
                                f'⚠️ All {executor._max_workers} threads '
                                f'are stuck on long running records'
                            )

                # Educational: Throttle when thread pool is full
                if len(futures) >= executor._max_workers:
                    time.sleep(EMPTY_QUEUE_SLEEP)
                    continue

                # Educational: Handle pauses when no records are available
                if empty_pause:
                    if time.time() < empty_pause:
                        time.sleep(EMPTY_QUEUE_SLEEP)
                        continue
                    empty_pause = 0

                # Educational: Fill thread pool with work if available
                while len(futures) < executor._max_workers:
                    try:
                        response = g2.get_redo_record()
                        if not response:
                            print(
                                f"🚨 No redo records available. "
                                f"Pausing for {EMPTY_PAUSE_TIME} seconds."
                            )
                            empty_pause = time.time() + EMPTY_PAUSE_TIME
                            break
                        # Educational: Submit work to thread pool
                        msg = response
                        futures[executor.submit(process_msg, g2, msg, args.info)] = (
                            msg,
                            time.time(),
                        )
                    except Exception as err:
                        print(f"⚠️ {type(err).__name__} in redo retrieval: {err}", file=sys.stderr)
                        raise

            # Educational: Final statistics on normal completion
            final_active = sum(1 for f in futures if not f.done())
            print_simple_stats(messages, start_time, final_active, executor._max_workers)
            print(f"✅ Completed processing {messages} redo records")

        except Exception as err:
            print(
                f"⚠️ {type(err).__name__}: Shutting down due to error: {err}",
                file=sys.stderr,
            )
            print(f"📏 Processed {messages} records before failure")
            traceback.print_exc()

            # Educational: Show what work is still in progress during shutdown
            now_time = time.time()
            for fut, msg in futures.items():
                if not fut.done():
                    duration = now_time - msg[TUPLE_STARTTIME]
                    record = orjson.loads(msg[TUPLE_MSG])
                    print(
                        f'⏱️ Still processing ({duration/60:.1f} min): {logging_id(record)}'
                    )
            executor.shutdown(wait=True)  # Educational: Wait for threads to complete
            exit(1)

except Exception as err:
    print(f"⚠️ Fatal error during startup: {err}", file=sys.stderr)
    traceback.print_exc()
    exit(1)
