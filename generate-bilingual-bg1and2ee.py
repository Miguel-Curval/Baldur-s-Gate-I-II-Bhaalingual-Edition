#!/usr/bin/env python3
"""
generate-bilingual-bg1and2ee.py
================================
Merge two language versions of Baldur's Gate I/II Enhanced Edition's
dialog.tlk (and dialogf.tlk) into a single bilingual file.

Every string will display BOTH languages, e.g.:

    Ihr seid nicht im richtigen Gemütszustand.
    ---
    You are not in the right frame of mind.

Note on dialogf.tlk
-------------------
    dialogf.tlk exists only for gendered languages (e.g. de_DE, fr_FR).
    Languages like en_US only have dialog.tlk.  If the secondary language
    is missing dialogf.tlk, dialog.tlk from that language is used instead
    as the secondary source for merging dialogf.tlk.

Usage
-----
    python generate-bilingual-bg1and2ee.py \\
        --game-dir "path/to/game" \\
        --primary-lang de_DE \\
        --secondary-lang en_US \\
        --separator "\\n---\\n" \\
        --output-dir ./output

    # Dump first N entries of a TLK:
    python generate-bilingual-bg1and2ee.py --dump dialog.tlk [--max 200]

    # Run built-in self-test:
    python generate-bilingual-bg1and2ee.py --test
"""

import argparse
import os
import shutil
import sys

# tlk.py must be in the same directory
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from tlk import TlkFile, TlkEntry, FLAG_TEXT


# --------------------------------------------------------------------------- #
#  Core merge logic
# --------------------------------------------------------------------------- #

def merge_tlks(
    primary: TlkFile,
    secondary: TlkFile,
    separator: str = '\n',
    swap: bool = False,
) -> TlkFile:
    """
    Merge two TlkFile objects into one bilingual TlkFile.

    For each entry:
      - If both texts are identical (or one is empty), keep as-is.
      - Otherwise combine:  primary_text + separator + secondary_text
        (or swapped if swap=True)
    """
    if len(primary) != len(secondary):
        print(
            f"  WARNING: entry count mismatch — "
            f"primary={len(primary)}, secondary={len(secondary)}. "
            f"Using minimum."
        )

    count = min(len(primary), len(secondary))
    merged = TlkFile(language_id=primary.language_id)

    stats = dict(total=count, combined=0, kept=0, empty=0)

    for i in range(count):
        p_entry = primary.entries[i]
        s_entry = secondary.entries[i]

        p_text = p_entry.text.strip()
        s_text = s_entry.text.strip()

        if not p_text and not s_text:
            # Both empty — keep blank entry
            merged.entries.append(TlkEntry(
                text='',
                sound_resref=p_entry.sound_resref,
                flags=p_entry.flags & ~FLAG_TEXT,
                volume_variance=p_entry.volume_variance,
                pitch_variance=p_entry.pitch_variance,
            ))
            stats['empty'] += 1

        elif p_text == s_text or not s_text:
            # Identical or secondary is empty — keep primary as-is
            merged.entries.append(TlkEntry(
                text=p_entry.text,
                sound_resref=p_entry.sound_resref,
                flags=p_entry.flags,
                volume_variance=p_entry.volume_variance,
                pitch_variance=p_entry.pitch_variance,
            ))
            stats['kept'] += 1

        elif not p_text:
            # Primary is empty, secondary has text — keep secondary
            merged.entries.append(TlkEntry(
                text=s_entry.text,
                sound_resref=p_entry.sound_resref,
                flags=p_entry.flags,
                volume_variance=p_entry.volume_variance,
                pitch_variance=p_entry.pitch_variance,
            ))
            stats['kept'] += 1

        else:
            # Both have different text — combine them
            first  = s_entry.text if swap else p_entry.text
            second = p_entry.text if swap else s_entry.text
            combined = first + separator + second

            merged.entries.append(TlkEntry(
                text=combined,
                sound_resref=p_entry.sound_resref,
                flags=p_entry.flags | FLAG_TEXT,
                volume_variance=p_entry.volume_variance,
                pitch_variance=p_entry.pitch_variance,
            ))
            stats['combined'] += 1

    print(
        f"  Merged {stats['total']} entries: "
        f"{stats['combined']} bilingual, "
        f"{stats['kept']} kept, "
        f"{stats['empty']} empty"
    )
    return merged


# --------------------------------------------------------------------------- #
#  File operations
# --------------------------------------------------------------------------- #

