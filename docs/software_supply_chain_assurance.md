# Software Supply Chain Assurance Guide

This module covers software build artifacts attestation audits and bill of materials (SBOM) parsing verification.

## Attestation digest verification

Verification compares artifact digests against SHA-256 signatures, running completely offline without dynamic external transparencies query networks.

## SBOM registries

Supports standard CycloneDX, SPDX, and internal JSON formats metadata schema parses. All processing is static and executes no code binaries.
