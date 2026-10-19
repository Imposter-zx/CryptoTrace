"""
Unit tests for Ethereum validation, decimal arithmetic, and integrity hashing utilities.
"""
from __future__ import annotations

import pytest
from decimal import Decimal

from app.utils.ethereum import (
    canonical_json_dumps,
    compute_integrity_hash,
    is_valid_ethereum_address,
    is_valid_tx_hash,
    keccak_256,
    raw_to_token_amount,
    to_checksum_address,
    validate_and_normalize_address,
    validate_and_normalize_tx_hash,
    wei_to_ether,
)


# ── keccak_256 ────────────────────────────────────────────────────────────────

class TestKeccak256:
    def test_empty_input_hash(self):
        """keccak256("") == 0xc5d246...  (well-known Ethereum test vector)."""
        result = keccak_256(b"")
        assert result.hex() == "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"

    def test_hello_world(self):
        """keccak256(b"hello") must equal the known Ethereum hash."""
        result = keccak_256(b"hello")
        assert result.hex() == "1c8aff950685c2ed4bc3174f3472287b56d9517b9c948127319a09a7a36deac8"

    def test_bytes_length(self):
        assert len(keccak_256(b"test")) == 32


# ── EIP-55 checksum address ───────────────────────────────────────────────────

class TestChecksumAddress:
    """Test all four official EIP-55 test vectors."""

    def test_eip55_vector_1(self):
        addr = "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"
        assert to_checksum_address(addr.lower()) == addr

    def test_eip55_vector_2(self):
        addr = "0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359"
        assert to_checksum_address(addr.lower()) == addr

    def test_eip55_vector_3(self):
        addr = "0xdbF03B407c01E7cD3CBea99509d93f8DDDC8C6FB"
        assert to_checksum_address(addr.lower()) == addr

    def test_eip55_vector_4(self):
        addr = "0xD1220A0cf47c7B9Be7A2E6BA89F429762e7b9aDb"
        assert to_checksum_address(addr.lower()) == addr


# ── Address validation ────────────────────────────────────────────────────────

class TestAddressValidation:
    def test_valid_lowercase(self):
        assert is_valid_ethereum_address("0x" + "a" * 40) is True

    def test_valid_uppercase(self):
        assert is_valid_ethereum_address("0x" + "A" * 40) is True

    def test_valid_mixed_checksum(self):
        # Correct EIP-55 checksum address passes
        addr = "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"
        assert is_valid_ethereum_address(addr) is True

    def test_invalid_mixed_wrong_checksum(self):
        # Deliberately flipped checksum character must fail
        bad = "0x5aaeb6053F3E94C9b9A09f33669435E7Ef1BeAed"
        assert is_valid_ethereum_address(bad) is False

    def test_too_short(self):
        assert is_valid_ethereum_address("0x" + "a" * 39) is False

    def test_too_long(self):
        assert is_valid_ethereum_address("0x" + "a" * 41) is False

    def test_no_0x_prefix(self):
        assert is_valid_ethereum_address("a" * 40) is False

    def test_empty_string(self):
        assert is_valid_ethereum_address("") is False

    def test_validate_and_normalize_returns_checksum(self):
        raw = "0x" + "b" * 40
        normalized = validate_and_normalize_address(raw)
        assert normalized.startswith("0x")
        assert len(normalized) == 42

    def test_validate_and_normalize_raises_on_invalid(self):
        with pytest.raises(ValueError, match="Invalid Ethereum address"):
            validate_and_normalize_address("not-an-address")


# ── Transaction hash validation ───────────────────────────────────────────────

class TestTxHashValidation:
    def test_valid_hash(self):
        assert is_valid_tx_hash("0x" + "a" * 64) is True

    def test_uppercase_valid(self):
        assert is_valid_tx_hash("0x" + "A" * 64) is True

    def test_too_short(self):
        assert is_valid_tx_hash("0x" + "a" * 63) is False

    def test_too_long(self):
        assert is_valid_tx_hash("0x" + "a" * 65) is False

    def test_no_0x(self):
        assert is_valid_tx_hash("a" * 64) is False

    def test_invalid_hex_chars(self):
        assert is_valid_tx_hash("0x" + "g" * 64) is False

    def test_normalize_lowercases(self):
        upper = "0x" + "A" * 64
        result = validate_and_normalize_tx_hash(upper)
        assert result == "0x" + "a" * 64

    def test_normalize_raises_on_invalid(self):
        with pytest.raises(ValueError):
            validate_and_normalize_tx_hash("not-a-hash")


# ── Wei/Ether decimal arithmetic ──────────────────────────────────────────────

class TestWeiToEther:
    def test_zero(self):
        assert wei_to_ether("0") == Decimal("0")

    def test_one_ether(self):
        one_ether_wei = "1000000000000000000"
        assert wei_to_ether(one_ether_wei) == Decimal("1")

    def test_fractional_ether(self):
        half_ether = "500000000000000000"
        assert wei_to_ether(half_ether) == Decimal("0.5")

    def test_1_gwei(self):
        assert wei_to_ether("1000000000") == Decimal("0.000000001")

    def test_no_float_type(self):
        result = wei_to_ether("1000000000000000000")
        assert isinstance(result, Decimal)
        assert not isinstance(result, float)

    def test_large_amount(self):
        large = str(21_000_000 * 10 ** 18)  # 21M ETH in wei
        result = wei_to_ether(large)
        assert result == Decimal("21000000")


# ── ERC-20 token amount normalization ─────────────────────────────────────────

class TestRawToTokenAmount:
    def test_18_decimals(self):
        # 1.5 USDC-like with 18 decimals
        raw = "1500000000000000000"
        result = raw_to_token_amount(raw, 18)
        assert result == Decimal("1.5")

    def test_6_decimals_usdc(self):
        # 1.0 USDC with 6 decimals
        raw = "1000000"
        result = raw_to_token_amount(raw, 6)
        assert result == Decimal("1")

    def test_zero_decimals(self):
        raw = "42"
        result = raw_to_token_amount(raw, 0)
        assert result == Decimal("42")

    def test_unknown_decimals_returns_none(self):
        result = raw_to_token_amount("1000000", None)
        assert result is None

    def test_no_float_type(self):
        result = raw_to_token_amount("1000000", 6)
        assert isinstance(result, Decimal)
        assert not isinstance(result, float)

    def test_2_decimals(self):
        raw = "100"
        result = raw_to_token_amount(raw, 2)
        assert result == Decimal("1")


# ── Canonical JSON and integrity hash ─────────────────────────────────────────

class TestCanonicalJson:
    def test_key_ordering(self):
        data = {"z": 1, "a": 2, "m": 3}
        result = canonical_json_dumps(data)
        assert result == '{"a":2,"m":3,"z":1}'

    def test_deterministic(self):
        data = {"b": 99, "a": 1}
        assert canonical_json_dumps(data) == canonical_json_dumps(data)

    def test_nested_sorted(self):
        data = {"outer": {"z": 1, "a": 2}}
        result = canonical_json_dumps(data)
        assert '"a":2' in result
        assert result.index('"a":2') < result.index('"z":1')


class TestIntegrityHash:
    def test_returns_hex_string(self):
        result = compute_integrity_hash({"key": "value"})
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex is 64 chars

    def test_deterministic(self):
        data = {"a": 1, "b": 2}
        assert compute_integrity_hash(data) == compute_integrity_hash(data)

    def test_differs_for_different_data(self):
        h1 = compute_integrity_hash({"key": "value1"})
        h2 = compute_integrity_hash({"key": "value2"})
        assert h1 != h2
