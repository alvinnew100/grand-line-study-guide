# Linux shell essentials and configuration management

> **Before this lesson:** read [Python packaging, Makefiles and pre-commit](#/lesson/mlops/packaging-tooling).
> You should have opened a terminal at least once; no Linux experience is assumed.

## In plain words

A **shell** is the program behind a terminal window: you type a line of text, it runs a program
and prints the result. **Linux** is the operating system that almost every server runs, and its
usual shell is called **bash**. There is no desktop and no mouse on a server, so the shell is how
you look inside a machine that is misbehaving. It is the mechanic's toolbox of this job: a few
dozen small tools, each doing one thing, that you combine as needed.

**Configuration** is the second topic. It means every setting that tells a program what to do
without changing its code: which database to talk to, which model to load, what learning rate to
train with. Think of the dials on an oven. The oven (the code) is the same in every kitchen; the
dial settings differ from one dish to the next. Configuration management is the habit of writing
those settings down, checking them, and knowing which settings produced which result.

Why this matters for a job: debugging on a real system happens in a shell, and interviewers ask
both practical questions ("a job was killed overnight, what do you check?") and design questions
("where do you put the password, the learning rate and the rollout percentage?").

## Why shell skills matter for MLOps

Every container, CI machine, training server and Kubernetes pod (the unit in which Kubernetes
runs a program; lesson 22) runs Linux. When a training job dies at 3 a.m., you connect to the
machine with `ssh` (secure shell, a command that opens a terminal on a remote computer), read
logs, check free disk space and GPU memory, and look at the settings the program was started
with. The first half of this lesson is that survival kit. The second half is configuration
management.

## Navigating and inspecting

Files on Linux live in a tree of **directories** (folders) starting at `/`. In the commands below,
everything after a `#` is a comment, and `;` separates two commands on one line.
```bash
pwd; ls -lah; cd /data/projects
tree -L 2                       # directory overview (if installed)
du -sh * | sort -h              # what is eating disk?
df -h                           # free space per filesystem (full disks kill training jobs)
find . -name "*.parquet" -size +100M -mtime -7    # large parquet files changed in last 7 days
head -n 5 data.csv; tail -f train.log             # follow a log as it grows
wc -l data.csv                  # count lines (rows + header)
less +F app.log                 # scrollable follow mode
```

Reading them: `pwd` prints the directory you are in, `ls -lah` lists its contents with sizes, and
`cd` moves to another directory. `du` reports how much disk space each item uses and `df` how much
is free on each disk. `find` searches for files by name, size or age. `head` and `tail` print the
first or last lines of a file; `tail -f` keeps printing as new lines are added, which is how you
watch a **log** (the running diary a program writes about what it is doing). `wc -l` counts lines.
Most commands take **flags**, options beginning with a dash, such as `-h` for "human-readable
sizes".

## Text processing pipelines

The symbol `|` is a **pipe**: it sends the output of the command on its left into the command on
its right. Unix tools are deliberately small and single-purpose, and pipes are how they are
combined into something useful. This is the ancestor of every data pipeline. Kleppmann (*DDIA*,
ch. 10) begins his treatment of batch processing with the same observation: a chain of small
commands that analyses a web-server log is a tiny batch job, and large-scale systems such as
MapReduce spread the same pattern across many machines.

```bash
# top 5 endpoints by request count from an access log
awk '{print $7}' access.log | sort | uniq -c | sort -rn | head -5

# count prediction errors by model version in JSON logs
grep '"level":"error"' service.log | jq -r '.model_version' | sort | uniq -c

# p95-ish latency from a column of numbers (nearest rank)
cut -d, -f3 latencies.csv | sort -n | awk '{a[NR]=$1} END {print a[int(NR*0.95+0.999)]}'

# replace a config value in place
sed -i 's/batch_size: 32/batch_size: 64/' configs/train.yaml
```

Take the first one apart, left to right. `awk '{print $7}' access.log` prints the seventh
space-separated field of every line, which in a web-server log is the requested path. `sort` puts
identical paths next to each other. `uniq -c` collapses each run of identical lines into one line
with a count in front. `sort -rn` sorts by that count, largest first. `head -5` keeps the top
five. No single tool knows how to "rank endpoints"; the chain does.

In the others, `grep` keeps only the lines containing a pattern, `jq` pulls a field out of JSON
text, `cut -d, -f3` takes the third comma-separated column, and `sed 's/old/new/'` replaces text.
The third example computes a **p95**: the value below which 95% of the numbers fall.

| Tool | Use |
|---|---|
| `grep -rn "pattern" src/` | search text |
| `cut`, `awk` | select / compute columns |
| `sort`, `uniq -c` | group and count |
| `sed` | stream edit |
| `jq` | query and transform JSON (structured logs, API responses) |
| `xargs`, `parallel` | run a command per input line, optionally in parallel |
| `tee` | write to file and stdout simultaneously |

### Redirection and exit codes

Every program has two output channels: **stdout** (standard output) for normal results and
**stderr** (standard error) for error messages. Both normally appear on the screen.

```bash
python train.py > train.log 2>&1      # stdout and stderr to file
python train.py 2>&1 | tee train.log  # and see it live
python train.py && echo "ok" || echo "failed with $?"
```

`>` sends stdout to a file. `2>&1` means "send channel 2 (stderr) to wherever channel 1 (stdout)
is going". `tee` writes its input to a file and also passes it on to the screen.

Every program also returns an **exit code** when it ends: 0 means success and anything else means
failure. `a && b` runs `b` only if `a` succeeded, `a || b` runs `b` only if `a` failed, and `$?`
holds the exit code of the last command. CI systems, orchestrators and Kubernetes all decide "did
this step pass?" from the exit code alone. So a training script must exit with a non-zero code
when it fails (`sys.exit(1)`, or let the exception propagate) and must never print an error and
then exit with 0.

## Processes, resources and GPUs

```bash
ps aux | grep train             # running processes
top / htop                      # live CPU and memory
free -h                         # RAM
nvidia-smi                      # GPU utilisation, memory, processes
watch -n 1 nvidia-smi           # refresh every second
kill <pid>; kill -9 <pid>       # SIGTERM (graceful) vs SIGKILL (immediate)
nohup python train.py > log 2>&1 &     # survive logout
tmux new -s train               # persistent terminal session; detach with Ctrl-b d

A **process** is one running program, identified by a number called its **PID**. `ps` lists
processes, `top` shows which are using the CPU and memory, and `nvidia-smi` does the same for
GPUs. `kill` sends a **signal**, a short message from the operating system to a process.
**SIGTERM** asks the process to stop and gives it the chance to finish cleanly; **SIGKILL** (`kill
-9`) ends it immediately and cannot be ignored. A command ending in `&` runs in the background,
and `nohup` or `tmux` keep it running after you disconnect.

> [!NOTE]
> Kubernetes stops a pod by sending **SIGTERM**, waiting for `terminationGracePeriodSeconds` (30
> seconds by default), then sending SIGKILL. A serving process should react to SIGTERM by
> finishing the requests it has already accepted; a training job should save a **checkpoint**
> (its progress so far) so it can resume. The web servers Uvicorn and Gunicorn already handle
> SIGTERM this way.

## Permissions, users and networking basics

```bash
chmod +x scripts/run.sh         # make executable
chmod 600 ~/.ssh/id_ed25519     # private keys must be private
chown app:app /models -R
whoami; id                      # containers should not run as root (lesson 17)
curl -s localhost:8000/health   # hit a local endpoint
curl -X POST localhost:8000/predict -H 'Content-Type: application/json' -d '{"tenure": 12}'
ss -tlnp                        # which ports are listening
ssh -L 5000:localhost:5000 user@trainbox   # tunnel a remote MLflow UI to your laptop
scp model.onnx user@host:/models/
```

`chmod` changes who may read, write or run a file; `600` means "only the owner may read and
write". `chown` changes the owner. **root** is the all-powerful administrator account. `curl`
sends a request to a web address and prints the answer, which makes it the quickest way to test a
service. A **port** is a numbered door on a machine through which one program accepts network
connections (the example service listens on port 8000), and `ss -tlnp` lists which doors are open.
`scp` copies a file to another machine over ssh.

## Shell scripts that do not lie

```bash
#!/usr/bin/env bash
set -euo pipefail        # exit on error, on unset variables, and on failures inside pipes
IFS=$'\n\t'

DATA_DIR="${DATA_DIR:-/data}"     # default if unset
MODEL_URI="${1:?usage: score.sh MODEL_URI}"   # required argument

echo "[$(date -Is)] scoring with ${MODEL_URI}"
python -m churn.score --model "${MODEL_URI}" --input "${DATA_DIR}/today.parquet"
```

The first line, `#!/usr/bin/env bash`, tells the system to run the file with bash. The second is
the most valuable line in any shell script. By default bash carries on after a command fails, so a
script with a broken step in the middle still reports success. `set -e` stops at the first
failure, `-u` treats the use of an undefined variable as an error, and `-o pipefail` makes a
pipeline fail if any command inside it fails. `${DATA_DIR:-/data}` means "the value of `DATA_DIR`,
or `/data` if it is not set", and `${1:?...}` means "the first argument, or stop with this message
if it is missing".

## Environment variables

An **environment variable** is a named value that the operating system hands to a program when it
starts, for example `MLFLOW_TRACKING_URI=http://mlflow:5000`. The program reads it by name. This
is the one configuration channel that every platform supports: Docker, Kubernetes, CI systems and
cloud services all have a way to set environment variables for the programs they start.

```bash
export MLFLOW_TRACKING_URI=http://mlflow:5000
env | grep MLFLOW
MODEL_STAGE=prod python serve.py     # set for one command only
```

## Configuration management

### The twelve-factor rule

The *Twelve-Factor App* is a widely followed list of rules for building services that are easy to
deploy. Its third rule says: **store config in the environment**, strictly separate from code.
Here "config" means everything that differs between deployments (development, staging,
production): addresses of other services, credentials, feature flags, sizes. A quick test of
whether you have done this: could the code be published openly today without exposing a
password?

ML adds a second kind of configuration: **experiment configuration**, the hyperparameters,
feature lists, date ranges of data and model type. This differs between training *runs*, and it
must be versioned and recorded with each run.

| Kind | Examples | Where it lives |
|---|---|---|
| Deployment config | DB URL, MLflow URI, log level, replicas | env vars, ConfigMaps, secret manager |
| Secrets | API keys, passwords | secret manager / K8s Secrets, never Git |
| Experiment config | learning rate, features, date window | YAML in Git + logged to the tracker |
| Runtime flags | rollout percentage, kill switch | feature-flag service or config store |

### Typed settings with pydantic-settings

Environment variables are always text. **pydantic-settings** is a library that reads them into a
Python object, converts each to a declared type, applies defaults and rejects invalid values. An
invalid setting then stops the service when it starts, with a clear message. This behaviour is
called **failing fast**, and it is far better than failing at the first customer request.

```python
# src/churn/serve/settings.py
from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CHURN_", env_file=".env")

    model_uri: str = "models:/churn@champion"
    mlflow_tracking_uri: HttpUrl = "http://localhost:5000"
    log_level: str = "INFO"
    max_batch_size: int = Field(32, ge=1, le=1024)
    request_timeout_s: float = 2.0

settings = Settings()   # reads CHURN_MODEL_URI, CHURN_MAX_BATCH_SIZE, ... ; raises if invalid
```

Reading the class: each attribute is one setting with its type and default. `env_prefix="CHURN_"`
means the setting `max_batch_size` is read from the variable `CHURN_MAX_BATCH_SIZE`.
`Field(32, ge=1, le=1024)` sets a default of 32 and requires a value between 1 and 1024 (`ge` is
"greater than or equal", `le` is "less than or equal"). Creating `Settings()` does the reading and
checking.

### Hierarchical experiment config with Hydra / OmegaConf

Experiment configuration is usually nested (a model section, a data section) and you want to swap
whole sections: "the same run, but with logistic regression". **Hydra** is a library for that. It
builds one configuration out of several YAML files, lets you override any value from the command
line, and saves the final configuration of every run. **OmegaConf** is the library underneath it
that represents the nested settings.

```yaml
# configs/train.yaml
defaults:
  - model: gbm           # picks configs/model/gbm.yaml
  - data: last_90_days
  - _self_
seed: 42
target: churned_30d
features: [tenure_months, plan, monthly_charges, support_tickets_30d]
```

```yaml
# configs/model/gbm.yaml
name: hist_gradient_boosting
params:
  learning_rate: 0.05
  max_iter: 400
  max_leaf_nodes: 31
```

```bash
python -m churn.train model=logreg seed=7 model.params.C=0.5
python -m churn.train --multirun model.params.learning_rate=0.01,0.05,0.1   # simple sweep
```

In `train.yaml`, the `defaults` list says which file to take from each group: `model: gbm` loads
`configs/model/gbm.yaml` into the `model` section. On the command line, `model=logreg` swaps that
whole section for another file, and `model.params.C=0.5` changes one nested value using a dotted
path. `--multirun` with a comma-separated list starts one run per value; a set of runs that
differ in one setting is called a **sweep**.

### A minimal config loader you can run

The mechanism at the heart of all these tools is **layering**: start from defaults, then apply a
file, then environment variables, then command-line overrides, and let each later layer win. The
program below implements it with plain dictionaries so you can see there is no magic.

```python-run
import copy, json

def deep_merge(base, override):
    out = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out

def set_dotted(cfg, dotted, value):
    keys = dotted.split(".")
    d = cfg
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = json.loads(value) if value[:1] in "0123456789[{-tfn" else value

defaults = {"seed": 0, "model": {"name": "gbm", "params": {"learning_rate": 0.1, "max_iter": 100}}}
file_cfg = {"seed": 42, "model": {"params": {"max_iter": 400}}}
env = {"TRAIN__MODEL__PARAMS__LEARNING_RATE": "0.05"}   # pretend environment
cli = ["model.params.max_iter=800", "model.name=gbm_v2"]

cfg = deep_merge(defaults, file_cfg)
for k, v in env.items():
    if k.startswith("TRAIN__"):
        set_dotted(cfg, ".".join(p.lower() for p in k[7:].split("__")), v)
for item in cli:
    key, val = item.split("=", 1)
    set_dotted(cfg, key, val)
print(json.dumps(cfg, indent=2))
```

`deep_merge` copies the base dictionary and walks through the override: where both sides hold a
dictionary under the same key it merges them recursively, and otherwise the override's value
replaces the base's. `set_dotted` turns a dotted path such as `model.params.max_iter` into steps
down the nested dictionaries and sets the last key; `json.loads` converts text such as `"800"`
into the number 800. The four layers are then applied in order. The printed result is:

```text
{
  "seed": 42,
  "model": {
    "name": "gbm_v2",
    "params": {
      "learning_rate": 0.05,
      "max_iter": 800
    }
  }
}
```

Trace one value: `max_iter` starts at 100 in the defaults, the file raises it to 400, and the
command line sets it to 800. The command line was applied last, so 800 wins. `seed` came from the
file, `learning_rate` from the environment and `name` from the command line.

> [!TIP]
> Whatever the mechanism, **log the fully resolved config** with every run (MLflow `log_dict` or
> `log_params`) and bake the serving config's hash into your logs. "Which config produced this model?"
> must always have an answer.

### Config anti-patterns

- Hard-coded paths and URLs in code (`/home/alice/data`).
- Secrets in YAML committed to Git.
- Untyped configs where `"0.1"` (string) silently becomes a learning rate.
- Copies of the same config per environment that drift (`train_prod.yaml`, `train_prod_final2.yaml`).
  Prefer a base plus small overrides.
- Config changes deployed without review: treat config diffs like code diffs (Sculley et al. call
  configuration debt out explicitly).

> [!INTERVIEW]
> "Where do you put the learning rate, the database password and the canary percentage?" —
> Learning rate: versioned experiment config (YAML in Git, logged per run). Password: secret manager,
> injected as env var/K8s Secret. Canary percentage: deployment/rollout config or a feature-flag system,
> changeable without rebuilding the image.

## A debugging session, start to finish

A realistic incident shows how the commands combine. *Symptom: the nightly scoring job on a
**VM** (virtual machine, a rented server) stopped writing predictions.* Read the numbered comments
as the questions an experienced engineer asks, in order. `systemctl` and `journalctl` are the
commands for inspecting services and their logs on modern Linux; `dmesg` shows messages from the
operating system itself.

```bash
# 1. Is it running? Did it run?
systemctl status churn-score.timer churn-score.service      # or: crontab -l ; grep CRON /var/log/syslog
journalctl -u churn-score.service --since "yesterday" | tail -50

# 2. The log ends mid-run with "Killed". Out of memory?
dmesg -T | grep -i -E "oom|killed process" | tail -5
free -h

# 3. Or out of disk?
df -h /data
du -xh /data --max-depth=2 | sort -h | tail -10              # find what grew
find /data/tmp -type f -mtime +7 -name "*.parquet" -print    # stale intermediates (inspect before deleting!)

# 4. Is the input there and fresh?
ls -lh --time-style=long-iso /data/features/dt=$(date -d yesterday +%F)/ | head

# 5. Can the box reach its dependencies?
curl -sS -m 5 -o /dev/null -w "%{http_code} %{time_total}s\n" http://mlflow.internal:5000/health
nc -zv db.internal 5432

# 6. Reproduce by hand with the same environment the job uses
sudo -u svc-churn bash -lc 'cd /opt/churn && set -a && source .env && set +a && churn score --date 2025-01-15'
echo "exit code: $?"
```

The pattern applies to almost any incident: **is it running → what do the logs say → resources
(memory, disk, GPU) → inputs → network → reproduce by hand**. Two root causes turn up again and
again on ML machines. One is the **OOM killer** (out-of-memory killer): when RAM runs out, Linux
picks a process and ends it, leaving only the word "Killed" in the log. The other is a full disk,
filled by checkpoints, logs or temporary files that were never cleaned up.

### Scheduling on a single machine

Before you have an orchestrator, `cron` or systemd timers run recurring jobs:

```bash
# m h dom mon dow  command        (cron uses the machine's local time zone - prefer UTC machines)
0 2 * * *  cd /opt/churn && /opt/churn/.venv/bin/churn score --date $(date -d yesterday +\%F) >> /var/log/churn/score.log 2>&1
```

Cron's weaknesses are exactly what orchestrators fix: no retries, no dependency management, no backfill,
no alert on failure, overlapping runs if a job is slow (`flock -n /tmp/churn.lock <cmd>` prevents
overlap). Treat cron as a stopgap.

### Log rotation and disk hygiene

Unbounded logs fill disks. Either log to stdout and let the platform handle it (containers,
systemd-journald), or configure `logrotate`:

```text
/var/log/churn/*.log {
    daily
    rotate 14
    compress
    missingok
    notifempty
    copytruncate
}
```

## Layered configuration for multiple environments

A recurring design problem: the same service runs in dev, staging and production with mostly identical
settings. Copying whole files leads to drift; the robust pattern is **base + small overrides**, with
secrets injected separately.

```yaml
# configs/serve/base.yaml
model_uri: models:/churn@champion
threshold: 0.5
max_batch: 256
log_level: INFO
feature_store: {timeout_ms: 50, retries: 2}
```

```yaml
# configs/serve/production.yaml  - only what differs
log_level: WARNING
feature_store: {timeout_ms: 30}
```

```yaml
# configs/serve/dev.yaml
model_uri: models:/churn@challenger
log_level: DEBUG
```

At startup the service loads `base.yaml`, deep-merges `${APP_ENV}.yaml`, applies environment-variable
overrides (highest precedence), validates the result against a typed schema, **logs the final config
with secrets redacted**, and exposes a hash of it. On Kubernetes the same layering is done with
Kustomize overlays or Helm values files producing a ConfigMap.

```python-run
import hashlib, json

SECRET_KEYS = {"password", "token", "api_key", "secret"}
def redact(cfg):
    if isinstance(cfg, dict):
        return {k: ("***" if any(s in k.lower() for s in SECRET_KEYS) else redact(v)) for k, v in cfg.items()}
    return cfg

def validate(cfg):
    errors = []
    if not 0 <= cfg["threshold"] <= 1: errors.append("threshold must be in [0, 1]")
    if not isinstance(cfg["max_batch"], int) or cfg["max_batch"] < 1: errors.append("max_batch must be a positive int")
    if cfg["feature_store"]["timeout_ms"] > 100: errors.append("feature_store.timeout_ms exceeds latency budget")
    if cfg["log_level"] not in {"DEBUG", "INFO", "WARNING", "ERROR"}: errors.append("bad log_level")
    return errors

cfg = {"model_uri": "models:/churn@champion", "threshold": 0.5, "max_batch": 256, "log_level": "WARNING",
       "feature_store": {"timeout_ms": 30, "retries": 2}, "mlflow_tracking_password": "hunter2"}
errs = validate(cfg)
print("validation:", "OK" if not errs else errs)
print("effective config:", json.dumps(redact(cfg)))
print("config hash:", hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:10])
bad = dict(cfg, threshold="0.5", max_batch=0)
try:
    print("validation of bad config:", validate(bad))
except TypeError as e:
    print("validation of bad config: type error caught at startup ->", e)
```

`redact` replaces the value of any key whose name contains a secret-looking word with `***`, so
the configuration can be logged safely. `validate` collects a list of problems. The hash on the
third line is a short fingerprint of the whole configuration; two services printing the same hash
are running with identical settings. The output:

```text
validation: OK
effective config: {"model_uri": "models:/churn@champion", "threshold": 0.5, "max_batch": 256, "log_level": "WARNING", "feature_store": {"timeout_ms": 30, "retries": 2}, "mlflow_tracking_password": "***"}
config hash: b68f177a0f
validation of bad config: type error caught at startup -> '<=' not supported between instances of 'int' and 'str'
```

The last line is the instructive one. The bad configuration has `threshold="0.5"`, a piece of
text where a number is expected. This is the classic bug of untyped YAML. Comparing it with 0
raises a `TypeError`, and because the check runs at startup, the service refuses to start. Without
the check, the wrong threshold would have been discovered in production.

### Feature flags vs configuration

Configuration is set at deploy time and changes with a rollout. **Feature flags** change at run time,
per request or per user, without redeploying: kill switches ("disable the new ranker now"), gradual
exposure, and experiment assignment. Keep the two separate: flags that live forever become configuration
debt, so give each flag an owner and an expiry date.

## Summary

- Know your way around files, logs, processes, GPUs, ports and permissions; pipes and `jq` make you fast.
- Exit codes are the contract with CI and orchestrators; use `set -euo pipefail` in scripts.
- Handle SIGTERM gracefully in services and training jobs.
- Separate deployment config (env vars, twelve-factor), secrets (secret manager) and experiment config
  (versioned YAML, logged per run). Validate config with types and fail fast.

## Glossary

- **Shell / bash** - the program that runs the commands you type / the usual Linux shell.
- **ssh** - a command that opens a shell on a remote machine.
- **Pipe (`|`)** - sends one command's output into the next command.
- **stdout / stderr** - a program's normal output channel / its error channel.
- **Exit code** - the number a program returns when it ends; 0 means success.
- **Process / PID** - a running program / its identifying number.
- **Signal (SIGTERM, SIGKILL)** - a message to a process: please stop / stop now.
- **Log** - the running record a program writes about what it does.
- **Port** - a numbered endpoint on which a program accepts network connections.
- **OOM killer** - the Linux mechanism that ends a process when memory runs out.
- **cron** - the built-in scheduler for recurring commands on one machine.
- **Environment variable** - a named value given to a program by its environment at start.
- **Twelve-factor** - a set of rules for deployable services, including "config in the
  environment".
- **Deployment config / experiment config** - settings that differ per environment / per training
  run.
- **Fail fast** - stop at startup when something is wrong, before serving any request.
- **Hydra** - a library that composes layered experiment configuration from YAML files.
- **Layering (overrides)** - applying defaults, files, environment and command line in order, the
  later winning.
- **Redact** - hide secret values before printing or logging.
- **Feature flag** - a switch changed at run time without redeploying.

```quiz
[
  {"q": "What does `set -euo pipefail` do in a bash script?",
   "options": ["Enables GPU usage", "Exits on errors, on unset variables, and when any command in a pipe fails", "Runs the script in parallel", "Suppresses all output"],
   "answer": 1, "explain": "Without it, failing commands in the middle of a script are silently ignored."},
  {"q": "A CI step runs `python train.py`, which prints 'ERROR: data missing' and exits with code 0. What happens?",
   "options": ["CI marks the step failed", "CI marks the step as passed, hiding the failure", "CI retries automatically", "Kubernetes restarts it"],
   "answer": 1, "explain": "CI and orchestrators judge success by exit code; scripts must exit non-zero on failure."},
  {"q": "Which signal does Kubernetes send first when stopping a pod?",
   "options": ["SIGKILL", "SIGTERM", "SIGHUP", "SIGSTOP"],
   "answer": 1, "explain": "SIGTERM first, then SIGKILL after the grace period."},
  {"q": "According to the twelve-factor methodology, where should deployment config live?",
   "options": ["Hard-coded constants", "In environment variables, separate from code", "In the Docker image name", "In comments"],
   "answer": 1, "explain": "Config that varies between deploys belongs in the environment."},
  {"q": "Where should hyperparameters for a training run be stored?",
   "options": ["Only in the engineer's memory", "In versioned config files and logged with each run", "In a Kubernetes Secret", "In the model filename only"],
   "answer": 1, "explain": "Experiment config must be versioned and recorded for reproducibility."},
  {"q": "What does `jq -r '.model_version'` do when applied to JSON log lines?",
   "options": ["Deletes the field", "Extracts the model_version field as raw text from each JSON object", "Validates JSON schema", "Compresses logs"],
   "answer": 1, "explain": "jq queries JSON; -r prints raw strings without quotes."},
  {"q": "What is the advantage of pydantic-settings for service configuration?",
   "options": ["It trains models", "It validates and types environment-based config, failing fast at startup", "It replaces Docker", "It encrypts logs"],
   "answer": 1, "explain": "Invalid config (e.g., a negative batch size) raises at startup rather than at the first request."}
]
```

> **Source:** Martin Kleppmann, *Designing Data-Intensive Applications*, ch. 10 (Batch processing with Unix tools); The Twelve-Factor App (12factor.net), factor III *Config*; Hydra and pydantic-settings documentation; Kubernetes documentation, *Pod lifecycle — termination of pods*; Sculley et al. (2015) on configuration debt.
