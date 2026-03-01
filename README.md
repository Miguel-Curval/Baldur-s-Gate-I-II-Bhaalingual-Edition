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
    --game-dir "path to game" \
    --list-langs
```

To install additional languages, launch the game and switch the language via the in-game settings, or use GOG Galaxy's language options. BG:EE/BG2:EE supports: `en_US`, `de_DE`, `fr_FR`, `es_ES`, `pl_PL`, `cs_CZ`, `it_IT`, `ru_RU`, `zh_CN`, `ko_KR`, `ja_JP`.

---

## Basic Usage

```bash
python generate-bilingual-bg2ee.py \
    --game-dir "path to game" \
    --primary-lang de_DE \
    --secondary-lang en_US \
    --output-dir ./output
```

This generates merged `.tlk` files in `./output/`. The primary language appears on top; the secondary appears below, separated by `---`.

### Merge and Install in One Step

```bash
python generate-bilingual-bg2ee.py \
    --game-dir "path to game" \
    --primary-lang de_DE \
    --secondary-lang en_US \
    --install
```

The `--install` flag copies the merged files into `lang/de_DE/` and backs up the originals as `dialog.tlk.bak`.

---

## All Options

| Flag | Default | Description |
|---|---|---|
| `--game-dir` | required | Path to BG:EE/BG2:EE installation |
| `--primary-lang` | required | Language shown first (e.g. `de_DE`) |
| `--secondary-lang` | required | Language shown second (e.g. `en_US`) |
| `--separator` | `\n` | Text between the two languages |
| `--inline-separator` | ` ~ ` | Text between short UI/Location strings. Used to prevent **save-game creation crashes**. |
| `--swap` | off | Swap primary/secondary order |
| `--output-dir` | `./output` | Where to write merged TLK files |
| `--encoding` | `cp1252` | File encoding (`cp1252` or `utf-8`) |
| `--install` | off | Install merged files into the game |
| `--restore` | off | Restore `.bak` backup files |
| `--dump TLK_FILE` | — | Print TLK contents (for debugging) |
| `--list-langs` | — | List installed language dirs |
| `--test` | — | Run self-test |

---

## Restoring Originals

```bash
python generate-bilingual-bg2ee.py \
    --game-dir "path to game" \
    --primary-lang de_DE \
    --restore
```

---

## How It Works

All BG:EE/BG2:EE text is stored in `dialog.tlk` (and `dialogf.tlk` for female character lines) inside the active language folder. The game looks up strings by numeric index. By replacing `dialog.tlk` with a merged bilingual version, every piece of text the game displays shows both languages.

- Strings that are identical in both languages (or empty) are kept as-is to avoid redundant output.
- **Save Game Crash Fix**: The game uses "Area Name" strings and the "Auto-Save" string to physically create save-game folders on your PC. If these strings contain newlines (`\n`), the OS refuses to create the folder and the game crashes while autosaving. To fix this, the script automatically detects short, non-dialogue strings and merges them with an inline separator (` ~ `) instead of a newline.

---

## Notes

- **Female dialogue**: `dialogf.tlk` is processed automatically if present in both language dirs.
- **Mods**: Other WeiDU mods that append to `dialog.tlk` may need to be reinstalled after this step.
- **Compatibility**: Tested with BG2:EE v2.6. The TLK format has been stable since the original BG2. The game runs a special encoding for certain languages, so you can't combine languages from different encodings. I haven't tested it but I assume this applies to CJK and cyrillic alphabet languages.
