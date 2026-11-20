# Packet captures, socket inspection and common outage patterns

> **Before this lesson:** read [Network debugging tools: ping, traceroute, dig and curl](#/lesson/networking/cli-tools). Reading packet traces relies on TCP flags, sequence numbers and connection states from [UDP and the TCP connection lifecycle](#/lesson/networking/udp-tcp-lifecycle), and on retransmission and windows from [Flow control and congestion control](#/lesson/networking/tcp-flow-congestion). The outage patterns draw on [Timeouts, retries, pools, rate limits and idempotency](#/lesson/networking/resilience-patterns).

## In plain words

The tools in the previous lesson tell you *that* something failed and roughly where. Sometimes that is not enough: two systems each insist they are behaving correctly, and the truth is somewhere between them.

At that point you stop asking the programs and look at what was actually sent. A **packet capture** is a recording of the packets passing through a network interface, like a security camera pointed at a doorway. Whatever each side claims, the recording shows who sent what, in which order, and when.

A second kind of evidence comes from inside the machine: the operating system keeps a table of every connection and every listening port. Reading that table is like checking a hotel's register: which rooms are occupied, by whom, and who has been waiting at reception.

The last part of this lesson is a field guide. Network outages are rarely original. The same dozen patterns recur across companies and decades, and knowing their signatures lets you recognise one within minutes instead of rediscovering it over hours.

Why this matters for a job: senior engineers are distinguished less by knowing more commands than by recognising patterns. "Requests fail on the first call after a quiet period" and "errors started exactly ninety days after the last deployment" are each a sentence that points straight at a cause, if you have seen the pattern. Site-reliability and backend interviews often present such a scenario and ask what you would suspect.

## Part 1: Packet capture

### The idea and the tools

A capture tool asks the operating system for a copy of every packet on an interface that matches a **filter**.

- **`tcpdump`** is the command-line tool, present on almost every server. It prints one line per packet or writes them to a file.
- **Wireshark** is a graphical analyser that decodes hundreds of protocols and can open files written by tcpdump. The usual workflow: capture on the server with tcpdump, analyse on your own machine with Wireshark.

Capture files use the **pcap** format. Capturing needs administrator rights, because it can see everyone's traffic on that machine.

```
sudo tcpdump -i eth0 -nn host 203.0.113.80 and port 443           # print matching packets
sudo tcpdump -i any -nn -w /tmp/trace.pcap 'tcp port 5432'        # write to a file for Wireshark
sudo tcpdump -i eth0 -nn -c 200 'tcp[tcpflags] & (tcp-syn|tcp-rst) != 0'   # only SYN and RST packets
```

| Option | Meaning |
|---|---|
| `-i eth0` / `-i any` | which interface to listen on |
| `-nn` | print numeric addresses and ports; do not look up names |
| `-c 200` | stop after 200 packets |
| `-w file` | write raw packets to a file instead of printing |
| `-r file` | read a saved file |
| `-A` / `-X` | also print packet contents as text / as hexadecimal |

The expression at the end is a capture filter. Useful building blocks: `host 10.0.0.5`, `net 10.0.0.0/24`, `port 443`, `tcp`, `udp`, `icmp`, combined with `and`, `or`, `not`. **Always filter.** An unfiltered capture on a busy server produces gigabytes within seconds.

Two practical cautions. A capture shows what one machine saw; if a firewall dropped a packet before it arrived, the packet is absent, which is itself evidence. Comparing captures taken at both ends shows where packets disappear. And with TLS you see the handshake and the sizes and timing of encrypted records, not the contents (Wireshark can decrypt if the client is configured to export its session keys).

### Reading tcpdump output

One line per packet. Here is a short, healthy HTTP exchange:

```
10:15:01.000000 IP 10.0.0.5.51822 > 203.0.113.80.80: Flags [S], seq 1000, win 64240, options [mss 1460,sackOK,TS,wscale 7], length 0
10:15:01.030112 IP 203.0.113.80.80 > 10.0.0.5.51822: Flags [S.], seq 7000, ack 1001, win 65160, options [mss 1460,sackOK,TS,wscale 7], length 0
10:15:01.030180 IP 10.0.0.5.51822 > 203.0.113.80.80: Flags [.], ack 1, win 502, length 0
10:15:01.030410 IP 10.0.0.5.51822 > 203.0.113.80.80: Flags [P.], seq 1:79, ack 1, win 502, length 78: HTTP: GET /health HTTP/1.1
10:15:01.060552 IP 203.0.113.80.80 > 10.0.0.5.51822: Flags [.], ack 79, win 509, length 0
10:15:01.064890 IP 203.0.113.80.80 > 10.0.0.5.51822: Flags [P.], seq 1:201, ack 79, win 509, length 200: HTTP: HTTP/1.1 200 OK
10:15:01.064950 IP 10.0.0.5.51822 > 203.0.113.80.80: Flags [.], ack 201, win 501, length 0
10:15:01.065300 IP 10.0.0.5.51822 > 203.0.113.80.80: Flags [F.], seq 79, ack 201, win 501, length 0
10:15:01.095410 IP 203.0.113.80.80 > 10.0.0.5.51822: Flags [F.], seq 201, ack 80, win 509, length 0
10:15:01.095470 IP 10.0.0.5.51822 > 203.0.113.80.80: Flags [.], ack 202, win 501, length 0
```

Each field:

- **Timestamp.** Differences between lines are your stopwatch.
- **`source.port > destination.port`.** The last number after the final dot is the port.
- **Flags.** The notation is compact:

  | Shown | Flags set | Meaning |
  |---|---|---|
  | `[S]` | SYN | connection request |
  | `[S.]` | SYN + ACK | connection accepted (the dot means ACK) |
  | `[.]` | ACK only | a pure acknowledgement |
  | `[P.]` | PSH + ACK | data, delivered promptly |
  | `[F.]` | FIN + ACK | this side has finished sending |
  | `[R]` or `[R.]` | RST | abort |

- **`seq 1:79`**: this segment carries bytes 1 up to but not including 79, so `length 78`. After the handshake tcpdump shows **relative** sequence numbers, counted from the start of the connection, which makes arithmetic easy.
- **`ack 79`**: "I have everything before byte 79."
- **`win`**: the advertised receive window (to be multiplied by the scale factor from the handshake).
- **`options`**: on the SYN packets you see what was negotiated: MSS, selective acknowledgements, timestamps, window scaling.

Now read the trace as a story. Lines 1–3 are the three-way handshake; the gap between the SYN and the SYN-ACK is 30 ms, which is the round-trip time. Line 4 is the request (78 bytes). Line 5 acknowledges it 30 ms later. Line 6 is the response, arriving 34.5 ms after the request was sent: one round trip plus about 4 ms of server work. Lines 8–10 close the connection in both directions; note `ack 80` and `ack 202`, each one more than the data because a FIN consumes a sequence number.

### Signatures of trouble

What the common failures look like in a capture:

**Nobody answers (a timeout).** The SYN is repeated with doubling gaps and nothing comes back. A firewall is dropping it, the address is wrong, or the host is down.

```
10:20:00.000 IP 10.0.0.5.40112 > 10.9.9.9.6379: Flags [S], seq 500, length 0
10:20:01.001 IP 10.0.0.5.40112 > 10.9.9.9.6379: Flags [S], seq 500, length 0      <- retry after 1 s
10:20:03.005 IP 10.0.0.5.40112 > 10.9.9.9.6379: Flags [S], seq 500, length 0      <- after 2 s more
10:20:07.013 IP 10.0.0.5.40112 > 10.9.9.9.6379: Flags [S], seq 500, length 0      <- after 4 s more
```

**Refused.** The SYN is answered at once with a reset. The machine is reachable and nothing listens on that port.

```
10:21:00.000 IP 10.0.0.5.40200 > 10.0.0.9.5433: Flags [S], seq 900, length 0
10:21:00.000410 IP 10.0.0.9.5433 > 10.0.0.5.40200: Flags [R.], seq 0, ack 901, length 0
```

**Loss and retransmission.** The same sequence range appears twice from the sender, and the receiver repeats the same acknowledgement number (duplicate ACKs).

```
IP A > B: Flags [.], seq 1:1461, ack 1, length 1460
IP A > B: Flags [.], seq 1461:2921, ack 1, length 1460        <- this one is lost on the way
IP A > B: Flags [.], seq 2921:4381, ack 1, length 1460
IP B > A: Flags [.], ack 1461, length 0
IP B > A: Flags [.], ack 1461, options [sack 2921:4381], length 0    <- duplicate ACK: "still waiting for 1461"
IP A > B: Flags [.], seq 1461:2921, ack 1, length 1460        <- the retransmission
IP B > A: Flags [.], ack 4381, length 0                       <- everything acknowledged at once
```

**A slow receiver.** The receiver's advertised window shrinks to zero and the sender stops. The application on the receiving side is not reading its data.

```
IP B > A: Flags [.], ack 90001, win 0, length 0               <- zero window: "stop, my buffer is full"
```

**A reset in the middle of a conversation.** One side (or a device between them) aborts. Typical causes: the application crashed or closed the socket with unread data; a firewall, NAT or load balancer had forgotten the connection after an idle period and rejected the next packet.

**A stalled large transfer.** Small packets flow, full-sized ones (1460 bytes of payload) are sent again and again without acknowledgement. This is the signature of an MTU problem with ICMP blocked.

### Try it: analyse a capture with code

The program takes a simplified capture as a list of records and reports the handshake time, retransmissions and how the connection ended. Reading it shows how the reasoning above becomes mechanical.

```python-run
# (time in s, sender, flags, relative seq, ack, payload length)
capture = [
    (0.000, "client", "S",  0,    0,    0),
    (0.042, "server", "S.", 0,    1,    0),
    (0.042, "client", ".",  1,    1,    0),
    (0.043, "client", "P.", 1,    1,    120),     # the request
    (0.086, "server", ".",  1,    121,  0),
    (0.130, "server", ".",  1,    121,  1460),
    (0.130, "server", ".",  1461, 121,  1460),    # never reaches the client
    (0.131, "server", "P.", 2921, 121,  600),
    (0.172, "client", ".",  121,  1461, 0),
    (0.173, "client", ".",  121,  1461, 0),       # duplicate ACK
    (0.390, "server", ".",  1461, 121,  1460),    # the same bytes again: a retransmission
    (0.432, "client", ".",  121,  3521, 0),
    (0.433, "client", "F.", 121,  3521, 0),
    (0.475, "server", "F.", 3521, 122,  0),
    (0.475, "client", ".",  122,  3522, 0),
]

# 1. Handshake round-trip time: SYN to SYN-ACK.
syn = next(p for p in capture if p[2] == "S")
synack = next(p for p in capture if p[2] == "S.")
print(f"handshake RTT: {(synack[0] - syn[0]) * 1000:.0f} ms")

# 2. Retransmissions: a data segment whose (sender, seq) was already seen.
seen, retransmissions = set(), []
for t, sender, flags, seq, ack, length in capture:
    if length > 0:
        if (sender, seq) in seen:
            retransmissions.append((t, sender, seq, length))
        seen.add((sender, seq))
for t, sender, seq, length in retransmissions:
    print(f"retransmission at {t:.3f}s by {sender}: bytes {seq}..{seq + length - 1}")

# 3. Duplicate ACKs: the same pure acknowledgement number repeated by one side.
last_ack, duplicates = {}, 0
for t, sender, flags, seq, ack, length in capture:
    if flags == "." and length == 0:
        if last_ack.get(sender) == ack:
            duplicates += 1
        last_ack[sender] = ack
print("duplicate ACKs:", duplicates)

# 4. How long did recovery take?
if retransmissions:
    first_copy = next(p for p in capture if p[1] == retransmissions[0][1] and p[3] == retransmissions[0][2])
    print(f"the lost segment was resent {(retransmissions[0][0] - first_copy[0]) * 1000:.0f} ms after the original")

# 5. How did it end?
flags_seen = {p[2] for p in capture}
ending = "reset (RST)" if any("R" in f for f in flags_seen) else "clean close (FIN from both sides)" if any("F" in f for f in flags_seen) else "still open"
print("ending:", ending)
print(f"total duration: {capture[-1][0] * 1000:.0f} ms")
```

The output says the path has a 42 ms round trip, one segment was lost and resent 260 ms later (a timer expiry: only one duplicate ACK arrived, too few for fast retransmit), and the connection closed cleanly. More than half of the total time was spent waiting for that one retransmission, which is head-of-line blocking seen directly in the data.

### Wireshark in three features

- **Display filters** narrow what you see after capturing: `tcp.port == 443`, `ip.addr == 10.0.0.5`, `http.response.code >= 500`, `dns`, `tcp.flags.reset == 1`, and the invaluable `tcp.analysis.retransmission` and `tcp.analysis.zero_window`.
- **Follow → TCP Stream** reassembles one connection and shows the conversation as readable text.
- **Statistics → Conversations** and the **Expert Information** panel summarise who talked to whom and flag retransmissions, resets and other anomalies automatically.

> [!WARNING]
> Captures contain whatever was sent: passwords, tokens, cookies and personal data in any unencrypted traffic. Capture only what you are authorised to, filter tightly, treat the files as sensitive, and delete them when the investigation ends.

## Part 2: Inspecting sockets

The operating system knows every socket. On Linux the tool is **`ss`** (socket statistics); the older `netstat` shows the same information and still exists on macOS and Windows.

### What is listening?

```
$ ss -tlnp
State   Recv-Q  Send-Q  Local Address:Port   Peer Address:Port  Process
LISTEN  0       4096    0.0.0.0:443          0.0.0.0:*          users:(("nginx",pid=812,fd=6))
LISTEN  0       128     127.0.0.1:5432       0.0.0.0:*          users:(("postgres",pid=640,fd=5))
LISTEN  0       511     [::]:8080            [::]:*             users:(("node",pid=1290,fd=19))
```

The options: `-t` TCP, `-l` listening sockets only, `-n` numeric, `-p` show the owning process. Read the local address closely:

- `0.0.0.0:443` (or `[::]:…` for IPv6): listening on **all** interfaces; reachable from other machines.
- `127.0.0.1:5432`: listening on **loopback only**; reachable solely from the same machine.

That second line explains one of the most common "connection refused" puzzles: a service that works when tested on the server itself and refuses every remote client. It is bound to `127.0.0.1`. In containers the same mistake appears constantly: a process listening on loopback inside its container is unreachable from outside it.

For a listening socket, `Send-Q` is the maximum length of the accept queue (the backlog) and `Recv-Q` is how many established connections are waiting for the application to accept them. A `Recv-Q` that stays near the maximum means the application cannot keep up with new connections.

### What connections exist?

```
$ ss -tan | awk 'NR>1 {print $1}' | sort | uniq -c
   1840 ESTAB
     12 LISTEN
      3 SYN-SENT
   9120 TIME-WAIT
    410 CLOSE-WAIT
```

This one-liner counts sockets by state, and the counts tell a story:

| Observation | Likely meaning |
|---|---|
| Many `SYN-SENT` | outgoing connections are not being answered: a firewall or a dead destination |
| Many `CLOSE-WAIT`, growing | the peer closed, and your application never closes its end: a connection leak in your code |
| Very many `TIME-WAIT` | a high rate of short-lived connections; a sign that connections are not being reused, and a risk of running out of ephemeral ports |
| Many `ESTAB` to one destination, near the pool's maximum | connection pool saturation |
| Non-zero `Send-Q` on established sockets | data is queued but not acknowledged: a slow or stalled peer or path |

Related commands: `ss -tanp | grep :5432` to see who is connected to a port; `ss -s` for totals; `ss -ti` for per-connection TCP details (RTT, congestion window, retransmission counts); `nstat` or `netstat -s` for system-wide counters such as "SYNs to LISTEN sockets dropped", which increases when a backlog overflows.

```python-run
from collections import Counter

# A simplified listing: (state, local address:port, peer address:port)
sockets = (
    [("ESTAB", "10.0.0.5:443", f"198.51.100.{i % 250}:{40000 + i}") for i in range(300)]
    + [("TIME-WAIT", f"10.0.0.5:{32768 + i}", "10.0.2.9:6379") for i in range(27000)]
    + [("CLOSE-WAIT", f"10.0.0.5:{61000 - i}", "10.0.3.3:8080") for i in range(40)]
    + [("ESTAB", f"10.0.0.5:{50000 + i}", "10.0.1.7:5432") for i in range(20)]
)

by_state = Counter(state for state, local, peer in sockets)
print("sockets by state:", dict(by_state))

# Which remote endpoint is responsible for the TIME-WAIT pile?
time_wait_peers = Counter(peer for state, local, peer in sockets if state == "TIME-WAIT")
peer, count = time_wait_peers.most_common(1)[0]
EPHEMERAL_PORTS = 60999 - 32768 + 1
print(f"{count} TIME-WAIT sockets toward {peer}: {count / EPHEMERAL_PORTS:.0%} of the ephemeral port range")
print("diagnosis: a new connection is opened to", peer, "for every operation; use a connection pool")

leaks = Counter(peer for state, local, peer in sockets if state == "CLOSE-WAIT")
print("CLOSE-WAIT by peer:", dict(leaks), "-> the code calling that service does not close its connections")
```

The numbers point at two separate bugs: connections to the cache at `10.0.2.9:6379` are never reused (96% of the ephemeral ports are tied up in TIME_WAIT, so new connections are about to fail with "cannot assign requested address"), and the client code for `10.0.3.3:8080` leaks sockets.

## Part 3: A field guide to outage patterns

Each entry gives the signature, the mechanism and the lasting remedy.

### 1. The certificate expired

- **Signature:** every client fails at the same instant with a TLS error; the server and network are healthy; nothing was deployed.
- **Mechanism:** certificates have an end date, and a renewal was missed.
- **Evidence:** `curl -v` shows "certificate has expired".
- **Remedy:** automated renewal, and an alert weeks before expiry on every certificate, including internal ones.

### 2. DNS: the change that did not arrive, or the name that vanished

- **Signature:** partial and location-dependent; some users reach the old system, some the new, some nothing. Or a whole domain stops resolving.
- **Mechanism:** cached records with long TTLs after a change; a deleted or mistyped record; an expired domain registration; a failing DNS provider.
- **Evidence:** `dig` against the authoritative server and public resolvers disagree, or return `NXDOMAIN` or `SERVFAIL`.
- **Remedy:** lower TTLs before changes; keep old endpoints alive during the overlap; monitor resolution from outside; renew domains automatically.

### 3. Idle timeout mismatch

- **Signature:** intermittent resets or hangs, typically on the first request after a quiet period; retries succeed.
- **Mechanism:** a load balancer, NAT or firewall discards idle connection state while the client's pool still believes the connection is alive.
- **Evidence:** a capture shows the request sent on an old connection answered by an RST, or by nothing.
- **Remedy:** client idle timeout shorter than every timeout on the path; keep-alives; backend keep-alive timeout longer than the proxy's.

### 4. Ephemeral port exhaustion

- **Signature:** outgoing connections fail with "cannot assign requested address" under load; inbound traffic is unaffected.
- **Mechanism:** a new connection per request to one destination; closed connections hold their port in TIME_WAIT; the roughly 28,000 ports for that destination run out. A NAT gateway can exhaust its ports in the same way for a whole fleet.
- **Evidence:** tens of thousands of `TIME-WAIT` sockets toward one address.
- **Remedy:** connection pooling and keep-alive.

### 5. Connection pool exhaustion

- **Signature:** requests time out waiting for a connection; the service's CPU is idle; the database reports either few busy connections or "too many connections".
- **Mechanism:** a slow query or dependency holds connections longer; or code leaks them; or many instances together exceed the database's limit.
- **Evidence:** pool metrics at maximum with waiters; `CLOSE-WAIT` growth for leaks.
- **Remedy:** acquire timeouts, leak detection, sizing the total against the database's capacity.

### 6. One slow dependency takes everything down

- **Signature:** a non-essential feature becomes slow, then the whole service stops answering.
- **Mechanism:** calls without timeouts pile up; every worker thread ends up waiting on the slow dependency; none is left for healthy requests.
- **Evidence:** thread dumps or traces showing all workers blocked in the same call.
- **Remedy:** timeouts everywhere, circuit breakers, bulkheads, degraded fallbacks.

### 7. Retry storm

- **Signature:** a brief failure turns into a long outage; traffic to the affected service is several times normal; it recovers only when traffic is cut.
- **Mechanism:** clients and intermediate layers all retry, multiplying load on something already overloaded.
- **Evidence:** request rate rising as success rate falls.
- **Remedy:** backoff with jitter, retry budgets, retries at one layer only, load shedding.

### 8. Thundering herd on a cold cache

- **Signature:** a spike of database or origin load at a regular interval, or immediately after a deployment, purge or restart.
- **Mechanism:** a popular cached item expires, or the cache is emptied, and every request recomputes it at once.
- **Remedy:** request collapsing (one recomputation, the others wait), serving stale while refreshing, randomised expiry times, warming caches before taking traffic.

### 9. Health checks eject everything

- **Signature:** the load balancer reports zero healthy backends and returns `503`, although the backends are running.
- **Mechanism:** the health check depends on a shared component that hiccuped, or is too slow under load, so all instances fail together.
- **Remedy:** health checks that test the instance itself; fail-open thresholds; separate liveness from readiness.

### 10. The MTU black hole

- **Signature:** connections open and small requests work; large uploads or responses hang for ever. Often appears after introducing a VPN, tunnel or overlay network.
- **Mechanism:** the path's MTU is below 1500 and the ICMP "fragmentation needed" messages are being filtered, so the sender never learns to send smaller packets.
- **Evidence:** a capture shows full-sized segments retransmitted without acknowledgement; `ping -M do -s 1472 host` fails while a smaller size succeeds.
- **Remedy:** allow that ICMP type; or lower the MTU or clamp the TCP MSS on the tunnel.

### 11. The firewall or security rule change

- **Signature:** a clean, total failure between two specific groups of machines, starting at a precise moment; connections time out.
- **Mechanism:** a rule or route change blocks the port; or return traffic takes a different path through a stateful firewall that never saw the opening SYN and drops it (**asymmetric routing**).
- **Evidence:** SYNs retransmitted with no reply; the start time matches a change record.
- **Remedy:** review and stage network changes; test connectivity automatically after each.

### 12. A bad configuration pushed everywhere at once

- **Signature:** a sudden failure across all regions simultaneously.
- **Mechanism:** a configuration change (routing, DNS, load balancer, feature flag) deployed globally in one step. Several of the largest Internet outages on record were BGP or DNS configuration errors of this kind.
- **Remedy:** staged rollouts, automatic rollback, and keeping the tools needed for recovery independent of the system being recovered.

### A quick lookup

| Symptom | First suspects |
|---|---|
| Fails for everyone at one instant, no deployment | certificate expiry; domain or DNS |
| Fails for some users or regions only | DNS caching; one bad load-balancer node; routing |
| First request after idle fails, retry works | idle timeout mismatch; stale pooled connection |
| Small requests fine, large ones hang | MTU |
| Timeouts while CPU is idle | pool exhaustion; blocked threads on a slow dependency |
| "Cannot assign requested address" | ephemeral port exhaustion |
| Load rises as success falls | retry storm |
| Periodic load spikes | cache expiry stampede; synchronised timers |
| `502` during deployments | no connection draining |
| `503` with running backends | health check design |
| Exactly at midnight, or N days after something | scheduled jobs; expiry of certificates, tokens, licences |

> [!INTERVIEW]
> **"Requests from our service to an internal API intermittently fail with 'connection reset', mostly after quiet periods. What is going on?"** Suspect an idle timeout mismatch. The HTTP client keeps pooled connections open; a load balancer, NAT or firewall between the two drops state for connections idle longer than its timeout without telling either side; the next request reuses a dead connection and receives a reset. Confirm by correlating failures with idle time and with a packet capture showing the request on an old connection answered by RST. Fix by setting the client's idle timeout below the smallest timeout on the path, enabling keep-alives, validating connections before reuse, and making sure the backend's keep-alive timeout exceeds the proxy's. Retries on idempotent requests cover what remains.

> [!TIP]
> In any incident, ask two questions before touching a tool: "what changed?" and "what ran out?". Most outages follow a change (a deployment, a configuration push, a certificate or token reaching its end date), and most of the rest are a finite resource being exhausted (connections, ports, threads, memory, a rate limit).

## Learning from incidents

After an outage, good teams write a **postmortem**: a factual account of the timeline, the impact, the chain of causes, what made detection or recovery slow, and concrete follow-up actions. It is written without blame, because people who fear punishment hide the details that would prevent the next incident. The patterns in this lesson are, in effect, the distilled postmortems of many organisations. Reading public postmortems from large providers is one of the fastest ways to build the instinct this lesson is about.

## Pitfalls

- **Capturing without a filter** on a busy host.
- **Assuming the capture shows the whole truth.** It shows one vantage point; compare both ends.
- **Reading absolute sequence numbers** when relative ones make the arithmetic plain.
- **Ignoring where a service is bound.** `127.0.0.1` is not reachable from other machines.
- **Treating `TIME-WAIT` as the bug.** It is a symptom of not reusing connections.
- **Fixing the symptom only.** Restarting clears a leak or a stuck pool for an hour; find what is leaking.
- **Not checking recent changes first.**
- **Forgetting that captures hold sensitive data.**

## Summary

- A packet capture records what was really sent. `tcpdump` captures with a filter; Wireshark analyses.
- tcpdump lines show time, endpoints, flags (`[S]`, `[S.]`, `[.]`, `[P.]`, `[F.]`, `[R]`), relative sequence and acknowledgement numbers, window and length.
- Signatures: repeated SYNs with no reply (dropped), SYN answered by RST (nothing listening), repeated sequence ranges with duplicate ACKs (loss), `win 0` (slow receiver), unexpected RST (aborted or forgotten connection).
- `ss -tlnp` shows listening sockets and their bind addresses; counts of sockets by state reveal leaks (`CLOSE-WAIT`), connection churn (`TIME-WAIT`) and unanswered connects (`SYN-SENT`).
- Outages follow recurring patterns: expired certificates, DNS, idle timeout mismatches, port and pool exhaustion, slow dependencies, retry storms, cache stampedes, health-check cascades, MTU black holes, rule changes and global configuration pushes.
- Ask what changed and what ran out.

## Glossary

- **Packet capture**: a recording of packets seen on an interface.
- **tcpdump / Wireshark**: the command-line capture tool / the graphical protocol analyser.
- **pcap**: the standard capture file format.
- **Capture filter / display filter**: a rule selecting what to record / what to show.
- **Relative sequence number**: a sequence number counted from the start of the connection.
- **Retransmission**: a segment sent again because it was not acknowledged.
- **Duplicate ACK**: a repeated acknowledgement indicating a gap.
- **Zero window**: an advertisement that the receive buffer is full.
- **`ss` / `netstat`**: tools that list sockets and their states.
- **Bind address**: the local address a server listens on.
- **Loopback**: the interface (`127.0.0.1`, `::1`) reachable only from the same machine.
- **Accept queue / backlog**: established connections waiting for the application.
- **Ephemeral port exhaustion**: running out of client-side ports for new connections.
- **Connection leak**: connections opened and never closed.
- **MTU black hole**: silent loss of large packets when path MTU discovery is broken.
- **Asymmetric routing**: forward and return traffic taking different paths.
- **Cache stampede (thundering herd)**: many simultaneous recomputations after a cache miss.
- **Request collapsing**: letting one request recompute a value while others wait for it.
- **Postmortem**: a blameless written analysis of an incident.

## Check yourself

```quiz
[
  {"q": "In tcpdump output, what does 'Flags [S.]' indicate?",
   "options": ["A SYN with no acknowledgement", "A SYN-ACK, the second step of the handshake", "A FIN", "A reset"], "answer": 1,
   "explain": "S is SYN and the dot stands for ACK, so [S.] is the server's SYN+ACK reply."},
  {"q": "A capture shows the same SYN sent at 0 s, 1 s, 3 s and 7 s with no reply. What does this mean?",
   "options": ["The port is closed and the host refused", "The SYN or its reply is being dropped: a firewall, wrong address or dead host", "The connection is established", "TLS failed"], "answer": 1,
   "explain": "A refusal would be an immediate RST. Silence followed by retries with doubling gaps is a timeout caused by dropped packets."},
  {"q": "A line reads 'Flags [P.], seq 1:79, ack 1, length 78'. Which bytes does the segment carry?",
   "options": ["Bytes 1 to 79 inclusive", "Bytes 1 to 78 inclusive", "Byte 79 only", "No data"], "answer": 1,
   "explain": "The notation first:last is half-open: it starts at 1 and stops before 79, which is 78 bytes."},
  {"q": "A receiver repeatedly advertises 'win 0'. Where is the bottleneck?",
   "options": ["In the network path", "In the receiving application, which is not reading its buffer", "In DNS", "In the sender's congestion window"], "answer": 1,
   "explain": "A zero window means the receive buffer is full. The sender is being held back by flow control, not by the network."},
  {"q": "ss shows a database listening on 127.0.0.1:5432. A client on another machine gets 'connection refused'. Why?",
   "options": ["The firewall drops the packets", "The service only accepts connections from the same machine because it is bound to loopback", "The port number is wrong", "TIME_WAIT is too long"], "answer": 1,
   "explain": "A socket bound to 127.0.0.1 is not reachable through other interfaces. It must listen on 0.0.0.0 or a specific external address."},
  {"q": "A server has thousands of sockets in CLOSE-WAIT and the number keeps growing. What is the cause?",
   "options": ["A SYN flood", "The application is not closing connections after the peer has closed them", "The NAT gateway ran out of ports", "A DNS cache problem"], "answer": 1,
   "explain": "CLOSE-WAIT means the peer's FIN was received and the local program has not called close: a leak in the application."},
  {"q": "Small API calls through a new VPN succeed, but file uploads hang indefinitely. What should you suspect first?",
   "options": ["A retry storm", "An MTU black hole: large packets are dropped and the ICMP message reporting it is filtered", "An expired certificate", "Pool exhaustion"], "answer": 1,
   "explain": "The tunnel lowers the usable MTU. Small packets fit; full-sized ones vanish, and without the ICMP feedback the sender never adapts."},
  {"q": "All clients worldwide start failing with TLS errors at exactly 00:00 UTC, with no deployment. What is the most likely cause?",
   "options": ["A BGP route leak", "The certificate reached its expiry time", "Ephemeral port exhaustion", "A slow database query"], "answer": 1,
   "explain": "A simultaneous, global TLS failure at a round timestamp is the signature of a certificate's validity period ending."}
]
```

> **Source:** written from general operations knowledge (packet analysis and incident patterns are outside the chapters of Grigorik, *High Performance Browser Networking*, https://hpbn.co). Facts checked against the tcpdump manual page (https://www.tcpdump.org/manpages/tcpdump.1.html), the Wireshark User's Guide on display filters and TCP analysis (https://www.wireshark.org/docs/wsug_html_chunked/), the Linux `ss(8)` manual page (https://man7.org/linux/man-pages/man8/ss.8.html) and RFC 9293 (TCP states).
