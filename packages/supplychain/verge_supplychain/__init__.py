"""Supply-chain integrity: signed bundles, SBOM, cosign/minisign verification."""

from .bundle import inspect_bundle, verify_bundle

__all__ = ["inspect_bundle", "verify_bundle"]
