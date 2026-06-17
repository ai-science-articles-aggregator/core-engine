# Control prefix for transient status updates on the SSE token stream.
# The ml_cores agent prefixes status messages (e.g. "Reading articles…") with
# this marker; we strip it and re-emit the payload as a `status` event instead
# of answer content (so it isn't persisted into the message text).
# Must stay in sync with ml_cores/services/agent/src/agent.py:STATUS_PREFIX.
STREAM_STATUS_PREFIX = "\x1fstatus\x1f"
