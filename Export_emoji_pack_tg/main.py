import asyncio
import json
import logging
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient, functions, types, errors, utils

load_dotenv()

api_id_raw = os.getenv("TG_API_ID")
api_hash = os.getenv("TG_API_HASH")

if not api_id_raw or not api_hash:
    raise RuntimeError("TG_API_ID or TG_API_HASH not found in .env")

api_id = int(api_id_raw)

SEARCH_QUERIES = [
"steampunkalphabetEmoji",
"Adaptive_4c35f_by_MoiStikiBot",
"shwarzz_by_fStikBot",
"MadEmoji",
"gifts_emoji_by_gifts_changes_bot",
"Minecraft2_by_epgobot",
"CreepyEmoji",
"RestrictedEmoji",
]

BASE_DIR = Path("export")
BASE_DIR.mkdir(exist_ok=True)

MANIFEST_NAME = "manifest.json"
KNOWN_EXTENSIONS = {".tgs", ".webm", ".webp", ".bin"}

logging.getLogger("telethon").setLevel(logging.ERROR)


def get_ext(doc):
    mime = getattr(doc, "mime_type", "") or ""
    if mime == "application/x-tgsticker":
        return ".tgs"
    if mime == "video/webm":
        return ".webm"
    if mime == "image/webp":
        return ".webp"
    return ".bin"


def get_set_obj(item):
    return getattr(item, "set", item)


def safe_dir_name(name: str) -> str:
    name = (name or "").strip()
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r"\s+", "_", name)
    return name or "unknown_pack"


