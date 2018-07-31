# freeradius-datadog-metrics

This repo contains a Datadog agent check to monitor [FreeRADIUS](https://freeradius.org/). The check will publish one service check to Datadog, called `freeradius`. It also records a number of custom metrics about what the FreeRADIUS process is doing.


## Installation

Prerequisites:

* A working installation of FreeRADIUS.
* `radclient` installed on the server that will be running the custom check. (On Ubuntu, at least, this is installed with the FreeRADIUS server.)

To install:

1. [Configure a status server](https://wiki.freeradius.org/config/Status) on your FreeRADIUS installation.
1. Configure the Datadog Agent to collect stats (assuming the agent is already installed):
    1. Copy `freeradius.py` to `/etc/datadog-agent/checks.d/`.
    1. Copy `freeradius.yaml` to `/etc/datadog-agent/conf.d/` and customize for your implementation. Each instance must have a `host`, `port` and `secret`. You can also optionally include a `type` of 1, 2, 4, 8, corresponding to [the `FreeRADIUS-Statistics-Type` parameter](https://wiki.freeradius.org/config/Status#querying-with-radclient). If you don't include a `type`, all four types will be queried (warning, this will create quite a few custom metrics).
    1. Restart the `datadog-agent` service.


## List of custom metrics published

* `freeradius.response_time`: _gauge_, response time of the status request, in seconds. If you don't include a `type`, the check will make four status requests, and this will be the mean response time of all requests.
* **Type 1: Authentication Counters**
    * freeradius.access.requests
    * freeradius.access.accepts
    * freeradius.access.rejects
    * freeradius.access.challenges
    * freeradius.auth.responses
    * freeradius.auth.duplicate.requests
    * freeradius.auth.malformed.requests
    * freeradius.auth.invalid.requests
    * freeradius.auth.dropped.requests
    * freeradius.auth.unknown.types
* **Type 2: Accounting Counters**
    * freeradius.accounting.requests
    * freeradius.accounting.responses
    * freeradius.acct.duplicate.requests
    * freeradius.acct.malformed.requests
    * freeradius.acct.invalid.requests
    * freeradius.acct.dropped.requests
    * freeradius.acct.unknown.types
* **Type 4: Proxy Authentication Counters**
    * freeradius.proxy.access.requests
    * freeradius.proxy.access.accepts
    * freeradius.proxy.access.rejects
    * freeradius.proxy.access.challenges
    * freeradius.proxy.auth.responses
    * freeradius.proxy.auth.duplicate.requests
    * freeradius.proxy.auth.malformed.requests
    * freeradius.proxy.auth.invalid.requests
    * freeradius.proxy.auth.dropped.requests
    * freeradius.proxy.auth.unknown.types
* **Type 8: Proxy Accounting Counters**
    * freeradius.proxy.accounting.requests
    * freeradius.proxy.accounting.responses
    * freeradius.proxy.acct.duplicate.requests
    * freeradius.proxy.acct.malformed.requests
    * freeradius.proxy.acct.invalid.requests
    * freeradius.proxy.acct.dropped.requests
    * freeradius.proxy.acct.unknown.types

Except for `freeradius.response_time`, all metrics are monotonic counters that will reset when the `freeradius` process restarts.
