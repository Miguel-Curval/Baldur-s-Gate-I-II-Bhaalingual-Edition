"""
tlk.py - TLK v1 Reader/Writer for Infinity Engine games (Baldur's Gate, Icewind Dale, etc.)

TLK file format documentation:
  https://gibberlings3.github.io/iesdp/file_formats/ie_formats/tlk_v1.htm

Structure:
  Header (18 bytes):
    4 bytes: signature ('TLK ')
    4 bytes: version  ('V1  ')
    2 bytes: language_id (uint16)
    4 bytes: num_entries (uint32)
    4 bytes: offset_to_strings (uint32)

  Entry table (num_entries * 26 bytes each):
    2 bytes: flags (uint16)  bit0=text, bit1=sound, bit2=token
    8 bytes: sound_resref (char[8])
    4 bytes: volume_variance (uint32) - unused
    4 bytes: pitch_variance  (uint32) - unused
    4 bytes: string_offset (uint32)   - relative to offset_to_strings
    4 bytes: string_length (uint32)

  String section:
    Raw bytes of all strings (UTF-8 / cp1252 encoding)

MIT License - adapted from tkarabela/infinityengine-tools
"""

import struct
from dataclasses import dataclass, field
from typing import List, Optional

# Header layout
_HDR_FMT = '<4s4sHII'
_HDR_SIZE = struct.calcsize(_HDR_FMT)  # 18 bytes

# Entry layout
_ENTRY_FMT = '<H8sIIII'
_ENTRY_SIZE = struct.calcsize(_ENTRY_FMT)  # 26 bytes

TLK_SIGNATURE = b'TLK '
TLK_VERSION   = b'V1  '

# Entry flag bits
FLAG_TEXT  = 0x01
FLAG_SOUND = 0x02
FLAG_TOKEN = 0x04


@dataclass
class TlkEntry:
    """Represents one string entry in a TLK file."""
    text: str = ''
    sound_resref: bytes = b'\x00' * 8
    flags: int = FLAG_TEXT
    volume_variance: int = 0
    pitch_variance: int = 0

    def has_text(self) -> bool:
        return bool(self.flags & FLAG_TEXT)

    def has_sound(self) -> bool:
        return bool(self.flags & FLAG_SOUND)


class TlkFile:
    """Reads and writes Infinity Engine TLK v1 files."""

    def __init__(self, language_id: int = 0):
        self.language_id: int = language_id
        self.entries: List[TlkEntry] = []

    def __len__(self):
        return len(self.entries)

    # ------------------------------------------------------------------ #
    #  Reading
    # ------------------------------------------------------------------ #

    @classmethod
    def from_file(cls, path: str, encoding: str = 'cp1252') -> 'TlkFile':
        with open(path, 'rb') as f:
            data = f.read()
        return cls._parse(data, encoding)

    @classmethod
    def _parse(cls, data: bytes, encoding: str = 'cp1252') -> 'TlkFile':
        # Parse header
        sig, ver, lang_id, num_entries, str_offset = struct.unpack_from(_HDR_FMT, data, 0)

        if sig != TLK_SIGNATURE:
            raise ValueError(f"Not a TLK file (got signature {sig!r})")
        if ver != TLK_VERSION:
            raise ValueError(f"Unsupported TLK version {ver!r}")

        tlk = cls(language_id=lang_id)

        # Parse entries
        entry_base = _HDR_SIZE
        string_base = str_offset

        for i in range(num_entries):
            off = entry_base + i * _ENTRY_SIZE
            flags, sound_resref, vol_var, pitch_var, str_off, str_len = \
                struct.unpack_from(_ENTRY_FMT, data, off)

            # Decode the string
            raw_str = data[string_base + str_off : string_base + str_off + str_len]
            text = raw_str.decode(encoding, errors='replace')

            entry = TlkEntry(
                text=text,
                sound_resref=sound_resref,
                flags=flags,
                volume_variance=vol_var,
                pitch_variance=pitch_var,
            )
            tlk.entries.append(entry)

        return tlk

    # ------------------------------------------------------------------ #
    #  Writing
    # ------------------------------------------------------------------ #

    def to_bytes(self, encoding: str = 'cp1252') -> bytes:
        # Encode all strings
        encoded_strings: List[bytes] = []
        for entry in self.entries:
            encoded_strings.append(entry.text.encode(encoding, errors='replace'))

        # Build string block and compute offsets
        string_offsets: List[int] = []
        string_block = bytearray()
        for s in encoded_strings:
            string_offsets.append(len(string_block))
            string_block.extend(s)

        num_entries = len(self.entries)
        str_offset = _HDR_SIZE + num_entries * _ENTRY_SIZE

        # Build header
        header = struct.pack(_HDR_FMT,
            TLK_SIGNATURE,
            TLK_VERSION,
            self.language_id,
            num_entries,
            str_offset,
        )

        # Build entry table
        entry_table = bytearray()
        for i, entry in enumerate(self.entries):
            # Ensure sound_resref is exactly 8 bytes
            sound_resref = entry.sound_resref[:8].ljust(8, b'\x00')

            # Recalculate flags based on content
            flags = entry.flags
            if entry.text:
                flags |= FLAG_TEXT
            else:
                flags &= ~FLAG_TEXT

            entry_table.extend(struct.pack(_ENTRY_FMT,
                flags,
                sound_resref,
                entry.volume_variance,
                entry.pitch_variance,
                string_offsets[i],
                len(encoded_strings[i]),
            ))

        return header + bytes(entry_table) + bytes(string_block)

    def to_file(self, path: str, encoding: str = 'cp1252') -> None:
        data = self.to_bytes(encoding)
        with open(path, 'wb') as f:
            f.write(data)

    # ------------------------------------------------------------------ #
    #  Utilities
    # ------------------------------------------------------------------ #

    def dump(self, max_entries: Optional[int] = None, show_empty: bool = False) -> None:
        """Print TLK contents for debugging."""
        total = len(self.entries)
        limit = min(total, max_entries) if max_entries else total
        print(f"TLK: {total} entries, language_id={self.language_id}")
        for i in range(limit):
            e = self.entries[i]
            if not show_empty and not e.text.strip():
                continue
            sound = e.sound_resref.rstrip(b'\x00').decode('ascii', errors='replace')
            print(f"  [{i:6d}] flags={e.flags:02x} sound={sound!r:12s} text={e.text[:80]!r}")

    @classmethod
    def run_self_test(cls) -> None:
        """Round-trip self-test: build synthetic TLK, write to bytes, re-read, verify."""
        import io
        tlk = cls(language_id=0)
        test_strings = [
            "Hello, world!",
            "You have selected an impressive lock.",
            "",  # empty entry
            "Minsc must lead — swords for everyone!",
            "Go for the eyes, Boo! GO FOR THE EYES!",
        ]
        for s in test_strings:
            tlk.entries.append(TlkEntry(text=s, flags=FLAG_TEXT if s else 0))

        raw = tlk.to_bytes()
        tlk2 = cls._parse(raw)

        assert len(tlk2.entries) == len(tlk.entries), "Entry count mismatch"
        for i, (a, b) in enumerate(zip(tlk.entries, tlk2.entries)):
            assert a.text == b.text, f"Text mismatch at {i}: {a.text!r} != {b.text!r}"

        print("tlk.py self-test: PASSED")
