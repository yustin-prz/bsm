import os
import io
import json
import shutil
import zipfile
from pathlib import Path


# ── Helpers ────────────────────────────────────────────────────────────────────
def read_manifest_from_zip(zf, prefix=""):
    """Try to find and parse manifest.json inside an open ZipFile."""
    candidates = [n for n in zf.namelist() if n.endswith("manifest.json")]
    if not candidates:
        return None
    # prefer shortest path (top-level)
    candidates.sort(key=lambda x: x.count("/"))
    try:
        data = json.loads(zf.read(candidates[0]))
        return data
    except Exception:
        return None

def detect_pack_type(manifest):
    """Return 'behavior', 'resource', or None based on manifest modules."""
    modules = manifest.get("modules", [])
    types = {m.get("type", "") for m in modules}
    if "resources" in types:
        return "resource"
    if "data" in types or "script" in types:
        return "behavior"
    return None

def pack_name_from_manifest(manifest):
    return manifest.get("header", {}).get("name", "Unknown Pack")

def pack_uuid_from_manifest(manifest):
    return manifest.get("header", {}).get("uuid", "")

def pack_version_from_manifest(manifest):
    v = manifest.get("header", {}).get("version", [1, 0, 0])
    return v

def safe_folder_name(name):
    return "".join(c if c.isalnum() or c in "._- " else "_" for c in name).strip()


def resolve_pack_name(zf, manifest, prefix=""):
    """Resolve the display name. Many packs set header.name to a localization key
    like 'pack.name'; look it up in texts/*.lang (preferring English)."""
    raw = pack_name_from_manifest(manifest) or ""
    if not raw or " " in raw or "." not in raw:
        return raw or "Unknown Pack"
    texts_prefix = prefix + "texts/"
    langs = [n for n in zf.namelist() if n.startswith(texts_prefix) and n.endswith(".lang")]
    langs.sort(key=lambda n: 0 if "en_US" in n else 1 if "en_" in n else 2)
    for lp in langs:
        try:
            content = zf.read(lp).decode("utf-8", errors="replace")
        except Exception:
            continue
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() == raw:
                return clean_lang_value(v)
    return clean_lang_value(raw)


def clean_archive_name(stem):
    """Turn a file stem like 'Waystones__addon_' into 'Waystones'."""
    s = stem.replace("_", " ")
    parts = [p for p in s.split() if p.lower() not in ("addon", "addons", "mcaddon")]
    return " ".join(parts).strip() or stem


def resolve_pack_name_disk(pack_dir, manifest):
    """Like resolve_pack_name but reads texts/*.lang from an extracted folder."""
    raw = pack_name_from_manifest(manifest) or ""
    if not raw or " " in raw or "." not in raw:
        return raw or "Unknown Pack"
    lang = lang_map_disk(pack_dir)
    return lang.get(raw, raw)


def strip_mc_format(s):
    """Remove Minecraft §-formatting codes from a string."""
    out = []
    i = 0
    while i < len(s):
        if s[i] == "§" and i + 1 < len(s):
            i += 2
            continue
        out.append(s[i])
        i += 1
    return "".join(out).strip()


def clean_lang_value(v):
    """A .lang value may have a trailing '\\t#comment' and §-codes; clean both."""
    if "\t" in v:
        v = v.split("\t", 1)[0]
    return strip_mc_format(v).strip()


