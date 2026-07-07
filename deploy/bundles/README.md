# Signed release bundles (spec §14.6, IEC 62443 SBOM)

Air-gapped `verge upgrade` ships a directory like `demo-0.3.0/`:

| File | Purpose |
|------|---------|
| `bundle.manifest.json` | Version, build time, component SHA-256 digests |
| `bundle.manifest.sig.json` | Detached signature (dev HMAC or cosign metadata) |
| `sbom.cdx.json` | CycloneDX SBOM |
| `components/` | Image tags, registry snapshots, migration bundles |

## Dev signing (pilot)

```bash
export VERGE_BUNDLE_HMAC_SECRET=verge-dev-bundle-secret
python scripts/sign_bundle.py deploy/bundles/demo-0.3.0
verge bundle verify --root deploy/bundles/demo-0.3.0
```

## Production (cosign)

```bash
cosign sign-blob --key cosign.key --output-signature bundle.manifest.cosign.sig bundle.manifest.json
```

Set `bundle.manifest.sig.json` to:

```json
{"algorithm": "cosign", "signatureFile": "bundle.manifest.cosign.sig", "publicKeyFile": "cosign.pub"}
```

Install with `VERGE_BUNDLE_ROOT=/opt/verge/bundle` and `VERGE_BUNDLE_PUBLIC_KEY=cosign.pub`.
