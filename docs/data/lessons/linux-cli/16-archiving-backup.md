# Archiving and backup: gzip, tar, zip and rsync

> **Before this lesson:** you should know pipes and redirection ([Redirection and pipelines](#/lesson/linux-cli/redirection-pipelines)), how to copy files ([Manipulating files](#/lesson/linux-cli/manipulating-files)), `find` ([Searching for files](#/lesson/linux-cli/finding-files)) and the idea of SSH ([Networking tools](#/lesson/linux-cli/networking)).

## In plain words

Three everyday ideas explain this lesson.

**Compression** is vacuum-packing: the same clothes take up less room in the suitcase and come out unchanged when you open the bag. A compressed file holds the same information in fewer bytes.

**Archiving** is putting many loose items into one box. An archive is a single file that contains a whole directory tree — all the files, their names and their folders — so that it can be moved or stored as one thing. On Linux the usual box is made by a program called `tar`, and the box is normally vacuum-packed as well.

**Synchronising** is keeping two bookshelves identical by carrying across only the books that are new or changed, instead of re-copying the whole library. The program `rsync` does this, and works between computers too.

A **backup** is a spare copy kept so that a mistake, a broken disk or a stolen laptop does not mean losing your work.

Why this matters for a job: sending code and data to other people and machines, saving storage costs, moving large data sets efficiently and protecting work against loss are part of every technical role. Whether a backup exists — and has been tested — is what decides whether an accident costs an hour or a month.

## Motivation

A dataset of two million small images takes four hours to copy to another machine as individual files and twenty minutes as one archive. A year of logs occupies 300 GB raw and 18 GB compressed. A laptop dies, and whether that costs you an afternoon or a quarter depends on a command that did or did not run last night.

Four families of tools cover this ground. **Compressors** (`gzip`, `bzip2`, `xz`, `zstd`) make one file smaller. **Archivers** (`tar`, `zip`) gather many files into one. **Synchronisers** (`rsync`) make one directory tree match another, transferring only the differences. You will use all of them constantly — to ship code and models, to trim storage bills, to move data between machines, and to keep the backups that let you recover from the mistakes described elsewhere in this track.

## Compression in one paragraph

Compression removes redundancy. Text, logs, CSV and source code are highly repetitive and often shrink by 70–95%. Data that is already compressed — JPEG, PNG, MP4, MP3, most model checkpoints, and anything encrypted — has no redundancy left, and compressing it again wastes CPU time for a saving of a percent or two. All the tools here are **lossless**: decompression restores the original byte for byte.

You can watch the effect of redundancy directly with Python's `zlib`, which implements the same algorithm as `gzip`:

```python-run
import os, zlib

samples = {
    "log lines (repetitive)": b"2026-11-20 10:00:01 INFO request ok status=200 path=/api/forecast\n" * 2000,
    "English-like text":      (b"the quick brown fox jumps over the lazy dog and keeps running " * 40) * 30,
    "CSV of numbers":         "\n".join(f"{i},{i * 7 % 1000},{i % 13}" for i in range(20000)).encode(),
    "random bytes (like encrypted or already-compressed data)": os.urandom(130_000),
}
for label, data in samples.items():
    fast, best = zlib.compress(data, 1), zlib.compress(data, 9)
    print(f"{label:58} {len(data):7d} -> level 1: {len(fast):6d} ({len(fast) / len(data):6.1%})  "
          f"level 9: {len(best):6d} ({len(best) / len(data):6.1%})")

twice = zlib.compress(zlib.compress(samples["CSV of numbers"], 9), 9)
print("compressing an already-compressed stream again:", len(zlib.compress(samples['CSV of numbers'], 9)), "->", len(twice))
```

The random sample comes out slightly *larger* than it went in, and so does the second pass over compressed data.

## `gzip` and its relatives

`gzip` compresses a single file and **replaces it** with a `.gz` version; `gunzip` (or `gzip -d`) reverses that.

```bash
mira@forge:~/lab$ ls -l access.log
-rw-r--r-- 1 mira mira 248113402 Nov 20 09:00 access.log
mira@forge:~/lab$ gzip access.log
mira@forge:~/lab$ ls -l access.log.gz
-rw-r--r-- 1 mira mira 14980211 Nov 20 09:00 access.log.gz
mira@forge:~/lab$ gzip -l access.log.gz
         compressed        uncompressed  ratio uncompressed_name
           14980211           248113402  94.0% access.log
mira@forge:~/lab$ gunzip access.log.gz
```

| Option | Effect |
|---|---|
| `-d` | decompress |
| `-k` | keep the original instead of replacing it |
| `-c` | write to standard output, leaving the file alone |
| `-1` … `-9` | speed versus size; `-6` is the default |
| `-l` | list compression statistics |
| `-t` | test integrity |
| `-r` | recurse into directories, compressing each file separately |
| `-v` | verbose |

You rarely need to decompress only to look inside. A family of `z` commands works on compressed files directly, and `-c` puts compression into pipelines:

```bash
mira@forge:~/lab$ zcat access.log.gz | head -n 2
mira@forge:~/lab$ zless access.log.gz
mira@forge:~/lab$ zgrep -c ' 500 ' access.log.2026-11-1*.gz
access.log.2026-11-18.gz:14
access.log.2026-11-19.gz:203
mira@forge:~/lab$ pg_dump weather | gzip > weather-$(date +%F).sql.gz
mira@forge:~/lab$ gunzip -c weather-2026-11-20.sql.gz | psql weather_restore
```

The alternatives share almost the same options; what differs is the trade-off.

| Tool | Extension | Speed | Ratio | Use it when |
|---|---|---|---|---|
| `gzip` | `.gz` | fast | good | the universal default; every system can read it |
| `bzip2` | `.bz2` | slow | better | legacy archives; rarely chosen today |
| `xz` | `.xz` | very slow to compress, fast to decompress | best | distributing software: compress once, download many times |
| `zstd` | `.zst` | very fast both ways | good to excellent (`-1` … `-19`) | backups, large datasets, anything time-sensitive |

`zstd -T0` and `xz -T0` use all CPU cores; `pigz` is a parallel drop-in for `gzip`.

> [!TIP]
> Do not compress what is already compressed. Running `gzip` over a directory of JPEGs or `.parquet` files burns CPU for nothing. `file name` tells you what you have, and `gzip -l` or a quick `ls -l` before and after tells you whether it was worth it.

## `tar` — many files into one

`tar` (*tape archive*) bundles a directory tree — names, contents, permissions, owners, timestamps, links — into a single stream. It does not compress by itself; it hands that job to a compressor, which is why Linux archives have double extensions such as `.tar.gz`.

```mermaid
flowchart LR
    D["Directory tree: project"] -->|tar c| T["project.tar: one uncompressed stream"]
    T -->|gzip, xz or zstd| Z[project.tar.gz]
    Z -->|decompress| T2[tar stream]
    T2 -->|tar x| D2[Directory tree restored]
```

A `tar` command is a **mode** letter, some options, then the archive name given to `f`:

| Mode | Meaning |
|---|---|
| `c` | **c**reate an archive |
| `x` | e**x**tract |
| `t` | lis**t** the contents |
| `r` | append files to an uncompressed archive |

| Option | Meaning |
|---|---|
| `f FILE` | the archive file (`-` means standard input or output) |
| `v` | verbose: show each entry |
| `z` / `j` / `J` | filter through gzip / bzip2 / xz |
| `--zstd` | filter through zstd |
| `a` | pick the compressor from the archive's extension |
| `C DIR` | change to DIR before doing anything |
| `p` | preserve permissions on extraction (default for root) |
| `--exclude=PATTERN` | skip matching entries |
| `--strip-components=N` | on extraction, drop the first N path components |

### Create, list, extract

```bash
mira@forge:~$ tar -czf weather-api.tar.gz weather-api/          # create, gzip, file
mira@forge:~$ tar -tzf weather-api.tar.gz | head -n 5           # list
weather-api/
weather-api/README.md
weather-api/pyproject.toml
weather-api/src/
weather-api/src/app.py
mira@forge:~$ mkdir /tmp/restore && tar -xzf weather-api.tar.gz -C /tmp/restore     # extract elsewhere
mira@forge:~$ tar -xzf weather-api.tar.gz weather-api/pyproject.toml                # extract one member
mira@forge:~$ tar -xf anything.tar.xz                           # modern tar detects the compression itself
```

The mnemonics are worth saying aloud: **c**reate **z**ipped **f**ile, e**x**tract **z**ipped **f**ile, lis**t** **z**ipped **f**ile.

Realistic creation commands usually exclude junk and compress harder:

```bash
mira@forge:~$ tar --exclude='.git' --exclude='__pycache__' --exclude='.venv' --exclude='*.pt' \
      -czf weather-api-src.tar.gz weather-api/
mira@forge:~$ tar --zstd -cf dataset.tar.zst -C /srv/data imagenet-subset
mira@forge:~$ tar -cf - big-dir | zstd -T0 -10 > big-dir.tar.zst      # multi-threaded compression
```

### How names are stored

`tar` records paths as you gave them. Archive `weather-api/` and the members are `weather-api/...`; they will be recreated under whatever directory you extract in. Give an absolute path and GNU `tar` strips the leading slash (and says so), so that extraction never writes to absolute locations by surprise. The `-C` option controls both ends: on creation, which directory names are relative to; on extraction, where files land.

> [!WARNING]
> **List before you extract** (`tar -tf archive`). An archive whose members are not wrapped in a single top-level directory — a "tarbomb" — scatters hundreds of files across your current directory, **overwriting any existing files with the same names** without asking. If the listing does not show one common leading directory, extract into a fresh empty directory with `-C`. And treat archives from untrusted sources with extra care: members can carry odd permissions or paths, so never extract them as root.

### Streaming through pipes and across machines

Because `tar` reads and writes streams, it combines with `ssh` to move a tree between machines with no intermediate file — one of the great classic idioms:

```bash
mira@forge:~$ tar -czf - experiments/ | ssh otto@build01 'tar -xzf - -C /srv/archive'
mira@forge:~$ ssh otto@build01 'tar -czf - -C /var/log weather' > weather-logs-$(date +%F).tar.gz
mira@forge:~$ tar -cf - data | pv | zstd -T0 | ssh backup 'cat > /srv/backup/data.tar.zst'   # pv shows throughput
```

For millions of tiny files this is dramatically faster than copying them individually, because one continuous stream replaces millions of separate transfers.

## `zip` — for exchanging files with other platforms

On Linux, `tar` is the native format. `zip` matters because Windows and macOS open it without extra software, and because some systems (cloud function deployments, browser extensions, grading portals) demand it. Unlike `tar`+`gzip`, zip compresses each member separately, so a single file can be extracted without reading the whole archive, at the cost of a somewhat worse overall ratio.

```bash
mira@forge:~$ zip -r report-bundle.zip report/ -x '*.DS_Store' '*/__pycache__/*'
  adding: report/ (stored 0%)
  adding: report/summary.md (deflated 61%)
  adding: report/figures/loss.png (deflated 2%)
mira@forge:~$ unzip -l report-bundle.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
        0  2026-11-20 10:02   report/
     8112  2026-11-20 09:58   report/summary.md
   221904  2026-11-19 17:31   report/figures/loss.png
mira@forge:~$ unzip report-bundle.zip -d /tmp/unpacked
mira@forge:~$ unzip -p report-bundle.zip report/summary.md | head -n 3
```

Remember `-r` (without it `zip` stores the directory entry and none of its contents), `unzip -l` to list, and `-d` to choose the destination. Note in the output that the PNG "deflated 2%": it was already compressed.

## `rsync` — synchronise, do not recopy

`cp -r` and `scp -r` copy everything every time. `rsync` compares source and destination and transfers only what differs — by default, files whose size or modification time has changed — and for changed files it can send only the altered portions. An interrupted transfer resumes on the next run.

```
rsync  options  SOURCE...  DESTINATION
```

Either side may be remote, written `user@host:path` (over SSH).

```bash
mira@forge:~$ rsync -av projects/ /mnt/backup/projects/
sending incremental file list
./
weather-api/src/app.py
weather-api/tests/test_app.py

sent 48,220 bytes  received 77 bytes  96,594.00 bytes/sec
total size is 1,204,553,118  speedup is 24,940.58
mira@forge:~$ rsync -av projects/ /mnt/backup/projects/
sending incremental file list

sent 9,811 bytes  received 19 bytes  19,660.00 bytes/sec
total size is 1,204,553,118  speedup is 122,538.47
```

The first run sent two changed files out of a 1.2 GB tree; the second, with nothing changed, sent only the file list.

| Option | Meaning |
|---|---|
| `-a` | archive mode: recurse and preserve permissions, times, owners, groups and symlinks |
| `-v` | list transferred files |
| `-z` | compress data in transit (useful on slow links, pointless on a fast LAN) |
| `-n`, `--dry-run` | show what **would** happen; change nothing |
| `--delete` | remove files from the destination that no longer exist in the source |
| `-P` | show progress and keep partially transferred files so they can resume |
| `--exclude=PATTERN` | skip matches (repeatable); `--exclude-from=FILE` reads a list |
| `-h` | human-readable sizes |
| `-e 'ssh -p 2222'` | choose the remote shell and its options |
| `--bwlimit=KBPS` | throttle so you do not saturate a link |
| `--link-dest=DIR` | hard-link unchanged files to a previous backup — cheap snapshots |

### The trailing slash

This single character changes the meaning of the source argument and catches everyone once:

```bash
rsync -av projects/  /mnt/backup/projects/    # copy the CONTENTS of projects into .../projects/
rsync -av projects   /mnt/backup/             # copy the DIRECTORY projects into backup -> /mnt/backup/projects/
rsync -av projects   /mnt/backup/projects/    # oops: creates /mnt/backup/projects/projects/
```

A trailing slash on the **source** means "what is inside this directory"; no slash means "this directory itself".

### Mirrors and `--delete`

Without `--delete`, `rsync` only adds and updates, so files you removed from the source linger in the destination forever. With it, the destination becomes an exact mirror.

> [!WARNING]
> `--delete` removes data on the destination, and combined with a wrong path or a missing trailing slash it can remove nearly all of it. Worse, if the **source** is accidentally empty — an unmounted disk leaves an empty mount-point directory — `rsync --delete` faithfully empties your backup to match. **Always run the exact command with `-n` first** and read the list of deletions; in scripts, verify that the source is mounted and non-empty before synchronising. A mirror is also not a history: a file corrupted or deleted at the source is corrupted or deleted in the mirror on the next run.

```bash
mira@forge:~$ rsync -avn --delete projects/ /mnt/backup/projects/ | grep '^deleting' | head -n 3
deleting weather-api/old_notes.txt
deleting scratch/tmp.ipynb
mira@forge:~$ rsync -av --delete projects/ /mnt/backup/projects/
```

### Over the network

```bash
mira@forge:~$ rsync -avzP --exclude='.venv' --exclude='*.ckpt' weather-api/ deploy@web01:/srv/weather-api/
mira@forge:~$ rsync -avP deploy@gpu02:/srv/runs/exp09/ ./exp09/          # pull results back
```

To see why repeated runs are cheap, here is the decision `rsync` makes for each file in its default mode — a comparison of size and modification time — along with the effect of `--delete`:

```python-run
source = {"app.py": (5120, 1700), "utils.py": (880, 1500), "model.bin": (9_000_000, 1200), "new.md": (300, 1750)}
dest   = {"app.py": (5010, 1600), "utils.py": (880, 1500), "model.bin": (9_000_000, 1200), "old.txt": (40, 900)}
# values are (size in bytes, modification time)

def plan(src, dst, delete=False):
    actions, sent = [], 0
    for name, meta in sorted(src.items()):
        if name not in dst:
            actions.append(f"send     {name}  (missing at destination)"); sent += meta[0]
        elif dst[name] != meta:
            actions.append(f"update   {name}  (size or mtime differs)"); sent += meta[0]
        else:
            actions.append(f"skip     {name}")
    for name in sorted(set(dst) - set(src)):
        actions.append(f"{'DELETE  ' if delete else 'keep    '} {name}  (not in source)")
    return actions, sent

for delete in (False, True):
    actions, sent = plan(source, dest, delete)
    total = sum(size for size, _ in source.values())
    print(f"--- rsync -a{' --delete' if delete else ''}: transfer {sent:,} of {total:,} bytes")
    print("\n".join("  " + a for a in actions))

print("--- empty source with --delete (the disaster case):")
print("\n".join("  " + a for a in plan({}, dest, delete=True)[0]))
```

## What makes something a backup

A copy is a backup only if it would survive whatever destroys the original and you have shown that you can restore from it.

- **3-2-1.** Three copies, on two different kinds of storage, one of them off-site. A second folder on the same disk protects against a mistaken `rm`, and nothing else.
- **Versions, not only a mirror.** Keep dated snapshots so that yesterday's deletion or last week's silent corruption can be undone. `rsync --link-dest` makes each snapshot cost only the changed files; tools such as `restic` and `borg` add deduplication and encryption.
- **Automation.** A backup that depends on someone remembering does not happen. Schedule it with cron or a systemd timer.
- **Restore tests.** Extract an archive into a scratch directory and compare (`tar -df`, `diff -r`, checksums). Dump files can be truncated and archives corrupted; you want to learn that on a quiet Tuesday.
- **Consistency.** Copying a running database's files yields garbage. Use the database's own dump tool (`pg_dump`, `mysqldump`) and back up the dump.

```bash
mira@forge:~$ today=$(date +%F)
mira@forge:~$ rsync -a --delete --link-dest=/mnt/backup/latest projects/ /mnt/backup/$today/ \
      && ln -sfn /mnt/backup/$today /mnt/backup/latest
mira@forge:~$ tar -tzf weather-api.tar.gz > /dev/null && echo "archive readable"
archive readable
```

> [!INTERVIEW]
> Expect: "What is the difference between `tar` and `gzip`?" (bundling many files versus compressing one stream; `tar -z` chains them), "`scp` versus `rsync`?" (rsync transfers only differences, resumes, preserves attributes and can mirror with `--delete`), "What does the trailing slash do in rsync?", and for operations roles, "How would you design backups for this service?" — where 3-2-1, versioned snapshots, automated schedules and *tested restores* are the points being listened for.

## Pitfalls

- **Extracting without listing first**, into a directory with files you care about.
- **Forgetting `f`**, or putting other letters after it: in `tar -cfz out.tar.gz dir` the archive name becomes `z`. Keep `f` last in the cluster.
- **`gzip` replacing the original** when you wanted both; use `-k`.
- **Compressing compressed data.**
- **rsync trailing slashes** and unreviewed `--delete`.
- **`zip` without `-r`.**
- **Calling a same-disk copy or an untested archive a backup.**
- **Archiving live databases or files being written**, producing inconsistent contents.

## Cheat sheet

| Task | Command |
|---|---|
| Compress / decompress one file | `gzip f` / `gunzip f.gz` |
| Compress, keeping the original | `gzip -k f` |
| Read compressed text | `zcat f.gz`, `zless f.gz`, `zgrep pat f.gz` |
| Fast modern compression | `zstd -T0 f`, `unzstd f.zst` |
| Create a gzip tarball | `tar -czf out.tar.gz dir/` |
| List an archive | `tar -tf out.tar.gz` |
| Extract into a directory | `tar -xf out.tar.gz -C dest/` |
| Extract without the top-level directory | `tar -xf a.tar.gz --strip-components=1 -C dest/` |
| Exclude paths | `tar --exclude='.git' -czf …` |
| Copy a tree over SSH | `tar -czf - dir \| ssh host 'tar -xzf - -C /dest'` |
| Zip / unzip | `zip -r out.zip dir/`, `unzip out.zip -d dest/` |
| List a zip | `unzip -l out.zip` |
| Synchronise locally | `rsync -av src/ dest/` |
| Preview a mirror | `rsync -avn --delete src/ dest/` |
| Push to a server with progress | `rsync -avzP src/ user@host:/path/` |
| Snapshot with hard links | `rsync -a --link-dest=PREV src/ NEW/` |

## Summary

- Compression removes redundancy and works well on text, poorly on already-compressed data. `gzip` is universal, `xz` smallest, `zstd` fastest.
- `tar` bundles a tree into one stream and delegates compression: `c` create, `t` list, `x` extract, `f` file, `z`/`J`/`--zstd` for the compressor, `-C` for location. List before extracting.
- `zip` is the cross-platform archive; remember `-r`.
- `rsync -a` transfers only differences; a trailing slash on the source means its contents; `--delete` makes a mirror and must be previewed with `-n`.
- Backups need multiple locations, versions, automation and tested restores.

## Glossary

| Term | Meaning |
|---|---|
| compression | storing the same data in fewer bytes |
| lossless | compression from which the original is restored exactly |
| redundancy | repetition in data, which compression removes |
| archive | one file containing many files and directories |
| tarball | an archive made by `tar`, usually compressed, such as `name.tar.gz` |
| extract | unpack an archive back into files |
| synchronise | make one directory tree match another by copying only the differences |
| mirror | an exact copy kept up to date, including deletions |
| dry run | a rehearsal that shows what would be done without doing it |
| backup | a spare copy kept in case the original is lost |
| snapshot | a copy of data as it was at one moment |
| restore | bring data back from a backup |

## Check yourself

```quiz
[
  {"q": "What does `tar -czf site.tar.gz site/` do?",
   "options": ["Extracts site.tar.gz into site/", "Creates a gzip-compressed archive named site.tar.gz containing the directory site/", "Lists the contents of site.tar.gz", "Compresses each file in site/ separately"],
   "answer": 1,
   "explain": "c creates, z filters through gzip and f names the archive file."},
  {"q": "Why is it wise to run `tar -tf archive.tar.gz` before extracting?",
   "options": ["It makes extraction faster", "To see whether members share a single top-level directory or would spill into, and overwrite files in, the current directory", "tar refuses to extract otherwise", "It verifies the checksum of each file"],
   "answer": 1,
   "explain": "Extraction overwrites existing files of the same name without asking. Listing shows exactly which paths will be created."},
  {"q": "You gzip a 2 GB folder of JPEG photos and save almost nothing. Why?",
   "options": ["gzip only works on text files", "JPEG data is already compressed, so little redundancy remains", "The compression level was too low", "The files were too large"],
   "answer": 1,
   "explain": "Lossless compressors exploit redundancy. Already-compressed or encrypted data looks random and does not shrink."},
  {"q": "What is the difference between `rsync -a data/ /backup/data/` and `rsync -a data /backup/data/`?",
   "options": ["None", "The first copies the contents of data into /backup/data/; the second creates /backup/data/data/", "The second deletes extra files", "The first is recursive and the second is not"],
   "answer": 1,
   "explain": "A trailing slash on the source means the directory's contents; without it the directory itself is copied into the destination."},
  {"q": "What should you always do before running an rsync command that includes `--delete`?",
   "options": ["Add -z", "Run the same command with -n (dry run) and review what would be deleted", "Unmount the destination", "Compress the source"],
   "answer": 1,
   "explain": "--delete removes destination files that are absent from the source. A wrong path or an empty source would wipe the destination."},
  {"q": "In `tar -czf - logs/ | ssh host 'tar -xzf - -C /srv/archive'`, what does the dash after f mean?",
   "options": ["A file literally named -", "Standard output on the creating side and standard input on the extracting side", "Disable compression", "Use the default tape device"],
   "answer": 1,
   "explain": "A dash as the archive name tells tar to write to or read from its standard stream, allowing the archive to flow through a pipe."},
  {"q": "Why is an rsync mirror on a second disk in the same machine, updated nightly, not a sufficient backup strategy?",
   "options": ["rsync does not preserve permissions", "It shares the machine's fate (theft, fire, power surge) and reproduces deletions and corruption on the next run, with no history to go back to", "Mirrors cannot be restored", "Nightly is too frequent"],
   "answer": 1,
   "explain": "Good backups are kept in more than one place and retain earlier versions; a mirror offers neither."},
  {"q": "Which command shows the names inside a zip file without extracting it?",
   "options": ["zip -t file.zip", "unzip -l file.zip", "tar -tf file.zip", "gunzip -l file.zip"],
   "answer": 1,
   "explain": "unzip -l lists each member with its size and timestamp."}
]
```

> **Source:** Shotts, *The Linux Command Line*, ch. 18 (Archiving and Backup). All examples and wording are original to this guide.
