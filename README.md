# Game Server Helm Charts

Helm charts for game servers and services maintained at
[jbmay/game-helm-charts](https://github.com/jbmay/game-helm-charts) and
published to GitHub Container Registry (GHCR).

## Installation

Charts are published as OCI artifacts to GHCR. Install directly using Helm 3.8+:

```bash
# Install a chart
helm install my-release oci://ghcr.io/jbmay/helm-charts/terraria --version 0.9.1

# Install with custom values
helm install my-release oci://ghcr.io/jbmay/helm-charts/terraria \
  --set persistence.worlds.enabled=true \
  --set terraria.serverSettings.worldsize=large

# Upgrade an existing release
helm upgrade my-release oci://ghcr.io/jbmay/helm-charts/terraria --version 0.9.1
```

## Available Charts

| Chart | Description | Version |
|-------|-------------|---------|
| [factorio](charts/factorio) | Factorio dedicated server | 1.3.2 |
| [palworld](charts/palworld) | Palworld dedicated server | 0.0.4 |
| [terraria](charts/terraria) | Terraria dedicated server with TShock and OCI world import | 0.9.1 |
| [core-keeper-dedicated-server](charts/core-keeper-dedicated-server) | Core Keeper dedicated server | 0.0.4 |
| [hkmp](charts/hkmp) | Hollow Knight Multiplayer server | 0.0.6 |

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

4. Open a pull request targeting `gh-pages` to validate the chart, then merge
   it to publish the chart to GHCR.

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

- [validate-charts.yml](.github/workflows/validate-charts.yml) detects and
  validates changed charts in pull requests.
- [release-charts.yml](.github/workflows/release-charts.yml) packages every
  current chart version that is not already published and pushes it to GHCR
  after changes merge to `gh-pages`.
