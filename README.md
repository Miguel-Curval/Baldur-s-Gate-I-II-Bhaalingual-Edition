# BG1/2 Bhaalingual Edition

Merge two language versions of Baldur's Gate I & II Enhanced Edition into a single bilingual `dialog.tlk`. Every string in-game (dialogue, item descriptions, spell names, etc.) will display both languages simultaneously.

```
Ihr seid nicht im richtigen Gemütszustand.
---
You are not in the right frame of mind.
```

---

## Requirements

- Python 3.7+
- Two language versions installed in your BG:EE/BG2:EE `lang/` folder

## Checking Installed Languages

```bash
python generate-bilingual-bg2ee.py \
    -g "path to game" \
    --list-langs
```

To install additional languages, launch the game and switch the language via the in-game settings, or use GOG Galaxy's language options. BG:EE/BG2:EE supports: `en_US`, `de_DE`, `fr_FR`, `es_ES`, `pl_PL`, `cs_CZ`, `it_IT`, `ru_RU`, `zh_CN`, `ko_KR`, `ja_JP`.

---

## Basic Usage

```bash
python generate-bilingual-bg2ee.py \
    -g "path to game" \
    -p de_DE \
    -s en_US \
    -o ./output
```

This generates merged `.tlk` files in `./output/`. The primary language appears on top; the secondary appears below, separated by `---`.

### Merge and Install in One Step

```bash
python generate-bilingual-bg2ee.py \
    -g "path to game" \
    -p de_DE \
    -s en_US \
    -i
```

The `--install` flag copies the merged files into `lang/de_DE/` and backs up the originals as `dialog.tlk.bak`.

---

## All Options

| Flag | Short | Default | Description |
|---|---|---|---|
| `--game-dir` | `-g` | required | Path to BG:EE/BG2:EE installation |
| `--primary-lang` | `-p` | required | Language shown first (e.g. `de_DE`) |
| `--secondary-lang` | `-s` | required | Language shown second (e.g. `en_US`) |
| `--separator` | `-S` | `\n` | Text between the two languages |
| `--inline-separator` | `-I` | ` ~ ` | Text between short UI/Location strings. Used to prevent **save-game creation crashes**. |
| `--swap` | `-w` | off | Swap primary/secondary order |
| `--output-dir` | `-o` | `./output` | Where to write merged TLK files |
| `--encoding` | `-e` | `cp1252` | File encoding (`cp1252` or `utf-8`) |
| `--install` | `-i` | off | Install merged files into the game |
| `--restore` | `-r` | off | Restore `.bak` backup files. `-g` required; `-p` optional (omit to restore all languages) |
| `--dump TLK_FILE` | `-d` | — | Print TLK contents (for debugging) |
| `--max` | `-m` | 100 | Max entries to show with `--dump` |
| `--list-langs` | `-l` | — | List installed language dirs |
| `--test` | `-t` | — | Run self-test |

---

## Restoring Originals

```bash
# Restore only one language:
python generate-bilingual-bg2ee.py -r -g "path to game" -p de_DE

# Restore all languages at once (omit -p):
python generate-bilingual-bg2ee.py -r -g "path to game"
```

If `-p`/`--primary-lang` is omitted, every language directory under `lang/` is scanned and all `.bak` files are restored.

---

## How It Works

All BG:EE/BG2:EE text is stored in `dialog.tlk` (and `dialogf.tlk` for female character lines) inside the active language folder. The game looks up strings by numeric index. By replacing `dialog.tlk` with a merged bilingual version, every piece of text the game displays shows both languages.

- Strings that are identical in both languages (or empty) are kept as-is to avoid redundant output.
- **Save Game Crash Fix**: The game uses "Area Name" strings and the "Auto-Save" string to physically create save-game folders on your PC. If these strings contain newlines (`\n`), the OS refuses to create the folder and the game crashes while autosaving. To fix this, the script automatically detects short, non-dialogue strings and merges them with an inline separator (` ~ `) instead of a newline.

---

## Notes

> [!WARNING]
> **Always restore your original TLK files before installing, reinstalling, or uninstalling anything with WeiDU.**
> WeiDU mods patch `dialog.tlk` directly. If your bilingual file is in place, WeiDU will patch the bilingual strings instead of the originals, producing corrupted or duplicated text. Run `--restore` first, apply your mods, then re-run the bilingual generator.

- **Mods**: After installing WeiDU mods, some mod-added strings will only appear in your primary language (the secondary translation won't exist for those entries). This is expected — only vanilla strings are bilingual; mod strings appear in whichever language the mod was installed with.
- **Compatibility**: Tested with BG2:EE v2.6. The TLK format has been stable since the original BG2. The game runs a special encoding for certain languages, so you can't combine languages from different encodings. I haven't tested it but I assume this applies to CJK and cyrillic alphabet languages.
