TRACK = dict(
    id="os",
    title="Operating Systems (Tanenbaum)",
    icon="🧵",
    color="#0f8b8d",
    group="Systems",
    blurb="Processes, memory, files, I/O, deadlocks, virtualization, multiprocessors and security, "
          "with runnable simulations of every classic algorithm and two real-system case studies.",
    sources=["Tanenbaum & Bos, Modern Operating Systems, 4th ed., ch. 1–12"],
    modules=[
        dict(
            id="introduction",
            title="1 · Introduction",
            summary="What an operating system is, the hardware it tames, and the concepts and system calls it offers.",
            lessons=[
                dict(id="what-is-an-os", title="What an operating system is, its history and its many forms", file="01-what-is-an-os.md"),
                dict(id="hardware-review", title="Hardware review: CPUs, memory, devices and booting", file="02-hardware-review.md"),
                dict(id="concepts-syscalls-structure", title="Core concepts, system calls and kernel structure", file="03-concepts-syscalls-structure.md"),
            ],
            problems=[],
        ),
        dict(
            id="processes-threads",
            title="2 · Processes and Threads",
            summary="The process model, threads, races and mutual exclusion, semaphores to monitors, and CPU scheduling.",
            lessons=[
                dict(id="processes-threads", title="Processes and threads", file="04-processes-threads.md"),
                dict(id="races-mutual-exclusion", title="Race conditions and mutual exclusion", file="05-races-mutual-exclusion.md"),
                dict(id="semaphores-monitors-messages", title="Semaphores, monitors, message passing and the classic problems", file="06-semaphores-monitors-messages.md"),
                dict(id="scheduling", title="CPU scheduling", file="07-scheduling.md"),
            ],
            problems=[
                "os-semaphore-trace", "os-dining-philosophers", "os-readers-writers",
                "os-fcfs-scheduling", "os-sjf-scheduling", "os-srtf-scheduling",
                "os-round-robin", "os-priority-scheduling", "os-mlfq",
            ],
        ),
        dict(
            id="memory-management",
            title="3 · Memory Management",
            summary="Address spaces, swapping, paging, TLBs, page replacement and segmentation.",
            lessons=[
                dict(id="address-spaces-swapping", title="Address spaces, swapping and free-space management", file="08-address-spaces-swapping.md"),
                dict(id="paging-tlb", title="Virtual memory: paging, page tables and TLBs", file="09-paging-tlb.md"),
                dict(id="page-replacement", title="Page replacement algorithms", file="10-page-replacement.md"),
                dict(id="paging-design-segmentation", title="Paging design, implementation issues and segmentation", file="11-paging-design-segmentation.md"),
            ],
            problems=[
                "os-first-fit", "os-best-fit", "os-buddy-allocator",
                "os-two-level-translation", "os-tlb-simulation",
                "os-fifo-page-faults", "os-lru-page-faults", "os-optimal-page-faults",
                "os-clock-page-faults", "os-aging-page-replacement", "os-working-set-size",
            ],
        ),
        dict(
            id="file-systems",
            title="4 · File Systems",
            summary="Files and directories, on-disk layout, journaling, the VFS, and how file systems are kept fast and consistent.",
            lessons=[
                dict(id="files-directories", title="Files and directories", file="12-files-directories.md"),
                dict(id="fs-implementation", title="File-system implementation", file="13-fs-implementation.md"),
                dict(id="fs-management-examples", title="Management, optimisation and example file systems", file="14-fs-management-examples.md"),
            ],
            problems=[
                "os-fat-chain", "os-inode-max-file-size", "os-inode-block-lookup",
                "os-free-bitmap", "os-unix-permissions",
            ],
        ),
        dict(
            id="input-output",
            title="5 · Input/Output",
            summary="Device hardware, the layered I/O software stack, disks and RAID, clocks, terminals and power.",
            lessons=[
                dict(id="io-hardware-software", title="I/O hardware and the layers of I/O software", file="15-io-hardware-software.md"),
                dict(id="disks-raid", title="Disks, RAID and disk-arm scheduling", file="16-disks-raid.md"),
                dict(id="clocks-terminals-power", title="Clocks, user interfaces and power management", file="17-clocks-terminals-power.md"),
            ],
            problems=[
                "os-disk-fcfs", "os-disk-sstf", "os-disk-scan", "os-disk-cscan", "os-disk-look",
                "os-raid-parity",
            ],
        ),
        dict(
            id="deadlocks",
            title="6 · Deadlocks",
            summary="When processes wait for each other forever: modelling, detection, recovery, avoidance and prevention.",
            lessons=[
                dict(id="deadlock-detection", title="Deadlock: conditions, modelling, detection and recovery", file="18-deadlock-detection.md"),
                dict(id="deadlock-avoidance-prevention", title="Deadlock avoidance, the banker's algorithm and prevention", file="19-deadlock-avoidance-prevention.md"),
            ],
            problems=["os-deadlock-detection", "os-bankers-safe-sequence"],
        ),
        dict(
            id="virtualization-cloud",
            title="7 · Virtualization and the Cloud",
            summary="Hypervisors, how privileged instructions, memory and devices are virtualised, containers and clouds.",
            lessons=[
                dict(id="hypervisors", title="Hypervisors and CPU virtualization techniques", file="20-hypervisors.md"),
                dict(id="virt-memory-io-cloud", title="Memory and I/O virtualization, containers and clouds", file="21-virt-memory-io-cloud.md"),
            ],
            problems=[],
        ),
        dict(
            id="multiple-processors",
            title="8 · Multiple Processor Systems",
            summary="Shared-memory multiprocessors, message-passing multicomputers and distributed systems.",
            lessons=[
                dict(id="multiprocessors", title="Multiprocessors: hardware, synchronisation and scheduling", file="22-multiprocessors.md"),
                dict(id="multicomputers-distributed", title="Multicomputers and distributed systems", file="23-multicomputers-distributed.md"),
            ],
            problems=[],
        ),
        dict(
            id="security",
            title="9 · Security",
            summary="Threats, access control, formal models, cryptography, authentication, and how attacks and defences work conceptually.",
            lessons=[
                dict(id="security-access-control", title="Threat models, access control and formal models", file="24-security-access-control.md"),
                dict(id="crypto-authentication", title="Cryptography basics and authentication", file="25-crypto-authentication.md"),
                dict(id="attacks-defences", title="Classes of attack and the defences against them", file="26-attacks-defences.md"),
            ],
            problems=[],
        ),
        dict(
            id="case-linux",
            title="10 · Case Study: Linux",
            summary="How Linux (and Android on top of it) realises processes, scheduling, memory, I/O, files and security.",
            lessons=[
                dict(id="linux-processes", title="Linux: history, structure, processes and scheduling", file="27-linux-processes.md"),
                dict(id="linux-memory-io-fs", title="Linux: memory, I/O, file systems and security", file="28-linux-memory-io-fs.md"),
                dict(id="android", title="Android: runtime, Zygote, Binder, apps and their lifecycle", file="28a-android.md"),
            ],
            problems=[],
        ),
        dict(
            id="case-windows",
            title="11 · Case Study: Windows",
            summary="The NT architecture: executive, objects and handles, threads, memory manager, I/O stack, NTFS and security.",
            lessons=[
                dict(id="windows-structure-processes", title="Windows: structure, objects, processes and threads", file="29-windows-structure-processes.md"),
                dict(id="windows-memory-io-ntfs", title="Windows: memory, caching, I/O, NTFS and security", file="30-windows-memory-io-ntfs.md"),
            ],
            problems=[],
        ),
        dict(
            id="os-design",
            title="12 · Operating System Design",
            summary="Designing interfaces, choosing structures, tuning performance and managing the project — then the interview round-up.",
            lessons=[
                dict(id="design-interfaces-implementation", title="Design goals, interfaces and implementation", file="31-design-interfaces-implementation.md"),
                dict(id="design-performance-trends", title="Performance, project management and trends", file="32-design-performance-trends.md"),
                dict(id="interview-essentials", title="OS interview essentials", file="33-interview-essentials.md"),
            ],
            problems=[],
        ),
    ],
)
