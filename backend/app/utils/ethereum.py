"""
CryptoTrace AI — Ethereum Forensics Utilities

Features:
- Pure-Python Keccak-256 implementation (zero external C-extension dependencies).
- EIP-55 checksum address validation and normalization.
- 32-byte 0x-prefixed transaction hash validation and normalization.
- Exact decimal cryptocurrency arithmetic (strictly no floating-point arithmetic).
- Deterministic canonical JSON serialization and SHA-256 integrity hashing.
"""
from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal
from typing import Any, Optional

# ── Keccak-256 Implementation (FIPS 202 / original Keccak sponge) ────────────

_KECCAK_ROUND_CONSTANTS = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
    0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
    0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
    0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
    0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]

_KECCAK_ROTATION_SHIFTS = [
    [0, 36, 3, 41, 18],
    [1, 44, 10, 45, 2],
    [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39, 8, 14],
]


def keccak_256(data: bytes) -> bytes:
    """
    Compute Keccak-256 hash according to the original Keccak specification
    used by Ethereum (rate = 1088 bits / 136 bytes, padding 0x01 ... 0x80).
    """
    state = [0] * 25
    rate = 136

    # Padding: 0x01 ... 0x80
    padded = bytearray(data)
    padded.append(0x01)
    while len(padded) % rate != (rate - 1):
        padded.append(0x00)
    padded.append(0x80)

    mask = 0xFFFFFFFFFFFFFFFF

    for block_offset in range(0, len(padded), rate):
        for i in range(17):
            chunk = int.from_bytes(
                padded[block_offset + i * 8 : block_offset + (i + 1) * 8], "little"
            )
            state[i] ^= chunk

        for round_idx in range(24):
            # Theta step
            c = [
                state[x] ^ state[x + 5] ^ state[x + 10] ^ state[x + 15] ^ state[x + 20]
                for x in range(5)
            ]
            d = [
                c[(x - 1) % 5] ^ (((c[(x + 1) % 5] << 1) | (c[(x + 1) % 5] >> 63)) & mask)
                for x in range(5)
            ]
            for x in range(5):
                for y in range(5):
                    state[x + y * 5] ^= d[x]

            # Rho and Pi steps
            b = [0] * 25
            for x in range(5):
                for y in range(5):
                    shift = _KECCAK_ROTATION_SHIFTS[x][y]
                    val = state[x + y * 5]
                    b[y + ((2 * x + 3 * y) % 5) * 5] = (
                        ((val << shift) | (val >> (64 - shift))) & mask if shift else val
                    )

            # Chi step
            for x in range(5):
                for y in range(5):
                    state[x + y * 5] = b[x + y * 5] ^ (
                        (~b[(x + 1) % 5 + y * 5]) & b[(x + 2) % 5 + y * 5]
                    )

            # Iota step
            state[0] ^= _KECCAK_ROUND_CONSTANTS[round_idx]

    out = bytearray()
    for i in range(4):
        out.extend(state[i].to_bytes(8, "little"))
    return bytes(out)


# ── EIP-55 Address Checksum & Validation ──────────────────────────────────────

_HEX_ADDRESS_REGEX = re.compile(r"^0x[0-9a-fA-F]{40}$")
_HEX_TX_HASH_REGEX = re.compile(r"^0x[0-9a-fA-F]{64}$")


def to_checksum_address(address: str) -> str:
    """
    Format a 20-byte hexadecimal address into its EIP-55 mixed-case checksum format.
    """
    clean_addr = address.lower().replace("0x", "")
    if len(clean_addr) != 40 or not all(c in "0123456789abcdef" for c in clean_addr):
        raise ValueError(f"Invalid Ethereum address length or characters: '{address}'")

    hash_hex = keccak_256(clean_addr.encode("ascii")).hex()
    checksummed = ["0x"]
    for i, char in enumerate(clean_addr):
        if char in "0123456789":
            checksummed.append(char)
        else:
            # If the i-th nibble of hash is >= 8, uppercase the letter
            if int(hash_hex[i], 16) >= 8:
                checksummed.append(char.upper())
            else:
                checksummed.append(char.lower())
    return "".join(checksummed)


