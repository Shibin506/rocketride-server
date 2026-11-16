/**
 * MIT License
 *
 * Copyright (c) 2026 Aparavi Software AG
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

import { it as test } from '@jest/globals';
import assert from 'node:assert/strict';
import { RocketRideClient } from '../src/client/client';

// A bare port names a port on localhost, as in the Python SDK. Without the
// rule, the URL parser reads '5590' as the IPv4 address 0.0.21.214.
test('a bare port means that port on localhost', () => {
	assert.equal(RocketRideClient.normalizeUri('5590'), 'http://localhost:5590');
	assert.equal(RocketRideClient.normalizeUri(' 5565 '), 'http://localhost:5565');
});

test('host:port, hostnames and full URLs keep their host', () => {
	assert.equal(RocketRideClient.normalizeUri('localhost:5590'), 'http://localhost:5590');
	assert.equal(RocketRideClient.normalizeUri('192.168.1.100:5590'), 'http://192.168.1.100:5590');
	assert.equal(RocketRideClient.normalizeUri('my-server'), 'http://my-server:5565');
	assert.equal(RocketRideClient.normalizeUri('https://api.rocketride.ai'), 'https://api.rocketride.ai');
	assert.equal(RocketRideClient.normalizeUri('ws://localhost:5565'), 'ws://localhost:5565');
});
