import asyncio
import re
from pathlib import Path
from telethon import TelegramClient, functions, types, errors
import os

api_id = int(os.environ["TG_API_ID"])
api_hash = os.environ["TG_API_HASH"]

SEARCH_QUERIES = [
    "PepeEmojiGifPack",
    "RestrictedEmoji",
]


BASE_DIR = Path("export")
BASE_DIR.mkdir(exist_ok=True)


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


async def download_pack(client, query):
    result = await resolve_pack(client, query)

    pack_short_name = getattr(result.set, "short_name", "") or query
    pack_title = getattr(result.set, "title", "unknown")
    pack_dir = BASE_DIR / safe_dir_name(pack_short_name)
    pack_dir.mkdir(exist_ok=True)

    print(f"\nPack: {pack_title}")
    print(f"Short name: {pack_short_name}")
    print(f"Files: {len(result.documents)}")
    print(f"Folder: {pack_dir}\n")

    for i, doc in enumerate(result.documents, start=1):
        ext = get_ext(doc)
        filename = pack_dir / f"{i:03d}_{doc.id}{ext}"
        await client.download_media(doc, file=str(filename))
        print(f"Saved: {filename}")

    print("Done\n")


async def main():
    async with TelegramClient("emoji_export_session", api_id, api_hash) as client:
        for query in SEARCH_QUERIES:
            if not query.strip():
                print("[skip] empty query")
                continue

            try:
                await download_pack(client, query)
            except Exception as e:
                print(f"[error] {query}: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())