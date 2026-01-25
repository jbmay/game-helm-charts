# Logan's Helm Charts

Helm charts for game servers and services, published to GitHub Container Registry (GHCR).

## Installation

Charts are published as OCI artifacts to GHCR. Install directly using Helm 3.8+:

```bash
# Install a chart
helm install my-release oci://ghcr.io/loganintech/helm-charts/voyagers-of-nera --version 0.1.0

# Install with custom values
helm install my-release oci://ghcr.io/loganintech/helm-charts/terraria \
  --set persistence.worlds.enabled=true \
  --set terraria.world.worldsize=large

# Upgrade an existing release
helm upgrade my-release oci://ghcr.io/loganintech/helm-charts/voyagers-of-nera --version 0.2.0
```

## Available Charts

| Chart | Description | Version |
|-------|-------------|---------|
| [starrupture](charts/starrupture) | StarRupture dedicated server (Proton) | 0.1.0 |
| [voyagers-of-nera](charts/voyagers-of-nera) | Voyagers of Nera dedicated server (Proton) | 0.1.0 |
| [enshrouded](charts/enshrouded) | Enshrouded dedicated server | - |
| [factorio](charts/factorio) | Factorio dedicated server | - |
| [palworld](charts/palworld) | Palworld dedicated server | - |
| [terraria](charts/terraria) | Terraria dedicated server with TShock | 0.4.15 |
| [core-keeper-dedicated-server](charts/core-keeper-dedicated-server) | Core Keeper dedicated server | 0.0.1 |
| [hkmp](charts/hkmp) | Hollow Knight Multiplayer server | - |

## Using with Pulumi

You can reference these charts in Pulumi using OCI URLs:

```go
release, err := helmv3.NewRelease(ctx, "voyagers", &helmv3.ReleaseArgs{
    Chart:     pulumi.String("oci://ghcr.io/loganintech/helm-charts/voyagers-of-nera"),
    Version:   pulumi.String("0.1.0"),
    Namespace: namespace.Metadata.Name(),
    Values: pulumi.Map{
        // ... your values
    },
})
```

## Development

### Adding a new chart

1. Create directory under `charts/`:
   ```bash
   mkdir -p charts/my-game/templates
   ```

2. Create `Chart.yaml`:
   ```yaml
   apiVersion: v2
   appVersion: "latest"
   description: My game server
   name: my-game
   version: 0.1.0
   dependencies:
     - name: common
       repository: https://library-charts.k8s-at-home.com
       version: 4.5.2
   ```

3. Create templates and values.yaml

4. Push to main branch - the workflow will automatically publish to GHCR

### Local testing

```bash
# Lint chart
helm lint charts/my-game

# Template locally
cd charts/my-game
helm dependency update
helm template test .

# Install locally
helm install test charts/my-game --dry-run --debug
```

## CI/CD

The [publish-charts.yml](.github/workflows/publish-charts.yml) workflow:
- Triggers on changes to `charts/` directory
- Detects which charts changed
- Packages and pushes to GHCR as OCI artifacts
- Validates charts on PRs (lint + template)