def process_tlk_file(
    game_dir: str,
    filename: str,
    primary_lang: str,
    secondary_lang: str,
    output_dir: str,
    separator: str,
    swap: bool,
    encoding: str,
) -> bool:
    """
    Process one TLK file (dialog.tlk or dialogf.tlk).

    For dialogf.tlk: if the secondary language doesn't have it (e.g. en_US),
    falls back to the secondary language's dialog.tlk as the secondary source.

    Returns True if successful, False if the primary file was not found.
    """
    primary_path   = os.path.join(game_dir, 'lang', primary_lang,   filename)
    secondary_path = os.path.join(game_dir, 'lang', secondary_lang, filename)
    output_path    = os.path.join(output_dir, filename)

    if not os.path.exists(primary_path):
        print(f"  Skipping {filename}: not found at {primary_path}")
        return False

    # For dialogf.tlk: fall back to dialog.tlk if secondary has no dialogf.tlk
    secondary_fallback = False
    if not os.path.exists(secondary_path):
        if filename == 'dialogf.tlk':
            fallback_path = os.path.join(game_dir, 'lang', secondary_lang, 'dialog.tlk')
            if os.path.exists(fallback_path):
                print(f"  Note: {secondary_lang} has no {filename}, "
                      f"falling back to dialog.tlk")
                secondary_path = fallback_path
                secondary_fallback = True
            else:
                print(f"  Skipping {filename}: no {filename} or dialog.tlk "
                      f"found for {secondary_lang}")
                return False
        else:
            print(f"  Skipping {filename}: not found at {secondary_path}")
            return False

    print(f"\nProcessing {filename}:")
    print(f"  Primary:   {primary_path}")
    print(f"  Secondary: {secondary_path}"
          + (" (fallback from dialog.tlk)" if secondary_fallback else ""))

    primary   = TlkFile.from_file(primary_path,   encoding=encoding)
    secondary = TlkFile.from_file(secondary_path, encoding=encoding)

    print(f"  Primary entries: {len(primary)}, Secondary entries: {len(secondary)}")

    merged = merge_tlks(primary, secondary, separator=separator, swap=swap)

    os.makedirs(output_dir, exist_ok=True)
    merged.to_file(output_path, encoding=encoding)
    print(f"  Written → {output_path}")
    return True


# --------------------------------------------------------------------------- #
#  Install helper
# --------------------------------------------------------------------------- #

def install_output(
    game_dir: str,
    primary_lang: str,
    output_dir: str,
    filenames: list,
) -> None:
    """
    Copy merged TLK files into the game's primary language directory,
    backing up originals first.
    """
    lang_dir = os.path.join(game_dir, 'lang', primary_lang)

    for filename in filenames:
        src = os.path.join(output_dir, filename)
        dst = os.path.join(lang_dir, filename)
        bak = dst + '.bak'

        if not os.path.exists(src):
            continue

        if os.path.exists(dst) and not os.path.exists(bak):
            print(f"  Backing up {dst} → {bak}")
            shutil.copy2(dst, bak)
        elif os.path.exists(bak):
            print(f"  Backup already exists: {bak}")

        print(f"  Installing {src} → {dst}")
        shutil.copy2(src, dst)


def restore_backup(game_dir: str, primary_lang: str, filenames: list) -> None:
    """Restore the original .bak files."""
    lang_dir = os.path.join(game_dir, 'lang', primary_lang)
    for filename in filenames:
        dst = os.path.join(lang_dir, filename)
        bak = dst + '.bak'
        if os.path.exists(bak):
            print(f"  Restoring {bak} → {dst}")
            shutil.copy2(bak, dst)
            os.remove(bak)
        else:
            print(f"  No backup found for {filename}")


# --------------------------------------------------------------------------- #
#  CLI
# --------------------------------------------------------------------------- #

def parse_separator(sep_str: str) -> str:
    """Allow \\n and \\t escape sequences in the separator argument."""
    return sep_str.replace('\\n', '\n').replace('\\t', '\t')


def list_installed_languages(game_dir: str) -> None:
    lang_dir = os.path.join(game_dir, 'lang')
    if not os.path.isdir(lang_dir):
        print(f"ERROR: lang directory not found at {lang_dir}")
        return
    langs = [
        d for d in os.listdir(lang_dir)
        if os.path.isdir(os.path.join(lang_dir, d))
    ]
    if langs:
        print("Installed languages:")
        for lang in sorted(langs):
            tlk = os.path.join(lang_dir, lang, 'dialog.tlk')
            size = f"{os.path.getsize(tlk):,} bytes" if os.path.exists(tlk) else "no dialog.tlk"
            print(f"  {lang:<12}  {size}")
    else:
        print("No language directories found.")


