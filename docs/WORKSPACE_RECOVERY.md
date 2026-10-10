# Portable workspace backup and restore

Projects can outlive their cloud container or coding agent session.

```bash
gep workspace-backup --repo /path/to/project --archive /persistent/storage/project.tar.gz
gep workspace-restore --archive /persistent/storage/project.tar.gz --destination /new/project --approve
```

The snapshot includes current tracked and untracked, non-ignored regular files
(including uncommitted edits) with SHA-256 hashes. Files like `.env`, API token
stores and Git ignored files are excluded. By default the archive is limited to
50 MiB; use durable object storage separately for model weights and datasets.
Snapshots must be saved outside the working repo and uploaded to truly persistent
storage before deleting a rented container.

Restore refuses to overwrite existing files and checks hashes and paths.
The destination is a file snapshot, not a configured Git repository or
reproducible runtime: use Git clone, dependency locks and a container image to
rebuild a working environment. Snapshots cannot catch every possible secret,
so review before uploading.
