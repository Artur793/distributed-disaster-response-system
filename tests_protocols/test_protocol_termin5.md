# Test_Termin5 Report --- DoY5BlockTeamF

## Project Overview

The purpose of these tests is to verify the decentralized charging
coordination introduced in Aufgabe 4 using the Ricart/Agrawala mutual
exclusion algorithm.

The tests verify:

-   Ricart/Agrawala request and reply handling
-   Mutual exclusion state transitions
-   Vehicle RPC charging restrictions
-   Charging coordination performance
-   Charging coordination latency

------------------------------------------------------------------------

# Test Execution

## Deploy all Containers

``` bash
docker compose up
```

## Run All Tests

``` bash
pytest -v
```

------------------------------------------------------------------------

# Test Summary

  Test Category                  Test Count   Passed   Failed
  ---------------------------- ------------ -------- --------
  Charging Coordinator Tests              7        7        0
  RPC Vehicle Tests                       4        4        0
  Charging Performance Tests              2        2        0
  Charging Latency Tests                  2        2        0
  **TOTAL**                          **15**   **15**    **0**

------------------------------------------------------------------------

# 1. Charging Coordinator Tests

File

``` text
tests/test_charging_coordinator.py
```

## Objective

Validate the Ricart/Agrawala coordination algorithm implemented inside
every charging vehicle.

### Verified

-   REQUEST generation
-   REQUEST priority comparison
-   Deferred replies
-   Duplicate request handling
-   Transition RELEASED → WANTED → HELD
-   Transition HELD → RELEASED
-   Deferred replies are released after charging

### Result

All coordinator tests completed successfully.

**Status:** PASS

------------------------------------------------------------------------

# 2. RPC Vehicle Tests

File

``` text
tests/test_rpc_vehicle.py
```

## Objective

Validate that vehicle RPC behaviour remains correct after introducing
charging coordination.

### Verified

-   Idle vehicle accepts missions
-   Busy vehicle rejects additional missions
-   Incompatible missions are rejected
-   Vehicle participating in charging coordination follows the updated
    assignment rules

### Result

All RPC vehicle tests completed successfully.

**Status:** PASS

------------------------------------------------------------------------

# 3. Charging Performance Tests

File

``` text
tests/test_ra_charging_performance.py
```

## Objective

Measure the execution performance of the charging coordination
implementation.

### Test 1

**Test:** `test_update_participant_performance`

Measured Result

``` text
Iterations : 10000
Average    : 0.0011 ms
Minimum    : 0.0010 ms
Maximum    : 0.0147 ms
```

Result: PASS

### Test 2

**Test:** `test_get_status_performance`

Measured Result

``` text
Average : 0.0052 ms
```

Result: PASS

------------------------------------------------------------------------

# 4. Charging Latency Tests

File

``` text
tests/test_ra_charging_latency.py
```

## Objective

Measure the latency of the Ricart/Agrawala charging coordination
workflow using both the real vehicle implementation and the coordinator
implementation.

### Test 1

**Test:** `test_vehicle_request_to_held_latency`

**Objective**

Measure the latency of the complete vehicle-side charging request
workflow, starting from the vehicle requesting access to the charging
station until it successfully enters the HELD state.

The test executes the real implementation of:

-   `request_charging_access()`
-   `VehicleChargingCoordinator.start_request()`
-   MQTT request payload creation
-   `handle_charging_reply()`
-   `VehicleChargingCoordinator.receive_reply()`
-   Transition to `HELD`

Only the external MQTT communication is mocked while the application
logic is executed unchanged.

Measured Result

``` text
Iterations : 500
Average    : 0.0047 ms
Minimum    : 0.0043 ms
Maximum    : 0.0286 ms
```

Result: PASS

### Test 2

**Test:** `test_finish_charging_latency`

**Objective**

Measure the latency required to release the charging station after
charging has completed. This includes the transition from HELD to
RELEASED and preparation of deferred replies.

Measured Result

``` text
Average : 0.0003 ms
```

Result: PASS

------------------------------------------------------------------------

# Performance Summary

  Metric                             Measured Value Result
  -------------------------------- ---------------- --------
  Vehicle request → HELD latency      **0.0047 ms** PASS
  Charging release latency            **0.0003 ms** PASS
  Charging state update               **0.0011 ms** PASS
  Status retrieval                    **0.0052 ms** PASS

------------------------------------------------------------------------

# Overall Assessment

The functional tests verify the correctness of the Ricart/Agrawala
charging coordination algorithm, including request handling, reply
processing, deferred replies, duplicate message handling, and charging
state transitions.

The updated RPC vehicle tests confirm that charging coordination
integrates correctly with the existing mission assignment behaviour.

The non-functional tests demonstrate that both the coordinator and the
complete vehicle charging workflow execute efficiently. The integration
latency test measures the real execution path from
`request_charging_access()` through REQUEST creation, REPLY processing,
and the transition to the HELD state. The measured average latency of
**0.0047 ms** shows that the complete charging coordination workflow
executes within a few microseconds. Charging state updates, status
retrieval, and charging release operations also complete within
microseconds, confirming that the decentralized Ricart/Agrawala
implementation introduces negligible overhead.

No failures occurred during execution.

## Final Result

``` text
PASSED: 15
FAILED: 0
```
