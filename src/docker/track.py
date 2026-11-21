import pathlib as _pl
import re as _re

_HERE = _pl.Path(__file__).parent
_DEFINED = set()
for _f in (_HERE / "problems").glob("*.py"):
    _DEFINED.update(_re.findall(r'^\s*id="(docker-[a-z0-9-]+)"', _f.read_text(encoding="utf-8"), _re.M))


def _m(mid, title, summary, lessons, problems=()):
    return dict(
        id=mid, title=title, summary=summary,
        lessons=[dict(id=i, title=t, file=f) for i, t, f in lessons if (_HERE / "lessons" / f).exists()],
        problems=[p for p in problems if p in _DEFINED],
    )


TRACK = dict(
    id="docker",
    title="Docker & Containers",
    icon="🐳",
    color="#1d63ed",
    group="Engineering Practice",
    blurb="Containers from the kernel up: namespaces, cgroups and layered images, Dockerfiles and the build "
          "cache, registries, storage, Compose, health checks, observability, Swarm and Kubernetes, safe "
          "upgrades, secrets, CI builds, multi-architecture images, security hardening, ML/GPU images and "
          "worked interview answers.",
    sources=[
        "Elton Stoneman, Learn Docker in a Month of Lunches (Manning, 2020), ch. 1-21",
        "Official docs: docs.docker.com (Dockerfile reference, Compose file reference, Engine, Build, Swarm)",
        "Official docs: kubernetes.io, prometheus.io, NVIDIA Container Toolkit, astral.sh/uv",
    ],
    modules=[
        _m("containers-basics", "1. Understanding Containers and Images",
           "What a container really is inside the kernel, how it differs from a VM, and how to run, inspect and stop one.",
           [("what-is-a-container", "What a container is: namespaces, cgroups and layered filesystems", "01-what-is-a-container.md"),
            ("running-containers", "Running, inspecting and stopping containers", "02-running-containers.md")],
           ["docker-port-mappings", "docker-image-size-dedup"]),
        _m("building-images", "2. Building Images",
           "Dockerfile instructions, layers and the build cache, the build context, and multi-stage builds from source.",
           [("dockerfile-instructions", "Dockerfile instructions, one by one", "03-dockerfile-instructions.md"),
            ("layers-cache-context", "Layers, the build cache, the context and .dockerignore", "04-layers-cache-context.md"),
            ("multi-stage-builds", "Multi-stage builds: packaging Python, Node and compiled apps from source", "05-multi-stage-builds.md")],
           ["docker-cmd-entrypoint", "docker-cache-invalidation", "docker-reorder-instructions",
            "docker-dockerignore", "docker-multistage-stages"]),
        _m("sharing-images", "3. Sharing Images",
           "Registries, image references, tags versus digests, and a versioning strategy people can trust.",
           [("registries-tags-digests", "Registries, image references, tags and digests", "06-registries-tags-digests.md"),
            ("versioning-strategy", "Tagging and versioning strategy, and running your own registry", "07-versioning-strategy.md")],
           ["docker-parse-image-ref", "docker-semver-tags"]),
        _m("storage", "4. Storage",
           "The container writable layer, copy-on-write, volumes, bind mounts and tmpfs.",
           [("writable-layer", "The writable layer and copy-on-write", "08-writable-layer.md"),
            ("volumes-bind-mounts", "Volumes, bind mounts and tmpfs", "09-volumes-bind-mounts.md")],
           ["docker-union-fs-lookup", "docker-mount-spec"]),
        _m("compose", "5. Multi-Container Apps with Docker Compose",
           "Services, networks and DNS, start order, environment and configuration, and override files per environment.",
           [("compose-basics", "Compose fundamentals: services, projects and start order", "10-compose-basics.md"),
            ("compose-networking", "Container networking and DNS on user-defined networks", "11-compose-networking.md"),
            ("compose-environments", "Environment, configuration and override files", "12-compose-environments.md")],
           ["docker-compose-start-order", "docker-dns-resolution", "docker-env-substitution", "docker-compose-merge"]),
        _m("reliability", "6. Reliability",
           "Health checks, dependency checks and restart policies: letting the platform notice and repair failure.",
           [("health-checks", "Health checks and dependency checks", "13-health-checks.md"),
            ("restart-policies", "Restart policies and self-healing containers", "14-restart-policies.md")],
           ["docker-health-state", "docker-restart-policy"]),
        _m("observability", "7. Observability",
           "Container logs and logging patterns, metrics with Prometheus, and dashboards that answer real questions.",
           [("container-logs", "Container logs, logging drivers and logging patterns", "15-container-logs.md"),
            ("metrics-prometheus", "Metrics with Prometheus and dashboards with Grafana", "16-metrics-prometheus.md")],
           ["docker-log-rotation"]),
        _m("orchestration", "8. Orchestration in Production",
           "Clusters, desired state and scheduling with Docker Swarm, then the same ideas in Kubernetes.",
           [("swarm", "Orchestration with Docker Swarm", "17-swarm.md"),
            ("kubernetes-comparison", "Kubernetes for Docker users: pods, deployments, services", "18-kubernetes-comparison.md")],
           ["docker-resource-accounting"]),
        _m("releases-config", "9. Upgrades, Rollbacks, Configuration and Secrets",
           "Rolling updates and automatic rollback, config and secret objects, and application configuration patterns.",
           [("rolling-updates", "Rolling updates and rollbacks", "19-rolling-updates.md"),
            ("configs-secrets", "Configs and secrets", "20-configs-secrets.md"),
            ("app-config-patterns", "Application configuration patterns for containers", "21-app-config-patterns.md")],
           ["docker-rolling-update", "docker-secret-audit"]),
        _m("build-infra", "10. Build Infrastructure",
           "CI pipelines whose only dependency is Docker, secure remote engines and continuous deployment, "
           "and images that run on both Intel and Arm.",
           [("ci-pipelines", "Build infrastructure and CI pipelines with Docker", "22-ci-pipelines.md"),
            ("remote-engines-cd", "Remote engines, secure access, contexts and continuous deployment", "22a-remote-engines-cd.md"),
            ("multi-arch", "Multi-architecture images", "23-multi-arch.md")],
           ["docker-platform-select"]),
        _m("security-optimisation", "11. Security and Image Optimisation",
           "Least privilege, non-root users, capabilities, read-only filesystems, scanning, and smaller, faster images.",
           [("container-security", "Container security: least privilege in practice", "24-container-security.md"),
            ("optimising-images", "Optimising images for size, speed and security", "25-optimising-images.md")],
           ["docker-lint-dockerfile", "docker-scan-triage"]),
        _m("architecture-patterns", "12. Architecture Patterns Around Containers",
           "Reverse proxies in front of containers and asynchronous messaging between them.",
           [("reverse-proxy", "Reverse proxies in front of containers", "26-reverse-proxy.md"),
            ("async-messaging", "Asynchronous messaging between containers", "27-async-messaging.md")],
           ["docker-proxy-route"]),
        _m("ml-python", "13. Docker for ML and Python Services",
           "CUDA base images, model weights and layer caching, uv and pip cache mounts, slim FastAPI images, GPU access.",
           [("ml-images", "ML images: CUDA bases, dependencies and model weights", "28-ml-images.md"),
            ("fastapi-gpu", "Slim FastAPI images and GPU access at run time", "29-fastapi-gpu.md")]),
        _m("interview", "14. Docker Interview Essentials",
           "Worked answers to the questions that come up again and again, and a method for debugging a container that will not start.",
           [("interview-core", "Core interview questions with worked answers", "30-interview-core.md"),
            ("interview-debugging", "Shrinking images and debugging containers that will not start", "31-interview-debugging.md")]),
    ],
)
