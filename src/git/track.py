TRACK = dict(
    id="git",
    title="Git (Pro Git)",
    icon="🌿",
    color="#f05133",
    group="Tools",
    blurb="Git from first commit to object internals: branching, rebasing, remotes, GitHub flow, history surgery and rescue drills, with Python problems that rebuild the commit graph, diff, merge and reflog yourself.",
    sources=[
        "Chacon & Straub, Pro Git, 2nd edition (CC BY-NC-SA 3.0), chapters 1-10",
        "Original material on team workflows, commit conventions and rescue scenarios",
    ],
    modules=[
        dict(
            id="getting-started",
            title="Getting Started",
            summary="What version control is for, how Git's snapshot model and three states work, and how to set Git up.",
            lessons=[
                dict(id="version-control-ideas", title="Version control and how Git thinks", file="01-version-control.md"),
                dict(id="setup-and-help", title="Installing, configuring and getting help", file="02-setup-and-help.md"),
            ],
            problems=[],
        ),
        dict(
            id="git-basics",
            title="Git Basics",
            summary="Creating repositories, staging and committing, reading history, undoing mistakes, remotes, tags and aliases.",
            lessons=[
                dict(id="recording-changes", title="Getting a repository and recording changes", file="03-recording-changes.md"),
                dict(id="viewing-history", title="Viewing history with git log", file="04-history.md"),
                dict(id="undoing-things", title="Undoing things safely", file="05-undoing.md"),
                dict(id="remotes-tags-aliases", title="Remotes, tags and aliases", file="06-remotes-tags-aliases.md"),
            ],
            problems=["git-status-categories", "git-staging-sim", "git-gitignore-match", "git-lcs-diff", "git-log-order", "git-sort-version-tags"],
        ),
        dict(
            id="branching",
            title="Git Branching",
            summary="Branches as movable pointers, merging and conflicts, branch management and workflows, remote branches, and rebasing.",
            lessons=[
                dict(id="branches-in-a-nutshell", title="What a branch really is", file="07-branches.md"),
                dict(id="merging-and-conflicts", title="Merging and resolving conflicts", file="08-merging-conflicts.md"),
                dict(id="branch-workflows-remote", title="Branch management, workflows and remote branches", file="09-branch-workflows-remote.md"),
                dict(id="rebasing", title="Rebasing and its golden rule", file="10-rebasing.md"),
            ],
            problems=["git-is-ancestor", "git-merge-base", "git-three-way-merge"],
        ),
        dict(
            id="git-on-the-server",
            title="Git on the Server",
            summary="The transfer protocols, bare repositories, SSH keys, and the range of self-hosted and hosted options.",
            lessons=[
                dict(id="protocols-and-bare-repos", title="Protocols and putting Git on a server", file="11-protocols.md"),
                dict(id="ssh-keys-and-hosting", title="SSH keys, access control and hosting options", file="12-ssh-keys-hosting.md"),
            ],
            problems=[],
        ),
        dict(
            id="distributed-git",
            title="Distributed Git",
            summary="Collaboration topologies, contributing well-formed work, and the maintainer's toolbox.",
            lessons=[
                dict(id="contributing", title="Distributed workflows and contributing to a project", file="13-contributing.md"),
                dict(id="maintaining", title="Maintaining a project", file="14-maintaining.md"),
            ],
            problems=["git-push-check", "git-apply-hunk", "git-cherry-pick-conflicts"],
        ),
        dict(
            id="github",
            title="GitHub",
            summary="Forks, the pull-request flow, reviews, protected branches, organisations and automation with Actions.",
            lessons=[
                dict(id="github-forks-prs", title="Accounts, forks and the pull-request flow", file="15-github-forks-prs.md"),
                dict(id="github-reviews-automation", title="Reviews, protected branches and Actions", file="16-github-reviews-automation.md"),
            ],
            problems=[],
        ),
        dict(
            id="git-tools",
            title="Git Tools",
            summary="Precise commit selection, interactive staging, stash, signing, search, history rewriting, reset, advanced merging, bisect, submodules and more.",
            lessons=[
                dict(id="revisions-staging-stash", title="Revision selection, interactive staging, stash and clean", file="17-revisions-staging-stash.md"),
                dict(id="sign-search-rewrite", title="Signing, searching and rewriting history", file="18-sign-search-rewrite.md"),
                dict(id="reset-advanced-merging", title="Reset demystified, advanced merging and rerere", file="19-reset-advanced-merging.md"),
                dict(id="debugging-submodules-more", title="Bisect, blame, submodules, bundles, replace and credentials", file="20-debugging-submodules.md"),
            ],
            problems=["git-rev-range", "git-resolve-revision", "git-abbreviate-ids", "git-stash-stack", "git-rebase-todo", "git-reset-modes", "git-bisect-next"],
        ),
        dict(
            id="customizing-git",
            title="Customising Git",
            summary="Configuration that matters, per-path attributes, client and server hooks, and a worked policy-enforcement example.",
            lessons=[
                dict(id="config-and-attributes", title="Configuration and attributes", file="21-config-attributes.md"),
                dict(id="hooks-and-policy", title="Hooks and enforcing policy", file="22-hooks-policy.md"),
            ],
            problems=[],
        ),
        dict(
            id="git-and-other-systems",
            title="Git and Other Systems",
            summary="Using Git as a client for other version-control systems and migrating a project's history into Git.",
            lessons=[
                dict(id="other-systems", title="Bridging to and migrating from other systems", file="23-other-systems.md"),
            ],
            problems=[],
        ),
        dict(
            id="git-internals",
            title="Git Internals",
            summary="The content-addressed object store, references, packfiles, refspecs, the wire protocols, and recovery tools.",
            lessons=[
                dict(id="objects", title="Objects: blobs, trees, commits and tags", file="24-objects.md"),
                dict(id="refs-and-packfiles", title="References and packfiles", file="25-refs-packfiles.md"),
                dict(id="refspec-and-transfer", title="The refspec and transfer protocols", file="26-refspec-transfer.md"),
                dict(id="maintenance-recovery", title="Maintenance and data recovery", file="27-maintenance-recovery.md"),
            ],
            problems=["git-blob-id", "git-tree-commit-id", "git-parse-refspec"],
        ),
        dict(
            id="team-workflows",
            title="Team Workflows in Practice",
            summary="Choosing a branching model and merge strategy, writing commits and reviews people thank you for, and scaling to monorepos and large files.",
            lessons=[
                dict(id="branching-models", title="Trunk-based, GitFlow, GitHub flow and merge strategies", file="28-branching-models.md"),
                dict(id="conventions-review-scale", title="Commit conventions, review etiquette, monorepos and large files", file="29-conventions-review-scale.md"),
            ],
            problems=["git-conventional-commit", "git-squash-commits"],
        ),
        dict(
            id="interview-rescue",
            title="Git Interview and Rescue Scenarios",
            summary="Worked command sequences for the mistakes everyone makes, and clear explanations for the questions interviewers ask.",
            lessons=[
                dict(id="rescue-scenarios", title="Rescue drills: wrong branch, pushed secret, undo, recover", file="30-rescue-scenarios.md"),
                dict(id="interview-explanations", title="Interview walkthroughs: conflicts, bisect, merge vs rebase", file="31-interview-explanations.md"),
            ],
            problems=["git-reflog-recover"],
        ),
    ],
)