def file_is_valid(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def load_manifest(pack_dir: Path) -> dict:
    manifest_path = pack_dir / MANIFEST_NAME
    if not manifest_path.exists():
        return {"items": {}}

    try:
        with manifest_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return {"items": {}}

        items = data.get("items")
        if not isinstance(items, dict):
            data["items"] = {}

        return data
    except Exception:
        return {"items": {}}


def save_manifest(pack_dir: Path, manifest: dict) -> None:
    manifest_path = pack_dir / MANIFEST_NAME
    tmp_path = pack_dir / f"{MANIFEST_NAME}.tmp"

    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    os.replace(tmp_path, manifest_path)


async def resolve_pack(client, query):
    try:
        print(f"[direct] {query}")
        return await client(
            functions.messages.GetStickerSetRequest(
                stickerset=types.InputStickerSetShortName(short_name=query),
                hash=0,
            )
        )
    except errors.StickersetInvalidError:
        print(f"[search] {query}")
        found = await client(
            functions.messages.SearchEmojiStickerSetsRequest(
                q=query,
                hash=0,
            )
        )

        for item in found.sets:
            s = get_set_obj(item)
            sid = getattr(s, "id", None)
            access_hash = getattr(s, "access_hash", None)

            if sid and access_hash:
                return await client(
                    functions.messages.GetStickerSetRequest(
                        stickerset=types.InputStickerSetID(
                            id=sid,
                            access_hash=access_hash,
                        ),
                        hash=0,
                    )
                )

    raise RuntimeError(f"Pack not found: {query}")


async def download_file_low_level(client, doc, target_path: Path, retries=8, base_delay=2):
    dc_id, input_location = utils.get_input_location(doc)
    file_size = getattr(doc, "size", None)

    last_error = None

    for attempt in range(1, retries + 1):
        temp_path = target_path.with_name(target_path.name + ".part")

        try:
            if temp_path.exists():
                temp_path.unlink()

            await client.download_file(
                input_location,
                file=str(temp_path),
                part_size_kb=64,
                file_size=file_size,
                dc_id=dc_id,
            )

            if not file_is_valid(temp_path):
                raise RuntimeError("Downloaded file is empty or invalid")

            if target_path.exists():
                target_path.unlink()

            os.replace(temp_path, target_path)
            return

        except errors.TimeoutError as e:
            last_error = e
            delay = min(base_delay * (2 ** (attempt - 1)), 30)
            print(f"[timeout] {target_path.name} attempt {attempt}/{retries}, sleep {delay}s")
        except Exception as e:
            last_error = e
            delay = min(base_delay * (2 ** (attempt - 1)), 30)
            print(f"[retry] {target_path.name} attempt {attempt}/{retries}: {e}")

        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass

        if attempt < retries:
            await asyncio.sleep(delay)

    raise last_error if last_error else RuntimeError(f"Failed to download {target_path.name}")


async def download_pack(client, query):
    result = await resolve_pack(client, query)

    pack_short_name = getattr(result.set, "short_name", "") or query
    pack_title = getattr(result.set, "title", "unknown")
    pack_dir = BASE_DIR / safe_dir_name(pack_short_name)
    pack_dir.mkdir(exist_ok=True)

    manifest = load_manifest(pack_dir)
    manifest["query"] = query
    manifest["pack_title"] = pack_title
    manifest["pack_short_name"] = pack_short_name
    manifest["items"] = manifest.get("items", {})

    stats = {
        "total": len(result.documents),
        "downloaded": 0,
        "skipped": 0,
        "failed": 0,
        "removed_stale": 0,
    }

    expected_files = set()

    print(f"\nPack: {pack_title}")
    print(f"Short name: {pack_short_name}")
    print(f"Files: {len(result.documents)}")
    print(f"Folder: {pack_dir}\n")

    for i, doc in enumerate(result.documents, start=1):
        ext = get_ext(doc)
        filename = f"{i}{ext}"
        target_path = pack_dir / filename
        expected_files.add(filename)

        doc_id = str(doc.id)
        record = manifest["items"].get(str(i))

        same_file_already_downloaded = (
            isinstance(record, dict)
            and record.get("doc_id") == doc_id
            and record.get("filename") == filename
            and record.get("ext") == ext
            and file_is_valid(target_path)
        )

        if same_file_already_downloaded:
            print(f"Skip: {target_path}")
            stats["skipped"] += 1
            continue

        try:
            await download_file_low_level(
                client=client,
                doc=doc,
                target_path=target_path,
                retries=8,
                base_delay=2,
            )

            manifest["items"][str(i)] = {
                "index": i,
                "doc_id": doc_id,
                "filename": filename,
                "ext": ext,
                "mime_type": getattr(doc, "mime_type", "") or "",
                "size": target_path.stat().st_size,
            }

            print(f"Saved: {target_path}")
            stats["downloaded"] += 1

        except Exception as e:
            print(f"[failed] {filename}: {e}")
            stats["failed"] += 1

    current_count = len(result.documents)

    stale_indexes = [
        key for key in manifest["items"].keys()
        if key.isdigit() and int(key) > current_count
    ]

    for key in stale_indexes:
        old_record = manifest["items"].get(key, {})
        old_filename = old_record.get("filename")

        if old_filename:
            old_path = pack_dir / old_filename
            if old_path.exists():
                try:
                    old_path.unlink()
                    print(f"Removed stale file: {old_path}")
                    stats["removed_stale"] += 1
                except Exception:
                    pass

        manifest["items"].pop(key, None)

    for path in pack_dir.iterdir():
        if not path.is_file():
            continue
        if path.name == MANIFEST_NAME or path.name.endswith(".part"):
            continue
        if path.suffix.lower() not in KNOWN_EXTENSIONS:
            continue
        if path.name not in expected_files:
            try:
                path.unlink()
                print(f"Removed stale file: {path}")
                stats["removed_stale"] += 1
            except Exception:
                pass

    manifest["total_files"] = len(result.documents)
    save_manifest(pack_dir, manifest)

    print(
        "\nStats:"
        f"\n  total: {stats['total']}"
        f"\n  downloaded: {stats['downloaded']}"
        f"\n  skipped: {stats['skipped']}"
        f"\n  failed: {stats['failed']}"
        f"\n  removed_stale: {stats['removed_stale']}\n"
    )

    return stats


async def main():
    total_stats = {
        "packs": 0,
        "total": 0,
        "downloaded": 0,
        "skipped": 0,
        "failed": 0,
        "removed_stale": 0,
    }

    client = TelegramClient(
        "emoji_export_session",
        api_id,
        api_hash,
        request_retries=10,
        connection_retries=10,
        retry_delay=2,
        auto_reconnect=True,
        timeout=20,
    )

    async with client:
        for query in SEARCH_QUERIES:
            if not query.strip():
                print("[skip] empty query")
                continue

            try:
                stats = await download_pack(client, query)
                total_stats["packs"] += 1
                total_stats["total"] += stats["total"]
                total_stats["downloaded"] += stats["downloaded"]
                total_stats["skipped"] += stats["skipped"]
                total_stats["failed"] += stats["failed"]
                total_stats["removed_stale"] += stats["removed_stale"]
            except Exception as e:
                print(f"[error] {query}: {e}\n")

    print("=== TOTAL ===")
    print(f"packs: {total_stats['packs']}")
    print(f"total: {total_stats['total']}")
    print(f"downloaded: {total_stats['downloaded']}")
    print(f"skipped: {total_stats['skipped']}")
    print(f"failed: {total_stats['failed']}")
    print(f"removed_stale: {total_stats['removed_stale']}")


if __name__ == "__main__":
    asyncio.run(main())