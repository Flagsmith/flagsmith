---
title: Load Testing
description: Instructions for load testing using JMeter and wrk.
---

## JMeter

There are [JMeter](https://jmeter.apache.org/) tests available in our public repo on GitHub:

https://github.com/Flagsmith/flagsmith/tree/main/api/jmeter-tests

## wrk

We also recommend using [wrk](https://github.com/wg/wrk) for load testing the core SDK endpoints. Some examples of this (make sure you update URL and environment keys!):

```bash
# Get flags endpoint
wrk -t6 -c200 -d20s -H 'X-Environment-Key: iyiS5EDNDxMDuiFpHoiwzG' http://127.0.0.1:8000/api/v1/flags/

# Get flags for an identity
wrk -t6 -c200 -d20s -H 'X-Environment-Key: iyiS5EDNDxMDuiFpHoiwzG' "http://127.0.0.1:8000/api/v1/identities/?identifier=mrflags@flagsmith.com"
```
