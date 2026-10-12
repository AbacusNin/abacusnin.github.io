"""Synthetic positive, benign, near-miss, and bounds tests."""
from hashlib import sha256
from pathlib import Path
import struct
import unittest

from embedded_bpf_inventory import inspect_elf, review


def make_elf(machine, sections):
    names = b"\0"
    records = []
    for label, content in sections:
        name_off = len(names)
        names += label.encode("ascii") + b"\0"
        records.append((name_off, content))
    string_name = len(names)
    names += b".shstrtab\0"
    output = bytearray(64)
    headers = [(0, 0, 0)]
    for name_off, content in records:
        offset = len(output)
        output.extend(content)
        headers.append((name_off, offset, len(content)))
    string_offset = len(output)
    output.extend(names)
    headers.append((string_name, string_offset, len(names)))
    while len(output) % 8:
        output.append(0)
    shoff = len(output)
    for index, (name_off, offset, size) in enumerate(headers):
        typ = 0 if index == 0 else (3 if index == len(headers) - 1 else 1)
        output.extend(struct.pack("<IIQQQQIIQQ", name_off, typ, 0, 0,
                                  offset, size, 0, 0, 1, 0))
    output[:16] = b"\x7fELF\x02\x01\x01" + b"\0" * 9
    struct.pack_into("<HHIQQQIHHHHHH", output, 16, 1, machine, 1, 0, 0,
                     shoff, 0, 64, 0, 0, 64, len(headers), len(headers) - 1)
    return bytes(output)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(__file__).with_name("_synthetic_test.elf")

    def tearDown(self):
        self.path.unlink(missing_ok=True)

    def test_positive_and_allowlist(self):
        inner = make_elf(247, [("tracepoint/raw_syscalls/sys_enter", b"\x95\0\0\0\0\0\0\0"),
                               (".rodata", b"R" * 800), (".BTF", b"BTF")])
        self.path.write_bytes(make_elf(62, [(".text", b"\x90"), (".embedded", inner)]))
        found = review(self.path)
        self.assertTrue(found["review_lead"])
        self.assertEqual(found["embedded_bpf_count"], 1)
        self.assertEqual(found["embedded_bpf_objects"][0]["rodata_bytes"], 800)
        self.assertFalse(review(self.path, [sha256(self.path.read_bytes()).hexdigest()])["review_lead"])

    def test_benign_host(self):
        self.path.write_bytes(make_elf(62, [(".text", b"\x90")]))
        self.assertFalse(review(self.path)["review_lead"])

    def test_near_miss_embedded_other_architecture(self):
        inner = make_elf(62, [("tracepoint/raw_syscalls/sys_enter", b"\x90")])
        self.path.write_bytes(make_elf(62, [(".embedded", inner)]))
        self.assertEqual(review(self.path)["embedded_bpf_count"], 0)

    def test_truncated_elf_rejected(self):
        self.assertIsNone(inspect_elf(b"\x7fELF\x02\x01"))


if __name__ == "__main__":
    unittest.main()