def is_valid_ethereum_address(address: str) -> bool:
    """
    Validate that an address is a valid 40-hex character Ethereum address.
    - If all-lowercase or all-uppercase: valid.
    - If mixed-case: strictly requires valid EIP-55 checksum.
    """
    if not isinstance(address, str) or not _HEX_ADDRESS_REGEX.match(address):
        return False

    hex_part = address[2:]
    # If all digits and lowercase letters or all digits and uppercase letters
    if hex_part == hex_part.lower() or hex_part == hex_part.upper():
        return True

    # Mixed-case requires EIP-55 checksum match
    try:
        return to_checksum_address(hex_part) == address
    except ValueError:
        return False


def validate_and_normalize_address(address: str) -> str:
    """
    Validate and return the EIP-55 checksum normalized address.
    Raises ValueError if invalid address or invalid mixed-case checksum.
    """
    if not isinstance(address, str) or not _HEX_ADDRESS_REGEX.match(address):
        raise ValueError(
            f"Invalid Ethereum address format: '{address}'. "
            "Must be 0x followed by exactly 40 hexadecimal characters."
        )

    hex_part = address[2:]
    is_lower = hex_part == hex_part.lower()
    is_upper = hex_part == hex_part.upper()

    checksummed = to_checksum_address(hex_part)

    # If mixed case, enforce checksum correctness
    if not is_lower and not is_upper:
        if address != checksummed:
            raise ValueError(
                f"Invalid EIP-55 checksum for mixed-case address '{address}'. "
                f"Expected '{checksummed}'."
            )

    return checksummed


def is_valid_tx_hash(tx_hash: str) -> bool:
    """Validate that a transaction hash is 0x followed by exactly 64 hex characters (32 bytes)."""
    return bool(isinstance(tx_hash, str) and _HEX_TX_HASH_REGEX.match(tx_hash))


def validate_and_normalize_tx_hash(tx_hash: str) -> str:
    """Validate and normalize a 32-byte transaction hash to lowercase 0x hex format."""
    if not is_valid_tx_hash(tx_hash):
        raise ValueError(
            f"Invalid Ethereum transaction hash: '{tx_hash}'. "
            "Must be 0x followed by exactly 64 hexadecimal characters (32 bytes)."
        )
    return "0x" + tx_hash[2:].lower()


# ── Exact Decimal Arithmetic ──────────────────────────────────────────────────

WEI_IN_ETHER = Decimal("1000000000000000000")  # 10^18


def wei_to_ether(wei_value: int | str) -> Decimal:
    """
    Convert wei (integer or string) to Ether using exact Decimal arithmetic.
    Never uses binary floating-point representation.
    """
    try:
        dec_wei = Decimal(str(wei_value).strip())
    except Exception as exc:
        raise ValueError(f"Cannot convert wei value '{wei_value}' to Decimal: {exc}")

    if dec_wei < 0:
        raise ValueError(f"Negative wei amount is invalid: '{wei_value}'")

    return dec_wei / WEI_IN_ETHER


def raw_to_token_amount(raw_value: int | str, decimals: Optional[int]) -> Optional[Decimal]:
    """
    Convert raw token units to human-readable token amount using token's exact decimal places.
    If decimals is None, returns None to avoid assuming 18 decimals.
    """
    if decimals is None:
        return None

    if decimals < 0 or decimals > 36:
        raise ValueError(f"Invalid token decimals value: {decimals}")

    try:
        dec_raw = Decimal(str(raw_value).strip())
    except Exception as exc:
        raise ValueError(f"Cannot convert token raw amount '{raw_value}' to Decimal: {exc}")

    if dec_raw < 0:
        raise ValueError(f"Negative token amount is invalid: '{raw_value}'")

    divisor = Decimal(10) ** decimals
    return dec_raw / divisor


# ── Canonical JSON & Integrity Hashing ────────────────────────────────────────

def canonical_json_dumps(data: Any) -> str:
    """
    Deterministic canonical JSON serialization:
    - Keys sorted alphabetically.
    - Compact separators (no redundant whitespace).
    - Ensure ascii encoding.
    """
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    )


def compute_integrity_hash(data: Any) -> str:
    """
    Compute SHA-256 integrity hash of the canonical JSON representation.

    Scope & Limitation:
    This integrity hash guarantees tamper-detection of the exact stored representation
    in the CryptoTrace database. It does NOT independently verify that the external
    provider's original claims or response data are truthful.
    """
    canonical_str = canonical_json_dumps(data)
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
