# Terraria Helm chart

This chart runs either the TShock or vanilla Terraria server and can optionally
import existing worlds from an OCI image before the server starts.

## Importing worlds from an image

The chart mounts the configured OCI image as a read-only Kubernetes image
volume. An init container then copies its contents into the writable worlds
volume. The server never writes to the source image.

Image volumes require Kubernetes 1.31 or newer and container-runtime support.
Before Kubernetes 1.36, the `ImageVolume` feature gate may need to be enabled.

Package world files under `/worlds` in a minimal image. For example:

```dockerfile
FROM scratch
COPY --chmod=0644 MyWorld.wld /worlds/MyWorld.wld
COPY --chmod=0644 MyWorld.wld.bak /worlds/MyWorld.wld.bak
```

Build and push that image, then configure the chart using an immutable digest:

```yaml
terraria:
  serverSettings:
    worldname: MyWorld

persistence:
  worlds:
    enabled: true
    size: 1Gi

worldImport:
  enabled: true
  image:
    reference: ghcr.io/example/terraria-worlds@sha256:0123456789abcdef
    pullPolicy: IfNotPresent
  sourcePath: /worlds
  overwrite: false
```

The source directory must contain at least one `.wld` file. Related files and
subdirectories are copied as well. By default, existing destination paths are
preserved. Setting `overwrite: true` replaces matching paths.

Each unique combination of image reference, source path, and overwrite setting
is imported once per worlds volume. The chart records completed imports under
`/worlds/.world-imports`. To import a new revision, update the image reference;
digest references are recommended because mutable tags do not identify content
changes reliably.

Private world images use the pod-level `imagePullSecrets` setting, just like the
server image.
