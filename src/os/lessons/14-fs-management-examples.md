# Management, optimisation and example file systems

> **Before this lesson:** [File-system implementation](#/lesson/os/fs-implementation), for blocks, i-nodes, the file allocation table and journaling.

## In plain words

Building a file system that works is the first half of the job. The second half is keeping it working for years: on a disk that fills up, through crashes and failing hardware, with people who delete the wrong thing.

Think of the warehouse from the previous lesson, now in daily use. The manager must decide how big the shelves should be (big shelves waste space on small items; small shelves mean many trips for big ones), keep a list of which shelves are empty, make copies of the records in case of fire, check after any accident that the paperwork still matches what is actually on the shelves, and arrange things so that the workers walk as little as possible.

Each of those has a counterpart here: choosing the **block size**, tracking **free space**, making **backups**, running a **consistency check**, and using a **cache** to avoid slow trips to the disk. The lesson then looks at three real file systems to see the ideas in use.

Why it matters for a job: these are the practical concerns of anyone who runs systems or writes software that stores data. Questions such as "why did my file not survive the crash although the program had written it?" are answered here.

## Motivation

Making a file system *work* is one thing. Making it work well for years — on a disk that fills up, with users who delete the wrong file, through crashes and failing hardware — is another. This lesson covers the operational side: how space is accounted for, how data is backed up, how consistency is checked and repaired, and the handful of techniques that make file access fast. It then grounds everything in three real designs: the FAT family, the classic UNIX file system and the format used on optical discs.

## Disk-space management

### Choosing a block size

Files are stored in fixed-size blocks, so a size must be chosen, and the choice cuts both ways.

- **Large blocks waste space.** Every file wastes, on average, half a block at its end; a 1-byte file occupies a whole block. Since most files are small, large blocks leave a great deal of the disk as internal fragmentation.
- **Small blocks waste time.** A file spread over many small blocks needs many separate transfers, and on a mechanical disk each may involve a seek and a rotational delay.

Studies of real file populations consistently show the same shape: the *median* file is only a few kilobytes, but most of the *bytes* live in a small number of very large files. The simulation below draws file sizes from such a skewed distribution and measures both effects.

```python-run
import random

rng = random.Random(42)
# A skewed population: many tiny files, a few huge ones (sizes in bytes).
files = [int(rng.lognormvariate(8.5, 2.2)) + 1 for _ in range(20000)]
files.sort()
total = sum(files)
print(f"{len(files)} files, median {files[len(files) // 2]:,} B, mean {total // len(files):,} B, largest {files[-1]:,} B")
big = sum(files[-len(files) // 100:])
print(f"the largest 1% of files hold {big / total:.0%} of all bytes\n")

SEEK_MS, ROTATION_MS, TRACK_BYTES = 5.0, 8.33, 1_000_000
print("block    space efficiency   time to read one 64 KB file from scattered blocks")
for kb in (1, 2, 4, 8, 16, 64, 256):
    block = kb * 1024
    used = sum(-(-f // block) * block for f in files)        # round each file up to whole blocks
    blocks_needed = -(-65536 // block)
    per_block_ms = SEEK_MS + ROTATION_MS / 2 + block / TRACK_BYTES * ROTATION_MS
    print(f"{kb:4d} KB   {total / used:8.1%}          {blocks_needed * per_block_ms:8.1f} ms")
```

**What the code does.** The first lines invent 20,000 file sizes with a realistic shape — very many small files and a few enormous ones — using `lognormvariate`, a random-number generator with that kind of spread. The sizes are sorted so that the middle one (the median) and the largest 1% can be picked out. The loop then tries seven block sizes. For each, `used` is the total space taken when every file is rounded up to a whole number of blocks: `-(-f // block)` is a compact way to divide and round *up*. The time to read one 64-kilobyte file is estimated as the number of blocks it needs times the time per block (a head movement, half a rotation on average, and the transfer itself).

**The output.** The middle-sized file is under 5 kilobytes, yet the largest 1% of files hold about two-fifths of all the bytes. As the block size grows from 1 to 256 kilobytes, the share of the disk holding real data falls from 99% to under 20%, while the time to read the sample file falls from about 590 milliseconds to about 10.

Space efficiency falls as blocks grow, access time falls too, and the two curves cross somewhere in the low kilobytes. With disks now enormous, wasting some space is cheap, and 4 KB has become the common choice (larger on some systems).

### Keeping track of free blocks

Two methods are in wide use.

A **linked list of disk blocks**: each list block holds as many free block numbers as will fit, plus a pointer to the next list block. With 1 KB blocks and 32-bit block numbers, each list block holds 255 free numbers. The list is stored *in the free blocks themselves*, so it costs nothing extra. Only one block of pointers needs to be in memory at a time; when it runs dry, the next is read in. (A subtle refinement: keeping that in-memory block about half full avoids pathological behaviour where alternately creating and deleting a few temporary files causes a disk read or write of a list block every time.)

A **bitmap**: one bit per block. A disk of n blocks needs n bits, which is far more compact than a list of 32-bit numbers unless the disk is nearly full. A bitmap also makes it easy to find free blocks *near a given location*, which helps keep files contiguous.

```python-run
def free_list_blocks(free_blocks, block_bytes=1024, number_bytes=4):
    per_block = block_bytes // number_bytes - 1          # one slot is the "next" pointer
    return -(-free_blocks // per_block)

def bitmap_blocks(total_blocks, block_bytes=1024):
    return -(-total_blocks // (block_bytes * 8))

total = 500_000_000                                       # a 500 GB disk of 1 KB blocks
print(f"bitmap: always {bitmap_blocks(total):,} blocks")
for pct_free in (90, 50, 10, 1, 0.1):
    free = int(total * pct_free / 100)
    print(f"free list with {pct_free:>4}% of the disk free: {free_list_blocks(free):>9,} blocks")
```

**What the code does.** Two ways of recording free blocks are compared for a disk of 500 million blocks. `free_list_blocks` computes how many blocks are needed to hold a list of free block numbers: each list block holds 255 numbers (256 four-byte slots, one of which points to the next list block). `bitmap_blocks` computes the size of a bitmap with one bit per block: a 1-kilobyte block holds 8,192 bits. Both use the round-up trick `-(-a // b)`.

**The output.** The bitmap always needs 61,036 blocks. The list needs about 1.76 million blocks when 90% of the disk is free, and becomes smaller than the bitmap only when the disk is almost full (about 19,600 blocks at 1% free).

The free list is smaller only when the disk is almost full — and in that state it lives entirely in blocks nobody else can use anyway.

### Disk quotas

On multi-user systems the administrator can cap each user's files and blocks. When a user opens a file, the system locates that user's quota record and attaches it to the open-file table entry; every block added is charged against it. There is a **soft limit**, which may be exceeded temporarily and produces a warning at login, and a **hard limit**, which may not be exceeded at all. Ignore the warning too many times and the system refuses to let you log in until you clean up.

## Backups

Disks fail, and users delete things by mistake. Backups address both: recovery from disaster and recovery from stupidity. Several design issues arise.

- **What to back up.** Executable programs can be reinstalled; device files should never be dumped. Usually only specific directories are worth saving.
- **Incremental dumps.** Copying everything every night is wasteful. Do a full dump periodically (weekly, monthly) and each day save only files modified since the last dump. Recovery is then more complicated: restore the latest full dump, then each incremental in order.
- **Compression** saves space, but a single bad spot on the medium can ruin the decompression of everything after it.
- **Consistency of an active file system.** Files changing during the dump can leave the backup incoherent. Systems take a **snapshot** — an instantaneous frozen view, implemented by copying critical structures and requiring later changes to copy blocks rather than update them in place — and back that up at leisure.
- **Security.** A backup holds everything; the media must be protected as carefully as the live system, and stored off-site, or a fire destroys both.

Two strategies exist for the dump itself.

A **physical dump** starts at block 0 and copies every block in order. It is simple, very fast and hard to get wrong. But it cannot skip chosen directories, cannot do incremental dumps, and cannot restore individual files on request. (It should skip unused blocks, and must take care with blocks marked bad.)

A **logical dump** starts at specified directories and recursively dumps the files and directories that have changed since a given date. To make restoring possible, it also dumps *every directory on the path* to a changed file, changed or not — so that the file can be restored into the right place, with the right owners and permissions, even on a fresh file system. Logical dumps make it easy to restore one file, and are the most common form.

Restoring a logical dump has its own traps: the free-block list must be rebuilt from scratch; hard-linked files must be restored once, not once per name; and UNIX files with **holes** (a file that was written at byte 0 and at byte 1,000,000,000 occupies only a couple of blocks) must not be filled in with a gigabyte of zeros.

## File-system consistency

If the system crashes before all modified blocks reach the disk, the file system can be left inconsistent — especially if the unwritten blocks are i-nodes, directories or the free list. Utilities such as `fsck` (UNIX) and `chkdsk`/`sfc` (Windows) check and repair it.

### Block consistency

The checker builds two tables, each with a counter per block. The first counts how many times each block appears *in a file* (found by reading every i-node and following its pointers); the second counts how many times it appears *in the free list or bitmap*.

In a consistent file system every block has a 1 in exactly one table. The possible faults:

| In use | Free | Diagnosis | Repair |
|---|---|---|---|
| 1 | 0 | fine | — |
| 0 | 1 | fine | — |
| 0 | 0 | **missing block** — harmless but wasted | add it to the free list |
| 0 | 2 | duplicate in the free list (possible only with a list, not a bitmap) | rebuild the free list |
| 2 | 0 | **same data block in two files** — the dangerous case | allocate a new block, copy the contents, give one file the copy |
| 1 | 1 | in a file *and* free — would be handed out again | remove it from the free list |

The double-allocation case is the worst: if either file is removed, the block goes on the free list while still in use by the other.

```python-run
def check_blocks(n_blocks, files, free_list):
    in_use, free = [0] * n_blocks, [0] * n_blocks
    for blocks in files.values():
        for b in blocks:
            in_use[b] += 1
    for b in free_list:
        free[b] += 1
    problems = []
    for b in range(n_blocks):
        u, f = in_use[b], free[b]
        if (u, f) in ((1, 0), (0, 1)):
            continue
        if u == 0 and f == 0:
            problems.append(f"block {b:2d}: missing -> add to free list")
        elif u == 0 and f > 1:
            problems.append(f"block {b:2d}: listed free {f} times -> rebuild free list")
        elif u > 1:
            owners = [name for name, bl in files.items() if b in bl]
            problems.append(f"block {b:2d}: shared by {owners} -> copy to a fresh block for one of them")
        else:
            problems.append(f"block {b:2d}: in a file AND free -> remove from free list")
    return problems or ["all consistent"]

files = {"a.txt": [0, 1, 2], "b.txt": [3, 4, 2], "c.txt": [7, 8]}
free_list = [5, 6, 6, 8, 10, 11]
for line in check_blocks(12, files, free_list):
    print(line)
```

**What the code does.** `check_blocks` builds two lists of counters, one entry per block: `in_use[b]` counts how many times block `b` appears in a file, and `free[b]` how many times it appears in the list of free blocks. It fills them by going through every file's blocks and through the free list. Then for each block it looks at the pair of counts. `(1, 0)` and `(0, 1)` are correct. Anything else is reported with its repair: in neither list, listed free more than once, claimed by more than one file, or both in a file and free.

**The output.** In the small example, block 2 is shared by two files; block 6 is in the free list twice; block 8 is both in a file and marked free; block 9 is in neither.

### Directory consistency

A second pass checks files rather than blocks. It walks the directory tree, counting for each i-node how many directory entries refer to it, then compares that with the **link count** stored in the i-node.

- Stored count *higher* than the real number of entries: even when all names are removed, the count will not reach zero and the i-node is never freed. Wasteful; fix by correcting the count.
- Stored count *lower* than the real number: catastrophic. When one name is removed the count hits zero, the i-node and blocks are freed, and the remaining names point into storage that will be reused. Fix by raising the count to the true value.

Checkers also look for implausible things: i-nodes with absurd modes, directories with entries whose i-numbers exceed the number of i-nodes, files in user directories owned by the administrator with powerful permission bits set.

Journaling has made a full check on every reboot unnecessary, but the checker remains the tool of last resort when hardware corrupts the disk.

## File-system performance

Disk access is vastly slower than memory access, so file systems go to great lengths to avoid it.

### The buffer cache

The most common technique is the **block cache** (buffer cache): a collection of blocks that logically belong on disk but are kept in memory. Every read first checks the cache; a hash table on (device, block number) makes that check fast. When the cache is full, a block must be evicted, and all the page replacement algorithms apply. Because cache references are system calls rather than individual memory accesses, exact LRU is feasible here — a doubly linked list moved on every access.

But pure LRU is wrong for a file system, for a reason memory paging does not have: **crash consistency**. If a critical block — an i-node, say — is modified and placed at the "recently used" end of the list, it might stay in memory for a long time. A crash before it is written leaves the file system inconsistent. So blocks are classified. Will this block be needed again soon? Is it essential to consistency? Blocks that matter for consistency are written promptly, regardless of their position in the LRU order.

It is also unwise to keep *data* blocks in memory indefinitely. UNIX has a `sync` call that forces all modified blocks out, traditionally invoked every 30 seconds by a background daemon, so that at most half a minute of work is lost in a crash. Windows historically leaned towards writing modified blocks through immediately (**write-through**), partly because removable disks may be pulled out at any moment. Modern systems integrate the buffer cache with the page cache so that a file page is cached once whether it is accessed by read/write or by memory mapping.

### Read-ahead

When a file is being read sequentially and block k is requested, the file system also schedules block k+1 on the expectation that it will be wanted next. This helps sequential access greatly and hurts random access (wasted I/O and cache pollution), so the system watches each open file's access pattern: a seek switches read-ahead off; a return to sequential reading switches it back on.

### Reducing arm motion

On a magnetic disk, blocks likely to be used together should be close together. Free-space bitmaps make it easy to allocate a new block near the previous one. A deeper problem in i-node systems is that reading even a short file takes two accesses — one for the i-node, one for the data — and if all i-nodes sit at the start of the disk, the average distance between an i-node and its data is half the disk. The remedy is to divide the disk into **cylinder groups**, each with its own i-nodes, blocks and free list, and to allocate a file's blocks in the same group as its i-node.

None of this applies to solid-state drives, which have no arm; there, the concern is distributing writes evenly.

### Defragmentation

A freshly installed system has its files laid out contiguously. As files are created and removed, free space is chopped up, and new files are scattered over the disk. **Defragmentation** moves files to make them contiguous and consolidates free space. Windows needed it routinely on mechanical disks; Linux file systems, thanks to their allocation policies, generally cope without. On an SSD, defragmentation not only yields no benefit but shortens the device's life by using up write cycles.

> [!INTERVIEW]
> "Why is writing to a file sometimes lost after a crash even though `write` returned success?" Because `write` normally copies data into the buffer cache and returns; the kernel flushes it later. Durability requires an explicit `fsync` (or opening the file for synchronous writes), and even then the storage device's own write cache must be flushed. Databases call `fsync` at commit for exactly this reason — and pay for it in latency.

## Example file systems

### MS-DOS and the FAT family

The MS-DOS file system began on floppy disks and lives on in memory cards and USB sticks. Its directory entries are a fixed 32 bytes: an 8-character name plus 3-character extension, an attributes byte (read-only, hidden, system, archive), time and date, the **number of the first block**, and the file size as a 32-bit number — which caps a file at 4 GB.

Blocks are tracked through the file allocation table. The three variants are named for the width of a table entry: **FAT-12**, **FAT-16**, **FAT-32** (which really uses 28 bits). Block ("cluster") sizes are multiples of 512 bytes, and the maximum partition is roughly the number of addressable blocks times the block size:

```python-run
def max_partition(entry_bits, block_bytes, hard_cap=None):
    size = (1 << entry_bits) * block_bytes
    return min(size, hard_cap) if hard_cap else size

MB, GB, TB = 1 << 20, 1 << 30, 1 << 40
def pretty(n):
    return f"{n / TB:g} TB" if n >= TB else f"{n / GB:g} GB" if n >= GB else f"{n / MB:g} MB"

print("block size   FAT-12      FAT-16      FAT-32")
for kb in (0.5, 1, 2, 4, 8, 16, 32):
    block = int(kb * 1024)
    fat12 = pretty(max_partition(12, block)) if kb <= 4 else "-"
    fat16 = pretty(max_partition(16, block)) if kb >= 2 else "-"
    fat32 = pretty(max_partition(28, block, hard_cap=2 * TB)) if kb >= 4 else "-"
    print(f"{kb:>5} KB    {fat12:>9}   {fat16:>9}   {fat32:>9}")
```

**What the code does.** `max_partition` multiplies the number of blocks a table entry can address (2 to the power of the entry's width in bits, written `1 << entry_bits`) by the block size, and applies an upper limit if one is given. `pretty` turns a number of bytes into megabytes, gigabytes or terabytes. The loop prints the largest partition for each block size under the three variants, showing a dash where a variant does not support that block size.

**The output.** With 12-bit entries the largest partition is 16 megabytes; with 16-bit entries, 2 gigabytes (using 32-kilobyte blocks); with the 28-bit entries of FAT-32 the limit set by the partition table, 2 terabytes, is reached.

FAT-16's largest block size of 32 KB gives a 2 GB limit and wasted about half of every small file's last block; FAT-32 brought small blocks back for large disks. (FAT-32 partitions are further limited to 2 TB because the partition table counts 512-byte sectors in a 32-bit field.) The free blocks are found by scanning the table for entries with a special "unused" code; no separate bitmap exists.

### The classic UNIX file system

The file system of early UNIX is a model of economy. A directory entry was only 16 bytes: a 14-character name and a 2-byte i-number. Everything else is in the i-node: mode, link count, owner and group ids, size, three timestamps (last access, last modification, last i-node change) and the block addresses — ten direct ones, then single, double and triple indirect.

Looking up a path such as `/usr/ast/mbox` shows the machinery working together:

1. The root directory's i-node is at a fixed place on the disk. Read the root directory and find the entry `usr`, obtaining its i-number.
2. Read that i-node, and from it the blocks of the directory `/usr`. Search them for `ast`, obtaining another i-number.
3. Read that i-node and its directory blocks; find `mbox` and its i-number.
4. Read the i-node for `mbox` into memory, where it stays until the file is closed.

```mermaid
flowchart LR
    R["Root i-node (fixed location)"] --> RD["Root directory blocks: find usr"]
    RD --> UI["I-node of /usr"] --> UD["Directory blocks of /usr: find ast"]
    UD --> AI["I-node of /usr/ast"] --> AD["Directory blocks: find mbox"]
    AD --> MI["I-node of mbox, kept in memory while open"]
```

Each component costs an i-node read and at least one directory-block read, which is why name lookups are cached so aggressively. Relative paths work the same way but start from the working directory; `.` and `..` are ordinary directory entries, so no special code is needed for them.

Later UNIX file systems (the Berkeley fast file system, then ext2/3/4 in Linux) kept the i-node idea and added long file names, cylinder or block groups, larger blocks, extents and journaling.

### Optical discs: ISO 9660

The file system for CD-ROMs was designed for media that are written once and read on every kind of computer. With no deletions there are no free lists to manage, and files are stored **contiguously**. To be readable everywhere, the base standard is extremely conservative: short upper-case names, limited directory nesting, and fields stored in both byte orders so that neither big-endian nor little-endian machines are disadvantaged.

Each disc begins with a reserved area followed by a **primary volume descriptor** naming the volume and pointing at the root directory. A directory entry is variable-length and contains the entry length, the location and size of the file (start block plus byte length is all that is needed for a contiguous file), date and time, flags and the file name.

Two extensions made it bearable. **Rock Ridge** adds what UNIX systems need — long names, permission bits, symbolic links, deeper directories — in a field that other systems ignore. **Joliet**, from Microsoft, adds long names in Unicode and deeper nesting. A disc can carry both, and each operating system uses the extension it understands.

## Pitfalls

- **Assuming a bitmap is always bigger than a free list** — it is the reverse except on a nearly full disk.
- **Backing up a live file system without a snapshot.**
- **Treating "link count too high" and "too low" as equally harmless.** Too low is the dangerous one.
- **Relying on the buffer cache for durability.**
- **Defragmenting an SSD.**
- **Forgetting FAT's limits:** 4 GB per file, no permissions, no journaling, no hard links.

## Summary

- Block size trades wasted space against transfer speed; about 4 KB is typical. Free space is tracked by a **list** stored in free blocks or by a **bitmap**. **Quotas** have soft and hard limits.
- Backups are **physical** (every block; fast, inflexible) or **logical** (changed files plus the directories leading to them; selective and incremental).
- A consistency checker compares per-block **in-use** and **free** counts and per-file **link counts** against the directory structure.
- Performance comes from the **buffer cache** (with prompt writing of critical blocks), **read-ahead**, placing related blocks together (**cylinder groups**) and, on mechanical disks, **defragmentation**.
- **FAT** uses 32-byte directory entries and a table of next-block numbers in 12-, 16- or 32-bit flavours. Classic **UNIX** uses tiny directory entries and i-nodes with direct and indirect blocks. **ISO 9660** stores files contiguously on write-once media, extended by Rock Ridge and Joliet.

## Glossary

- **Block size** — the size of the units in which disk space is handed out.
- **Free list** — a list of the numbers of unused blocks, itself stored in unused blocks.
- **Bitmap** — one bit per block recording whether it is in use.
- **Quota** — a limit on how much disk space a user may occupy; *soft* limits warn, *hard* limits refuse.
- **Backup (dump)** — a copy of data kept in case the original is lost.
- **Incremental dump** — a backup of only what has changed since the previous one.
- **Physical / logical dump** — copying every block of a disk / copying selected files and directories.
- **Snapshot** — a frozen view of a file system at one moment.
- **Consistency checker (fsck)** — a program that finds and repairs contradictions in a file system's records.
- **Buffer cache (block cache)** — disk blocks kept in memory to avoid reading them again.
- **Write-through** — writing changed blocks to disk immediately instead of holding them in memory.
- **sync** — the operation that forces changed blocks in memory to be written to disk.
- **Read-ahead** — fetching the next block of a file before it is asked for.
- **Cylinder group** — a region of a disk with its own i-nodes and blocks, used to keep related data close together.
- **Defragmentation** — rearranging files so that each occupies neighbouring blocks.
- **FAT-12 / FAT-16 / FAT-32** — versions of the file allocation table system with table entries of different widths.
- **ISO 9660** — the standard file system for optical discs.

## Check yourself

```quiz
[
  {"q": "A disk has 1 KB blocks and holds a 1-byte file and a 2049-byte file. How much space do they occupy in total?",
   "options": ["2050 bytes", "3 KB", "4 KB", "5 KB"],
   "answer": 2,
   "explain": "The 1-byte file takes one block; the 2049-byte file takes three. Four blocks of 1 KB = 4 KB."},
  {"q": "When is a linked free list smaller than a bitmap?",
   "options": ["Always", "Never", "Only when the disk is nearly full", "Only when the disk is nearly empty"],
   "answer": 2,
   "explain": "The bitmap has a fixed size of one bit per block. The list holds a 32-bit number per free block, so it is smaller only when few blocks are free."},
  {"q": "During a consistency check, block 17 has an in-use count of 2 and a free count of 0. What is the correct repair?",
   "options": ["Add it to the free list", "Remove it from the free list", "Allocate a new block, copy the contents into it and attach it to one of the two files", "Nothing; this is normal"],
   "answer": 2,
   "explain": "Two files claim the same data block. If either were deleted the block would be freed while still in use, so each file must get its own copy."},
  {"q": "An i-node's stored link count is 1 but two directory entries refer to it. Why is this dangerous?",
   "options": ["The file cannot be opened", "Removing one name frees the i-node while the other name still points to it", "The file will be backed up twice", "It wastes one block"],
   "answer": 1,
   "explain": "When the count reaches zero the storage is released and may be reused, leaving the surviving directory entry pointing into someone else's data."},
  {"q": "Why does a file-system buffer cache not use pure LRU for all blocks?",
   "options": ["LRU is too slow for system calls", "Blocks critical to consistency, such as i-nodes, must be written to disk promptly rather than waiting to age out", "LRU cannot be implemented without hardware support", "Data blocks are never cached"],
   "answer": 1,
   "explain": "A recently used but modified metadata block could sit in memory for a long time. A crash before it is written would corrupt the file system."},
  {"q": "A logical dump saves a changed file deep in the tree. Why does it also save unchanged directories on the path to that file?",
   "options": ["To waste less tape", "So the file can be restored into the correct location with the right attributes even on an empty file system", "Because directories are always modified", "To verify checksums"],
   "answer": 1,
   "explain": "Restoring needs the containing directories to exist, with their owners and permissions, before the file can be placed."},
  {"q": "What limits a single file on a FAT-32 volume to 4 GB?",
   "options": ["The 28-bit table entries", "The 32-bit file-size field in the directory entry", "The 8.3 file-name format", "The block size"],
   "answer": 1,
   "explain": "The directory entry stores the size as a 32-bit number, whose maximum is 2^32 - 1 bytes."},
  {"q": "Why can ISO 9660 store every file contiguously?",
   "options": ["Optical discs are faster than magnetic disks", "The medium is written once, so file sizes are known in advance and files are never deleted", "It uses i-nodes", "It has a journal"],
   "answer": 1,
   "explain": "Contiguous allocation fails only when files grow or are removed. Neither happens on write-once media."}
]
```

> **Source:** Tanenbaum & Bos, Modern Operating Systems 4e, §4.4 (File-system management and optimization), §4.5 (Example file systems)