def main():
    parser = argparse.ArgumentParser(
        description='Generate a bilingual dialog.tlk for Baldur\'s Gate I/II Enhanced Edition.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # --- Mode flags ---
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--test', action='store_true',
                      help='Run self-test and exit')
    mode.add_argument('--dump', metavar='TLK_FILE',
                      help='Dump contents of a TLK file and exit')
    mode.add_argument('--list-langs', action='store_true',
                      help='List installed language directories and exit')
    mode.add_argument('--restore', action='store_true',
                      help='Restore .bak backup files (undo a previous install)')

    # --- Core args ---
    parser.add_argument('--game-dir', metavar='PATH',
                        help='Path to BG2:EE installation directory')
    parser.add_argument('--primary-lang', metavar='LANG',
                        help='Primary language code (shown first), e.g. de_DE')
    parser.add_argument('--secondary-lang', metavar='LANG',
                        help='Secondary language code (shown second), e.g. en_US')

    # --- Options ---
    parser.add_argument('--separator', metavar='SEP', default='\\n---\\n',
                        help='Separator between languages (default: \\\\n---\\\\n). Supports \\\\n and \\\\t.')
    parser.add_argument('--swap', action='store_true',
                        help='Swap primary/secondary order in output')
    parser.add_argument('--output-dir', metavar='PATH', default='./output',
                        help='Output directory for merged TLK files (default: ./output)')
    parser.add_argument('--encoding', metavar='ENC', default='cp1252',
                        help='Text encoding of the TLK files (default: cp1252). '
                             'Use utf-8 for some Enhanced Edition installs.')
    parser.add_argument('--install', action='store_true',
                        help='After merging, install merged files into the game '
                             '(backs up originals as *.bak)')
    parser.add_argument('--max', metavar='N', type=int, default=100,
                        help='Max entries to show with --dump (default: 100)')

    args = parser.parse_args()

    # --- Self-test ---
    if args.test:
        from tlk import TlkFile as _TLK
        _TLK.run_self_test()

        # Also test the merge logic
        primary = TlkFile()
        secondary = TlkFile()
        data = [
            ("Hallo Welt",    "Hello World"),
            ("",              ""),
            ("Gleicher Text", "Gleicher Text"),
            ("Nur Primär",    ""),
        ]
        for p, s in data:
            primary.entries.append(TlkEntry(text=p, flags=FLAG_TEXT if p else 0))
            secondary.entries.append(TlkEntry(text=s, flags=FLAG_TEXT if s else 0))

        merged = merge_tlks(primary, secondary, separator='\n---\n')

        assert merged.entries[0].text == "Hallo Welt\n---\nHello World", \
            f"Merge test 0 failed: {merged.entries[0].text!r}"
        assert merged.entries[1].text == "", "Merge test 1 failed"
        assert merged.entries[2].text == "Gleicher Text", "Merge test 2 failed"
        assert merged.entries[3].text == "Nur Primär", "Merge test 3 failed"

        print("Merge self-test: PASSED")
        print("All tests passed!")
        return

    # --- Dump mode ---
    if args.dump:
        tlk = TlkFile.from_file(args.dump, encoding=args.encoding)
        tlk.dump(max_entries=args.max, show_empty=False)
        return

    # --- List languages ---
    if args.list_langs:
        if not args.game_dir:
            parser.error('--list-langs requires --game-dir')
        list_installed_languages(args.game_dir)
        return

    # --- Restore backups ---
    if args.restore:
        if not args.game_dir or not args.primary_lang:
            parser.error('--restore requires --game-dir and --primary-lang')
        restore_backup(args.game_dir, args.primary_lang, ['dialog.tlk', 'dialogf.tlk'])
        return

    # --- Normal merge mode ---
    if not args.game_dir:
        parser.error('--game-dir is required')
    if not args.primary_lang:
        parser.error('--primary-lang is required')
    if not args.secondary_lang:
        parser.error('--secondary-lang is required')

    separator = parse_separator(args.separator)

    print(f"BG1/2 Bhaalingual Edition — TLK Generator")
    print(f"  Game dir:       {args.game_dir}")
    print(f"  Primary lang:   {args.primary_lang}")
    print(f"  Secondary lang: {args.secondary_lang}")
    print(f"  Separator:      {args.separator!r}")
    print(f"  Output dir:     {args.output_dir}")
    if args.swap:
        print(f"  (languages swapped)")

    tlk_files = ['dialog.tlk', 'dialogf.tlk']
    processed = []

    for filename in tlk_files:
        ok = process_tlk_file(
            game_dir=args.game_dir,
            filename=filename,
            primary_lang=args.primary_lang,
            secondary_lang=args.secondary_lang,
            output_dir=args.output_dir,
            separator=separator,
            swap=args.swap,
            encoding=args.encoding,
        )
        if ok:
            processed.append(filename)

    if not processed:
        print("\nERROR: No TLK files were processed. Check --game-dir and language codes.")
        sys.exit(1)

    print(f"\nDone! Merged files are in: {os.path.abspath(args.output_dir)}")

    if args.install:
        print(f"\nInstalling into game ({args.primary_lang})...")
        install_output(args.game_dir, args.primary_lang, args.output_dir, processed)
        print("\nInstallation complete.")
        print("  To restore originals: python generate-bilingual-bg1and2ee.py "
              f"--game-dir \"{args.game_dir}\" --primary-lang {args.primary_lang} --restore")
    else:
        print("\nTo install into the game, copy the merged file(s) to:")
        for f in processed:
            dst = os.path.join(args.game_dir, 'lang', args.primary_lang, f)
            print(f"  {os.path.join(args.output_dir, f)}  →  {dst}")
        print("\nOr re-run with --install to do this automatically (backs up originals).")


if __name__ == '__main__':
    main()
