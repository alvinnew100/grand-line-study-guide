# Latency and bandwidth: the two numbers behind "slow"

> **Before this lesson:** you should know what a packet and a router are, from [Layers and encapsulation](#/lesson/networking/layers-encapsulation). Basic arithmetic and reading short Python programs are enough for the rest.

## In plain words

When someone says "the network is slow", they could mean two very different things.

Picture a motorway between two cities. **Latency** is how long one car takes to drive from one end to the other. **Bandwidth** is how many lanes the motorway has, which decides how many cars can arrive per minute. Adding lanes does not make a single car arrive sooner: the cities are still the same distance apart. And a short road with one lane delivers the first car quickly but cannot move a whole stadium's worth of traffic.

In network terms:

- **Latency** (also called **delay**) is the time a piece of data takes to travel from sender to receiver. It is measured in milliseconds, written ms; one millisecond is a thousandth of a second.
- **Bandwidth** is the maximum amount of data a link can carry per second. It is measured in bits per second.

Why this matters for a job: performance work is mostly about finding which of these two is the limit. Engineers who buy more bandwidth to fix a latency problem waste money, and the page stays slow. Interviewers ask about this distinction constantly, and it underlies every later lesson on TCP, HTTP and content delivery networks.

## Units first: bits, bytes and the factor of eight

Network speeds are quoted in **bits** per second; file sizes are quoted in **bytes**. A byte is 8 bits. Mixing them up produces answers that are wrong by a factor of eight, so settle it now.

| Written | Meaning | Value |
|---|---|---|
| kbps | kilobits per second | 1,000 bits/s |
| Mbps | megabits per second | 1,000,000 bits/s |
| Gbps | gigabits per second | 1,000,000,000 bits/s |
| MB | megabyte (file size) | 1,000,000 bytes = 8,000,000 bits |

Smallest example: how long does a 5 MB photo take on a 40 Mbps connection, ignoring everything else? Convert the file to bits: 5 MB × 8 = 40 megabits. Divide by the rate: 40 megabits ÷ 40 Mbps = 1 second. A "40 megabit" line moves 5 megabytes per second, not 40.

## Where latency comes from: four delays

A packet's journey has several stops, and time is spent in four distinct ways at each one. Learn the four names; they are a standard interview answer.

### 1. Propagation delay

**Propagation delay** is the time the signal needs to physically travel the distance. Signals are fast but not infinitely fast. Light in a vacuum covers about 300,000 km per second. Inside an optical fibre (a thin strand of glass carrying pulses of light) it is slower, roughly **200,000 km per second**, because glass slows light down.

$$\text{propagation delay} = \frac{\text{distance}}{\text{signal speed}}$$

Example: a server is 6,000 km of fibre away. One way takes 6,000 ÷ 200,000 = 0.03 s = 30 ms. A question and its answer need a trip there and back, so 60 ms pass before the first byte of a reply can possibly arrive. No amount of money spent on bandwidth changes this. Only moving the two ends closer does.

### 2. Transmission delay

**Transmission delay** is the time needed to push all the bits of a packet onto the link. It depends on the packet's size and the link's rate, not on distance.

$$\text{transmission delay} = \frac{\text{packet size in bits}}{\text{link rate in bits per second}}$$

Example: a full 1,500-byte packet is 12,000 bits. On a 1 Mbps link that takes 12 ms; on a 100 Mbps link, 0.12 ms. This is the delay that more bandwidth *does* reduce.

A way to keep the two apart: propagation is how long the front of the train takes to reach the next station; transmission is how long the whole train takes to pass a point.

### 3. Processing delay

**Processing delay** is the time a router or computer spends examining the packet: checking it for errors, reading the destination address, deciding where it goes next. On modern equipment this is usually a few microseconds (millionths of a second) per device, small enough to ignore unless a device is doing heavy work such as encryption or deep inspection.

### 4. Queuing delay

**Queuing delay** is time spent waiting in line. When packets arrive at a router faster than its outgoing link can send them, they wait in a memory area called a **buffer**. If the buffer is full, new packets are thrown away, which is called **packet loss**.

Queuing delay is the unpredictable one. On an idle network it is zero. On a congested one it can be hundreds of milliseconds. It is why the same connection feels fine at 10 in the morning and awful at 8 in the evening.

The total one-way latency is the sum of all four over every hop on the path:

$$d_{\text{total}} = \sum_{\text{hops}} \left( d_{\text{prop}} + d_{\text{trans}} + d_{\text{proc}} + d_{\text{queue}} \right)$$

```mermaid
flowchart LR
  A[Sender] -->|transmission then propagation| R1[Router 1]
  R1 -->|processing then queue then transmission then propagation| R2[Router 2]
  R2 -->|processing then queue then transmission then propagation| B[Receiver]
```

## Round-trip time

Most network conversations are question and answer, so the number people measure is the **round-trip time**, written **RTT**: the time from sending a small message to receiving its reply. It is the latency there plus the latency back (the two directions can differ) plus any time the far side takes to respond.

The `ping` tool measures exactly this. Typical figures to carry in your head:

| Path | Typical RTT |
|---|---|
| Two machines in one data centre | under 1 ms |
| Same city | 5–20 ms |
| Across a continent | 40–80 ms |
| Between continents | 100–250 ms |
| Via a geostationary satellite | 500–700 ms |

Real paths are longer than the straight-line distance because cables follow coastlines, roads and railway lines, and because traffic passes through exchange points that may not be on the direct route. A useful rule: measured RTT is often 1.5 to 2 times the theoretical minimum.

> [!INTERVIEW]
> **"Estimate the minimum RTT between London and Tokyo."** Great-circle distance is about 9,600 km. In fibre, one way is 9,600 ÷ 200,000 = 48 ms, so the round trip is at least 96 ms. Real cable routes are far longer, so 200 ms or more is what you would measure. The interviewer wants the method: distance, speed of light in fibre, double it, then admit reality is worse.

## Bandwidth, throughput and the bottleneck

Three words that sound alike:

- **Bandwidth** (or **capacity**): the maximum rate a link can carry.
- **Throughput**: the rate you are actually achieving right now.
- **Bottleneck**: the slowest link on the path. End-to-end throughput can never exceed it.

If your home line is 500 Mbps but the server's upload is limited to 20 Mbps, you get at most 20 Mbps. If your laptop is on weak Wi-Fi that manages 8 Mbps, you get 8. Throughput is the minimum over the whole chain, and it is further reduced by other traffic sharing the links, by packet loss, and by the way TCP cautiously probes for capacity (the subject of the TCP lessons).

The part of the path between a home or phone and its Internet provider is called the **last mile**. It is usually the bottleneck for bandwidth and adds a surprising share of the latency too, often 10 to 40 ms on cable, DSL or mobile connections.

## Which one limits a web page?

Here is the result that changes how people think. Loading a web page is not one big download. It is dozens of small exchanges, each needing several round trips before any data flows: a name lookup, opening a connection, setting up encryption, then request and response.

Take a small 30 kB resource (30,000 bytes = 240,000 bits) fetched over a brand-new encrypted connection that needs 4 round trips in total before the response is complete.

| Connection | RTT | Round-trip waiting (4 × RTT) | Transfer time (size ÷ rate) | Total |
|---|---|---|---|---|
| 5 Mbps, 100 ms | 100 ms | 400 ms | 48 ms | 448 ms |
| 50 Mbps, 100 ms | 100 ms | 400 ms | 4.8 ms | 405 ms |
| 5 Mbps, 20 ms | 20 ms | 80 ms | 48 ms | 128 ms |

Multiplying bandwidth by ten saved 43 ms. Dividing latency by five saved 320 ms. For small transfers, waiting for round trips dominates, so **latency is the limit**. For one large transfer such as a 4 GB film, transfer time dominates and **bandwidth is the limit**.

This is the central observation of web performance, and it explains most of the techniques later in this track: reuse connections to avoid repeated setup, cut the number of round trips, and move content physically closer to users with a **CDN** (content delivery network: a fleet of servers spread around the world that hold copies of your files).

### Try it: a small page-load model

The model below estimates fetch time as round trips multiplied by RTT, plus size divided by bandwidth. It is rough, but good enough to build intuition. Read the comments, run it, then change the numbers.

```python-run
def fetch_ms(size_bytes, rtt_ms, mbps, round_trips):
    """Estimated time to fetch one resource, in milliseconds."""
    waiting = round_trips * rtt_ms                 # time spent on back-and-forth
    bits = size_bytes * 8                          # bytes -> bits
    transfer = bits / (mbps * 1_000_000) * 1000    # seconds -> milliseconds
    return waiting + transfer

small = 30_000          # a 30 kB script
large = 200_000_000     # a 200 MB video file

print("resource   bandwidth  RTT    time")
for name, size in (("30 kB", small), ("200 MB", large)):
    for mbps in (5, 50, 500):
        for rtt in (20, 100):
            t = fetch_ms(size, rtt, mbps, round_trips=4)
            print(f"{name:8}  {mbps:4} Mbps  {rtt:3} ms  {t:12,.0f} ms")
    print()

# Which improvement helps the small file more?
base = fetch_ms(small, 100, 5, 4)
print("10x bandwidth saves", round(base - fetch_ms(small, 100, 50, 4)), "ms")
print("5x lower latency saves", round(base - fetch_ms(small, 20, 5, 4)), "ms")
```

In the output, look down the 30 kB rows: the time barely moves as bandwidth goes from 5 to 500 Mbps, but drops sharply when RTT falls. Then look at the 200 MB rows: the opposite holds, RTT is irrelevant and bandwidth is everything.

## What humans notice

Delay matters because people feel it. Commonly used thresholds:

| Delay | How it feels |
|---|---|
| under 100 ms | instant |
| 100–300 ms | a slight but noticeable lag |
| 300–1000 ms | "the machine is working" |
| over 1 s | attention starts to wander |
| over 10 s | the task is abandoned |

A budget of a few hundred milliseconds disappears quickly once you subtract name lookup, connection setup and server time. On a 150 ms RTT mobile connection, setup alone can consume the whole budget before the first byte of content. That is why "reduce round trips" appears in every performance guide.

## Jitter, loss and the tail

Average latency hides the experiences that hurt most.

- **Jitter** is the variation in latency from one packet to the next. A video call tolerates a steady 80 ms far better than a delay that swings between 20 ms and 200 ms, because audio must be played at an even pace.
- **Packet loss** forces retransmission, which adds at least one extra round trip for the affected data.
- **Tail latency** is the latency of the slowest requests. It is described with **percentiles**: the 50th percentile (written p50, also called the median) is the value half of requests are faster than; p99 is the value 99% of requests are faster than.

Why engineers obsess over p99: suppose one page view makes 50 requests to backend services, and each has a 1% chance of being slow. The chance that at least one is slow is $1 - 0.99^{50} \approx 39\%$. A problem that touches 1% of requests touches more than a third of users.

```python-run
# Probability that a page needing n backend calls hits at least one slow call,
# when each call independently is slow with probability p.
def chance_of_slow_page(n, p):
    return 1 - (1 - p) ** n     # 1 minus "all n calls were fast"

for n in (1, 10, 50, 100):
    print(f"{n:3} calls, 1% slow each -> {chance_of_slow_page(n, 0.01):5.1%} of pages are slow")

# Percentiles from raw samples: sort, then index.
samples = [12, 14, 13, 15, 11, 240, 13, 12, 16, 14, 13, 12, 15, 900, 13, 14, 12, 13, 15, 14]
samples.sort()
def percentile(sorted_values, q):
    index = min(len(sorted_values) - 1, int(q / 100 * len(sorted_values)))
    return sorted_values[index]
print("mean:", sum(samples) / len(samples), "ms")
print("p50 :", percentile(samples, 50), "ms")
print("p95 :", percentile(samples, 95), "ms")
```

The mean here is about 69 ms, a number no real request experienced: most took around 13 ms and two took far longer. Report percentiles, not averages.

## Bufferbloat: when big buffers make things worse

It seems sensible to give routers large buffers so they rarely drop packets. In practice, oversized buffers on home routers and modems fill up during a large upload or download and every packet then waits behind a long queue. Latency climbs from 20 ms to over a second while the link is busy. This is called **bufferbloat**. The symptom is familiar: a video call falls apart the moment someone else in the house starts a big upload. The cure is smarter queue management in the router, which drops or marks packets early so that senders slow down before the queue grows.

The lesson for engineers: packet loss is not purely bad. It is the signal TCP uses to learn that it is sending too fast. Hiding it behind a huge buffer trades a small loss for a large delay.

## Worked example: budgeting a request

A user in Cape Town opens a page hosted in Frankfurt. Measured RTT is 180 ms. The first request needs:

1. A name lookup (DNS): 1 round trip to a nearby resolver, say 20 ms.
2. Opening a TCP connection: 1 RTT = 180 ms.
3. Setting up encryption with a modern TLS version: 1 RTT = 180 ms.
4. Sending the request and receiving the first bytes: 1 RTT = 180 ms, plus server time of 50 ms.

Total before the first byte of the page: 20 + 180 + 180 + 180 + 50 = **610 ms**. Now put a CDN server in Johannesburg with a 25 ms RTT and the content cached there: 20 + 25 + 25 + 25 + 5 = **100 ms**. Same bandwidth, six times faster, purely by shortening the distance.

> [!TIP]
> When asked to speed something up, first ask "how many round trips does it take, and how long is each?". Count them on paper. That habit separates engineers who guess from engineers who know.

## Pitfalls

- **Confusing bits and bytes.** A 100 Mbps line downloads about 12.5 MB per second.
- **Assuming more bandwidth fixes a slow page.** Beyond a few Mbps, page load time barely improves; latency keeps mattering.
- **Quoting the theoretical propagation delay as the real RTT.** Real routes are longer and include queuing and last-mile delay.
- **Reporting averages.** One 5-second request among a hundred fast ones barely moves the mean and ruins a user's day.
- **Forgetting the two directions differ.** Home connections usually upload far slower than they download, and the reply path may be a different route.
- **Treating loss as the only congestion signal.** With bufferbloat, latency rises long before anything is dropped.

## Summary

- Latency is time per trip; bandwidth is volume per second. They are independent.
- Latency has four parts: propagation (distance), transmission (size ÷ rate), processing, and queuing.
- Light in fibre covers about 200,000 km per second; that sets a hard floor on RTT.
- Throughput is capped by the bottleneck link; the last mile is often the weak point.
- Small transfers are limited by round trips, large ones by bandwidth. Web pages are many small transfers.
- Measure with percentiles; the tail (p95, p99) is what users remember.

## Glossary

- **Latency / delay**: time for data to travel from sender to receiver.
- **RTT (round-trip time)**: time for a message to go out and its reply to come back.
- **Bandwidth / capacity**: the maximum data rate of a link, in bits per second.
- **Throughput**: the data rate actually achieved.
- **Bottleneck**: the slowest link on a path.
- **Propagation / transmission / processing / queuing delay**: the four components of latency.
- **Buffer**: memory in a router where packets wait for the outgoing link.
- **Packet loss**: a packet that never arrives, often because a buffer was full.
- **Jitter**: variation in latency between packets.
- **Percentile (p50, p99)**: the value below which that percentage of measurements fall.
- **Last mile**: the link between an end user and their provider.
- **CDN**: servers placed near users that hold copies of content.
- **Bufferbloat**: high latency caused by oversized, full buffers.

## Check yourself

```quiz
[
  {"q": "A 25 MB file is downloaded over a 100 Mbps link. Ignoring latency, about how long does the transfer take?",
   "options": ["0.25 seconds", "2 seconds", "4 seconds", "25 seconds"], "answer": 1,
   "explain": "25 MB is 200 megabits (multiply by 8). 200 megabits divided by 100 megabits per second is 2 seconds."},
  {"q": "Which delay component is determined only by the distance and the signal speed?",
   "options": ["Transmission delay", "Queuing delay", "Propagation delay", "Processing delay"], "answer": 2,
   "explain": "Propagation delay is distance divided by signal speed. It does not depend on packet size or link rate."},
  {"q": "A server is 4,000 km of fibre away. What is the smallest possible round-trip time?",
   "options": ["About 13 ms", "About 20 ms", "About 40 ms", "About 80 ms"], "answer": 2,
   "explain": "One way is 4,000 / 200,000 = 0.02 s = 20 ms. A round trip doubles it to 40 ms. Real measurements will be higher."},
  {"q": "A page consists of many 20 kB resources. Which change is likely to help most on a 200 ms RTT connection?",
   "options": ["Upgrading from 50 Mbps to 500 Mbps", "Serving the resources from a location with 30 ms RTT", "Using larger router buffers", "Increasing the Ethernet MTU"], "answer": 1,
   "explain": "Small resources are dominated by round-trip waiting, not transfer time. Cutting RTT shortens every one of those round trips."},
  {"q": "Your path has links of 1 Gbps, 40 Mbps and 300 Mbps. What is the best throughput you can expect?",
   "options": ["1 Gbps", "About 447 Mbps (the average)", "300 Mbps", "40 Mbps"], "answer": 3,
   "explain": "End-to-end throughput is limited by the slowest link, the bottleneck."},
  {"q": "Each of 20 backend calls made for one page has a 2% chance of being slow. Roughly what share of pages see at least one slow call?",
   "options": ["2%", "About 10%", "About 33%", "About 67%"], "answer": 2,
   "explain": "1 - 0.98^20 is about 0.33. Fan-out multiplies the impact of tail latency, which is why p99 matters."},
  {"q": "A home video call stutters whenever a large upload runs, although no packets are lost. The most likely cause is:",
   "options": ["Propagation delay increased", "Bufferbloat: packets wait in an oversized full queue", "The MTU is too small", "The DNS server is slow"], "answer": 1,
   "explain": "A saturated link with a large buffer adds queuing delay to every packet. Distance, and therefore propagation delay, has not changed."}
]
```

> **Source:** Grigorik, *High Performance Browser Networking*, ch. 1 "Primer on Latency and Bandwidth" (topic coverage only; wording, examples and numbers are original), https://hpbn.co/primer-on-latency-and-bandwidth/ . Tail-latency arithmetic follows the idea in Dean and Barroso, "The Tail at Scale" (2013).
