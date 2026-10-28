# MIT License
#
# Copyright (c) 2026 Aparavi Software AG
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Persist mode reconnects after a dropped connection (#2828).

The reconnect engine logged through ``self._debug_message``, which exists only on
the transport, so the client raised AttributeError the moment a persist-mode
connection dropped: no reconnect was scheduled and ``on_connect_error`` never ran.

No server is needed. The transport is never opened: each test drives the
reconnect engine directly and replaces ``_internal_attach`` with a stand-in that
fails or succeeds on demand.
"""

import asyncio

from rocketride import RocketRideClient


def _persist_client(**kwargs) -> RocketRideClient:
    """A persist-mode client that believes it was attached and has just dropped."""
    client = RocketRideClient(uri='ws://localhost:5565', auth='key', persist=True, **kwargs)
    client._desired_state = 'attached'
    return client


async def _settle(client: RocketRideClient) -> None:
    """Let a scheduled reconnect attempt run to completion."""
    for _ in range(50):
        timer = client._reconnect_timer
        if timer is None or timer.done():
            return
        await asyncio.sleep(0.01)


async def test_a_dropped_connection_schedules_a_reconnect():
    client = _persist_client()
    client._current_reconnect_delay = 60  # never fires during the test

    await client.on_disconnected('connection lost', True)

    try:
        assert client._reconnect_timer is not None
        assert not client._reconnect_timer.done()
    finally:
        client._clear_reconnect_timer()


async def test_a_failed_reconnect_reports_the_error_and_tries_again():
    errors = []

    async def on_connect_error(message):
        errors.append(message)

    client = _persist_client(on_connect_error=on_connect_error)
    attempts = []

    async def failing_attach(timeout=None):
        attempts.append(timeout)
        client._current_reconnect_delay = 5  # the next attempt waits past the end of the test
        raise ConnectionError('refused')

    client._internal_attach = failing_attach
    client._current_reconnect_delay = 0

    await client.on_disconnected('connection lost', True)
    first = client._reconnect_timer
    await _settle(client)

    try:
        assert len(attempts) == 1
        assert errors == ['refused']
        # The next attempt is scheduled, with the backoff increased.
        assert client._reconnect_timer is not None and client._reconnect_timer is not first
        assert not client._reconnect_timer.done()
        assert client._current_reconnect_delay == 5.25
    finally:
        client._clear_reconnect_timer()


async def test_a_successful_reconnect_resets_the_backoff():
    messages = []
    client = _persist_client(on_debug_message=messages.append)

    async def attach(timeout=None):
        return None

    client._internal_attach = attach
    client._current_reconnect_delay = 0

    await client.on_disconnected('connection lost', True)
    await _settle(client)

    assert client._reconnect_timer is None
    assert client._current_reconnect_delay == 0.25
    assert any('Reconnect successful' in m for m in messages)
