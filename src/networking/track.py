TRACK = dict(
    id="networking",
    title="Computer Networking for Engineers",
    icon="🌐",
    color="#2a6fdb",
    group="Systems",
    blurb="From bits on a wire to HTTP/3: layers, IP and routing, TCP, DNS, TLS, wireless, HTTP, browser "
          "performance, real-time APIs and backend networking, explained from zero with runnable simulations, "
          "annotated tool output and interview-style problems.",
    sources=[
        "Grigorik, High Performance Browser Networking (https://hpbn.co)",
        "IETF RFCs 791, 1034/1035, 1071, 6298, 6455, 8446, 9000, 9110-9114, 9293",
        "MDN Web Docs (HTTP, Fetch, WebSocket, Performance APIs)",
    ],
    modules=[
        dict(
            id="foundations",
            title="1 · Foundations",
            summary="How networks are layered, why latency matters more than bandwidth, and the full journey of a web request.",
            lessons=[
                dict(id="layers-encapsulation", title="Layers and encapsulation: how networks are organised", file="01-layers-encapsulation.md"),
                dict(id="latency-bandwidth", title="Latency and bandwidth: the two numbers behind \"slow\"", file="02-latency-bandwidth.md"),
                dict(id="url-walkthrough", title="What happens when you type a URL and press Enter", file="03-url-walkthrough.md"),
            ],
            problems=["net-url-normalize"],
        ),
        dict(
            id="link-network",
            title="2 · Link and Network Layers",
            summary="Ethernet, MAC addresses and switching; IPv4 addressing, subnets and NAT; IPv6, ICMP, routing and BGP.",
            lessons=[
                dict(id="ethernet-arp-switching", title="Ethernet, MAC addresses, ARP and switching", file="04-ethernet-arp-switching.md"),
                dict(id="ipv4-subnets-nat", title="IPv4 addressing, subnets, CIDR and NAT", file="05-ipv4-subnets-nat.md"),
                dict(id="ipv6-icmp-routing", title="The IP packet, IPv6, ICMP, routing and BGP", file="06-ipv6-icmp-routing.md"),
            ],
            problems=[
                "net-ipv4-int", "net-cidr-contains", "net-subnet-info", "net-split-subnets",
                "net-longest-prefix-match", "net-internet-checksum", "net-mac-learning-switch", "net-nat-table",
            ],
        ),
        dict(
            id="transport",
            title="3 · Transport: UDP and TCP",
            summary="Ports and sockets, the TCP lifecycle, reliability, flow and congestion control, and TCP behaviour in production.",
            lessons=[
                dict(id="udp-tcp-lifecycle", title="UDP and the TCP connection lifecycle", file="07-udp-tcp-lifecycle.md"),
                dict(id="tcp-flow-congestion", title="Flow control and congestion control", file="08-tcp-flow-congestion.md"),
                dict(id="tcp-tuning", title="TCP in practice: head-of-line blocking, Nagle, keep-alive and tuning", file="09-tcp-tuning.md"),
            ],
            problems=[
                "net-tcp-handshake-validate", "net-sliding-window-sender", "net-gbn-vs-sr",
                "net-rto-estimator", "net-cwnd-evolution",
            ],
        ),
        dict(
            id="dns",
            title="4 · DNS in Depth",
            summary="The name hierarchy, recursive and iterative resolution, record types, caching and TTLs, anycast and failure modes.",
            lessons=[
                dict(id="dns-resolution", title="How DNS resolution works", file="10-dns-resolution.md"),
                dict(id="dns-caching-failures", title="DNS caching, TTLs, anycast and failures", file="11-dns-caching-failures.md"),
            ],
            problems=["net-dns-resolver"],
        ),
        dict(
            id="tls",
            title="5 · TLS",
            summary="Keys, certificates and chains of trust, the handshake, and the practical features around it: SNI, ALPN, resumption, HSTS and mutual TLS.",
            lessons=[
                dict(id="tls-handshake-certificates", title="TLS: the handshake, certificates and chains of trust", file="12-tls-handshake-certificates.md"),
                dict(id="tls-in-practice", title="TLS in practice: SNI, ALPN, resumption, HSTS, TLS 1.3 and mutual TLS", file="13-tls-in-practice.md"),
            ],
            problems=[],
        ),
        dict(
            id="wireless",
            title="6 · Wireless and Mobile Networks",
            summary="Why radio links are variable, how Wi-Fi shares the air, and how cellular radio states shape battery life and latency.",
            lessons=[
                dict(id="wifi", title="Wireless fundamentals and Wi-Fi", file="14-wifi.md"),
                dict(id="cellular", title="Mobile networks: radio states, battery and latency", file="15-cellular.md"),
            ],
            problems=[],
        ),
        dict(
            id="http",
            title="7 · HTTP",
            summary="From HTTP/0.9 to HTTP/3: messages, methods, caching, cookies, multiplexing, header compression and QUIC.",
            lessons=[
                dict(id="http1", title="From HTTP/0.9 to HTTP/1.1", file="16-http1.md"),
                dict(id="http-caching-cookies", title="HTTP caching, cookies and content negotiation", file="17-http-caching-cookies.md"),
                dict(id="http2", title="HTTP/2: streams, multiplexing and HPACK", file="18-http2.md"),
                dict(id="http3-quic", title="HTTP/3 and QUIC", file="19-http3-quic.md"),
            ],
            problems=[
                "net-http-parse", "net-chunked-decode", "net-cache-freshness", "net-cookie-match", "net-hpack-toy",
            ],
        ),
        dict(
            id="browser-performance",
            title="8 · Browser Networking and Performance",
            summary="Connection management, resource hints, the critical rendering path, measurement, CDNs, compression and caching strategy.",
            lessons=[
                dict(id="browser-connections-rendering", title="Browser networking: connections, resource hints and the critical rendering path", file="20-browser-connections-rendering.md"),
                dict(id="measuring-cdn-compression", title="Measuring performance, CDNs, compression and caching strategy", file="21-measuring-cdn-compression.md"),
            ],
            problems=[],
        ),
        dict(
            id="real-time",
            title="9 · Real-Time and Browser APIs",
            summary="fetch, polling, long polling, Server-Sent Events, WebSocket and WebRTC, and how to choose among them.",
            lessons=[
                dict(id="xhr-fetch-sse", title="XHR, fetch, polling, long polling and Server-Sent Events", file="22-xhr-fetch-sse.md"),
                dict(id="websocket-webrtc", title="WebSocket, WebRTC and choosing a transport", file="23-websocket-webrtc.md"),
            ],
            problems=["net-websocket-frame"],
        ),
        dict(
            id="backend-networking",
            title="10 · Networking for Backend and ML Engineers",
            summary="Load balancers and proxies, resilience patterns, gRPC and protobuf, service discovery, API gateways and VPCs.",
            lessons=[
                dict(id="load-balancers-proxies", title="Load balancers, reverse proxies and health checks", file="24-load-balancers-proxies.md"),
                dict(id="resilience-patterns", title="Timeouts, retries, pools, rate limits and idempotency", file="25-resilience-patterns.md"),
                dict(id="grpc-discovery-vpc", title="gRPC, service discovery, API gateways and virtual private clouds", file="26-grpc-discovery-vpc.md"),
            ],
            problems=[
                "net-lb-weighted-round-robin", "net-lb-least-connections", "net-consistent-hash",
                "net-token-bucket", "net-leaky-bucket", "net-backoff-jitter",
            ],
        ),
        dict(
            id="tools-debugging",
            title="11 · Tools and Debugging",
            summary="ping, traceroute, dig and curl; reading packet captures and socket tables; the recurring patterns behind outages.",
            lessons=[
                dict(id="cli-tools", title="Network debugging tools: ping, traceroute, dig and curl", file="27-cli-tools.md"),
                dict(id="packet-capture-outages", title="Packet captures, socket inspection and common outage patterns", file="28-packet-capture-outages.md"),
            ],
            problems=["net-traceroute-hops"],
        ),
        dict(
            id="interview",
            title="12 · Networking Interview Essentials",
            summary="The most common fundamentals questions with worked answers, then design and debugging scenarios with a method for each.",
            lessons=[
                dict(id="interview-fundamentals", title="Networking interview essentials I: fundamentals with worked answers", file="29-interview-fundamentals.md"),
                dict(id="interview-design-debugging", title="Networking interview essentials II: design and debugging scenarios", file="30-interview-design-debugging.md"),
            ],
            problems=[],
        ),
    ],
)