def lang_map_disk(pack_dir):
    """Return {key: clean_value} from texts/*.lang (English preferred)."""
    result = {}
    texts = os.path.join(pack_dir, "texts")
    if not os.path.isdir(texts):
        return result
    langs = [f for f in os.listdir(texts) if f.endswith(".lang")]
    langs.sort(key=lambda n: 0 if "en_US" in n else 1 if "en_" in n else 2, reverse=True)
    for lp in langs:  # later (preferred) overwrite earlier
        try:
            with open(os.path.join(texts, lp), encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if "=" not in line or line.lstrip().startswith("##"):
                        continue
                    k, _, v = line.partition("=")
                    result[k.strip()] = clean_lang_value(v)
        except Exception:
            continue
    return result


def read_pack_config(pack_dir):
    """Read a pack's subpacks and settings (with labels resolved). Returns
    {'subpacks': [{folder, name}], 'settings': [...]} or None if no manifest."""
    mpath = os.path.join(pack_dir, "manifest.json")
    if not os.path.isfile(mpath):
        return None
    try:
        with open(mpath, encoding="utf-8") as f:
            m = json.load(f)
    except Exception:
        return None
    lang = lang_map_disk(pack_dir)

    def label(s, fallback=""):
        # a setting/option has 'text' (a key) and/or 'name'
        key = s.get("text") or ""
        if key and key in lang:
            return lang[key]
        if key:
            return strip_mc_format(key)
        return strip_mc_format(s.get("name", fallback))

    subpacks = []
    for sp in m.get("subpacks", []):
        raw = sp.get("name", sp.get("folder_name", ""))
        nm = strip_mc_format(raw.split("§")[0]) or strip_mc_format(raw)
        subpacks.append({"folder": sp.get("folder_name", ""), "name": nm})

    settings = []
    for s in m.get("settings", []):
        t = s.get("type")
        if t == "toggle":
            settings.append({"type": "toggle", "label": label(s),
                             "default": bool(s.get("default"))})
        elif t == "dropdown":
            opts = [label(o, o.get("name", "")) for o in s.get("options", [])]
            default = s.get("default", "")
            # resolve default option label
            dlabel = default
            for o in s.get("options", []):
                if o.get("name") == default:
                    dlabel = label(o, default)
                    break
            settings.append({"type": "dropdown", "label": label(s),
                             "options": opts, "default": dlabel})
        elif t == "slider":
            settings.append({"type": "slider", "label": label(s),
                             "default": s.get("default", "")})
    return {"subpacks": subpacks, "settings": settings}


# ── Pack installer ─────────────────────────────────────────────────────────────
class PackInstaller:
    """
    Handles extraction of .mcaddon / .mcpack / .zip into the server folders
    and updates world_behavior_packs.json / world_resource_packs.json.
    """

    def __init__(self, server_dir, world_dir):
        self.server_dir = server_dir
        self.world_dir = world_dir

    def _world_json_path(self, kind):
        fname = "world_behavior_packs.json" if kind == "behavior" else "world_resource_packs.json"
        return os.path.join(self.world_dir, fname)

    def _load_world_json(self, kind):
        path = self._world_json_path(kind)
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_world_json(self, kind, data):
        os.makedirs(self.world_dir, exist_ok=True)
        with open(self._world_json_path(kind), "w") as f:
            json.dump(data, f, indent=2)

    def _entry_exists(self, entries, uuid):
        return any(e.get("pack_id") == uuid for e in entries)

    def _add_to_world_json(self, kind, uuid, version):
        entries = self._load_world_json(kind)
        if not self._entry_exists(entries, uuid):
            entries.append({"pack_id": uuid, "version": version})
            self._save_world_json(kind, entries)
            return True
        return False  # already present

    def _extract_pack(self, zf, kind, folder_name, prefix=""):
        """Extract pack files (with optional prefix) into behavior_packs or resource_packs."""
        dest_root = "behavior_packs" if kind == "behavior" else "resource_packs"
        dest = os.path.join(self.server_dir, dest_root, folder_name)
        os.makedirs(dest, exist_ok=True)
        for member in zf.namelist():
            if prefix and not member.startswith(prefix):
                continue
            rel = member[len(prefix):] if prefix else member
            if not rel or rel.endswith("/"):
                continue
            target = os.path.join(dest, rel)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with zf.open(member) as src, open(target, "wb") as dst:
                dst.write(src.read())

    # ── grouping metadata (which packs were installed together as one addon) ──
    def _meta_path(self):
        return os.path.join(self.server_dir, ".bedrock_manager_packs.json")

    def _load_meta(self):
        path = self._meta_path()
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"groups": []}

    def _save_meta(self, meta):
        try:
            with open(self._meta_path(), "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)
        except Exception:
            pass

    def _record_group(self, name, source, results):
        meta = self._load_meta()
        # Replace any previous group from the same source archive (reinstall)
        meta["groups"] = [g for g in meta.get("groups", []) if g.get("source") != source]
        meta["groups"].append({
            "name": name,
            "source": source,
            "packs": [{"uuid": r["uuid"], "kind": r["kind"], "folder": r["folder"],
                       "name": r["name"], "version": r["version"]} for r in results],
        })
        self._save_meta(meta)

    def scan_installed(self):
        """Map uuid -> {name, kind, folder, version} by reading installed manifests."""
        index = {}
        for kind, root in (("behavior", "behavior_packs"), ("resource", "resource_packs")):
            base = os.path.join(self.server_dir, root)
            if not os.path.isdir(base):
                continue
            for entry in os.listdir(base):
                folder = os.path.join(base, entry)
                if not os.path.isdir(folder):
                    continue
                mf = os.path.join(folder, "manifest.json")
                if not os.path.isfile(mf):
                    mf = None
                    for r, _, files in os.walk(folder):
                        if "manifest.json" in files:
                            mf = os.path.join(r, "manifest.json")
                            break
                if not mf:
                    continue
                try:
                    with open(mf, encoding="utf-8") as f:
                        m = json.load(f)
                except Exception:
                    continue
                uuid = pack_uuid_from_manifest(m)
                if not uuid:
                    continue
                index[uuid] = {"name": resolve_pack_name_disk(os.path.dirname(mf), m),
                               "kind": kind, "folder": entry,
                               "version": pack_version_from_manifest(m)}
        return index

    def delete_pack_files(self, kind, folder):
        root = "behavior_packs" if kind == "behavior" else "resource_packs"
        path = os.path.join(self.server_dir, root, folder)
        if folder and os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)

    def _pack_dir(self, kind, folder):
        root = "behavior_packs" if kind == "behavior" else "resource_packs"
        return os.path.join(self.server_dir, root, folder)

    def force_subpack(self, kind, folder, subpack_folder, uuid=None):
        """Bake a subpack into the pack root so every client gets that variant
        (the only way to fix a subpack server-side). Backs up the pack first and
        bumps the version so clients re-download."""
        pack_dir = self._pack_dir(kind, folder)
        sp_dir = os.path.join(pack_dir, "subpacks", subpack_folder)
        if not os.path.isdir(sp_dir):
            raise ValueError("No se encontró la carpeta del subpack.")
        backup = pack_dir + ".bak"
        if not os.path.isdir(backup):
            shutil.copytree(pack_dir, backup)
        # overlay subpack files on top of the pack root
        for r, _dirs, files in os.walk(sp_dir):
            rel = os.path.relpath(r, sp_dir)
            dest = pack_dir if rel == "." else os.path.join(pack_dir, rel)
            os.makedirs(dest, exist_ok=True)
            for fn in files:
                shutil.copy2(os.path.join(r, fn), os.path.join(dest, fn))
        # drop the subpacks folder + manifest entry so the game can't re-pick one
        shutil.rmtree(os.path.join(pack_dir, "subpacks"), ignore_errors=True)
        new_version = None
        mpath = os.path.join(pack_dir, "manifest.json")
        try:
            with open(mpath, encoding="utf-8") as f:
                m = json.load(f)
            m.pop("subpacks", None)
            ver = m.get("header", {}).get("version", [1, 0, 0])
            if isinstance(ver, list) and len(ver) == 3:
                ver = [ver[0], ver[1], ver[2] + 1]   # bump patch
                m["header"]["version"] = ver
                new_version = ver
            with open(mpath, "w", encoding="utf-8") as f:
                json.dump(m, f, indent=2)
        except Exception:
            pass
        # keep world json version in sync so clients re-download
        if uuid and new_version:
            entries = self._load_world_json(kind)
            for e in entries:
                if e.get("pack_id") == uuid:
                    e["version"] = new_version
            self._save_world_json(kind, entries)

    def has_backup(self, kind, folder):
        return os.path.isdir(self._pack_dir(kind, folder) + ".bak")

    def restore_pack(self, kind, folder):
        pack_dir = self._pack_dir(kind, folder)
        backup = pack_dir + ".bak"
        if not os.path.isdir(backup):
            return False
        shutil.rmtree(pack_dir, ignore_errors=True)
        shutil.move(backup, pack_dir)
        return True

    def remove_group_meta(self, source):
        meta = self._load_meta()
        meta["groups"] = [g for g in meta.get("groups", []) if g.get("source") != source]
        self._save_meta(meta)

    def install(self, file_path):
        """
        Returns list of dicts: {name, kind, uuid, version, folder, already_present}
        Also records a grouping entry so addons (BP+RP) can be managed together.
        Raises on error.
        """
        results = []

        with zipfile.ZipFile(file_path, "r") as outer:
            names = outer.namelist()
            inner_packs = [n for n in names if n.endswith(".mcpack")]

            if inner_packs:
                for inner_name in inner_packs:
                    inner_data = outer.read(inner_name)
                    import io
                    with zipfile.ZipFile(io.BytesIO(inner_data), "r") as inner_zf:
                        manifest = read_manifest_from_zip(inner_zf)
                        if not manifest:
                            continue
                        kind = detect_pack_type(manifest)
                        if not kind:
                            continue
                        folder = safe_folder_name(Path(inner_name).stem)
                        self._extract_pack(inner_zf, kind, folder)
                        uuid = pack_uuid_from_manifest(manifest)
                        version = pack_version_from_manifest(manifest)
                        already = not self._add_to_world_json(kind, uuid, version)
                        results.append({"name": resolve_pack_name(inner_zf, manifest),
                                        "kind": kind, "uuid": uuid, "version": version,
                                        "folder": folder, "already_present": already})
            else:
                # No inner .mcpack files: the archive holds one or more packs as
                # folders (each with its own manifest.json). Process EVERY manifest
                # so addons that ship BP and RP as separate folders both get installed.
                manifests = [n for n in names if n.endswith("manifest.json")]
                for mpath in manifests:
                    try:
                        mdata = json.loads(outer.read(mpath))
                    except Exception:
                        continue
                    kind = detect_pack_type(mdata)
                    if not kind:
                        continue
                    prefix = mpath.rsplit("/", 1)[0] + "/" if "/" in mpath else ""
                    folder = safe_folder_name(prefix.strip("/") or Path(file_path).stem)
                    self._extract_pack(outer, kind, folder, prefix)
                    uuid = pack_uuid_from_manifest(mdata)
                    version = pack_version_from_manifest(mdata)
                    name = resolve_pack_name(outer, mdata, prefix)
                    already = not self._add_to_world_json(kind, uuid, version)
                    results.append({"name": name, "kind": kind, "uuid": uuid,
                                    "version": version, "folder": folder,
                                    "already_present": already})

        if not results:
            raise ValueError("No se encontró ningún pack válido con manifest.json en el archivo.")

        # Group name: a shared resolved name if all packs agree, else a cleaned
        # version of the archive filename; for a lone pack just use its name.
        if len(results) > 1:
            unique = {r["name"] for r in results}
            group_name = next(iter(unique)) if len(unique) == 1 else clean_archive_name(Path(file_path).stem)
        else:
            group_name = results[0]["name"]
        self._record_group(group_name, os.path.basename(file_path), results)
        return results

    def remove(self, kind, uuid):
        """Remove a pack entry from world JSON. Returns True if removed."""
        entries = self._load_world_json(kind)
        new_entries = [e for e in entries if e.get("pack_id") != uuid]
        if len(new_entries) == len(entries):
            return False
        self._save_world_json(kind, new_entries)
        return True
