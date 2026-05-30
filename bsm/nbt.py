import struct


# ── Bedrock NBT codec (little-endian, uncompressed, with 8-byte header) ──────────
# Bedrock's level.dat is NOT like Java's: it has an 8-byte header (version + length)
# followed by little-endian, uncompressed NBT. This is a self-contained reader/writer
# so the packaged .exe needs no extra dependencies.
TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11
TAG_LONG_ARRAY = 12

TAG_NAMES = {
    TAG_BYTE: "Byte", TAG_SHORT: "Short", TAG_INT: "Int", TAG_LONG: "Long",
    TAG_FLOAT: "Float", TAG_DOUBLE: "Double", TAG_BYTE_ARRAY: "ByteArray",
    TAG_STRING: "String", TAG_LIST: "List", TAG_COMPOUND: "Compound",
    TAG_INT_ARRAY: "IntArray", TAG_LONG_ARRAY: "LongArray",
}
_INT_TYPES = (TAG_BYTE, TAG_SHORT, TAG_INT, TAG_LONG)
_FLOAT_TYPES = (TAG_FLOAT, TAG_DOUBLE)
_CONTAINER_TYPES = (TAG_COMPOUND, TAG_LIST)
_ARRAY_TYPES = (TAG_BYTE_ARRAY, TAG_INT_ARRAY, TAG_LONG_ARRAY)


class NbtTag:
    """A single NBT tag. value depends on type:
       compound -> list of [name, NbtTag]; list -> [elem_type, [NbtTag,...]];
       arrays -> list of int; scalars -> python value."""
    __slots__ = ("type", "value")

    def __init__(self, t, v):
        self.type = t
        self.value = v


class _Reader:
    def __init__(self, data):
        self.d = data
        self.i = 0

    def _u(self, fmt, size):
        v = struct.unpack_from(fmt, self.d, self.i)[0]
        self.i += size
        return v

    def string(self):
        n = self._u("<H", 2)
        s = self.d[self.i:self.i + n]
        self.i += n
        return s.decode("utf-8", errors="replace")

    def payload(self, t):
        if t == TAG_BYTE:   return self._u("<b", 1)
        if t == TAG_SHORT:  return self._u("<h", 2)
        if t == TAG_INT:    return self._u("<i", 4)
        if t == TAG_LONG:   return self._u("<q", 8)
        if t == TAG_FLOAT:  return self._u("<f", 4)
        if t == TAG_DOUBLE: return self._u("<d", 8)
        if t == TAG_STRING: return self.string()
        if t == TAG_BYTE_ARRAY:
            n = self._u("<i", 4)
            arr = list(struct.unpack_from("<%db" % n, self.d, self.i)); self.i += n
            return arr
        if t == TAG_INT_ARRAY:
            n = self._u("<i", 4)
            arr = list(struct.unpack_from("<%di" % n, self.d, self.i)); self.i += 4 * n
            return arr
        if t == TAG_LONG_ARRAY:
            n = self._u("<i", 4)
            arr = list(struct.unpack_from("<%dq" % n, self.d, self.i)); self.i += 8 * n
            return arr
        if t == TAG_LIST:
            et = self._u("<b", 1)
            n = self._u("<i", 4)
            return [et, [NbtTag(et, self.payload(et)) for _ in range(n)]]
        if t == TAG_COMPOUND:
            entries = []
            while True:
                ct = self._u("<b", 1)
                if ct == TAG_END:
                    break
                name = self.string()
                entries.append([name, NbtTag(ct, self.payload(ct))])
            return entries
        raise ValueError(f"Tipo NBT desconocido: {t}")

    def named(self):
        t = self._u("<b", 1)
        name = self.string()
        return name, NbtTag(t, self.payload(t))


class _Writer:
    def __init__(self):
        self.b = bytearray()

    def string(self, s):
        e = s.encode("utf-8")
        self.b += struct.pack("<H", len(e))
        self.b += e

    def payload(self, t, v):
        if t == TAG_BYTE:     self.b += struct.pack("<b", int(v))
        elif t == TAG_SHORT:  self.b += struct.pack("<h", int(v))
        elif t == TAG_INT:    self.b += struct.pack("<i", int(v))
        elif t == TAG_LONG:   self.b += struct.pack("<q", int(v))
        elif t == TAG_FLOAT:  self.b += struct.pack("<f", float(v))
        elif t == TAG_DOUBLE: self.b += struct.pack("<d", float(v))
        elif t == TAG_STRING: self.string(v)
        elif t == TAG_BYTE_ARRAY:
            self.b += struct.pack("<i", len(v)) + struct.pack("<%db" % len(v), *v)
        elif t == TAG_INT_ARRAY:
            self.b += struct.pack("<i", len(v)) + struct.pack("<%di" % len(v), *v)
        elif t == TAG_LONG_ARRAY:
            self.b += struct.pack("<i", len(v)) + struct.pack("<%dq" % len(v), *v)
        elif t == TAG_LIST:
            et, items = v
            self.b += struct.pack("<b", et) + struct.pack("<i", len(items))
            for it in items:
                self.payload(et, it.value)
        elif t == TAG_COMPOUND:
            for name, tag in v:
                self.b += struct.pack("<b", tag.type)
                self.string(name)
                self.payload(tag.type, tag.value)
            self.b += struct.pack("<b", TAG_END)
        else:
            raise ValueError(f"Tipo NBT desconocido: {t}")

    def named(self, name, tag):
        self.b += struct.pack("<b", tag.type)
        self.string(name)
        self.payload(tag.type, tag.value)


def load_level_dat(path):
    """Returns (version, root_name, root_tag)."""
    with open(path, "rb") as f:
        raw = f.read()
    version = struct.unpack_from("<i", raw, 0)[0]
    length = struct.unpack_from("<i", raw, 4)[0]
    body = raw[8:8 + length] if length else raw[8:]
    name, root = _Reader(body).named()
    return version, name, root


def save_level_dat(path, version, root_name, root_tag):
    w = _Writer()
    w.named(root_name, root_tag)
    payload = bytes(w.b)
    out = struct.pack("<i", version) + struct.pack("<i", len(payload)) + payload
    with open(path, "wb") as f:
        f.write(out)


def comp_get(comp, key):
    for n, tag in comp.value:
        if n == key:
            return tag
    return None


def comp_set_byte(comp, key, val):
    for entry in comp.value:
        if entry[0] == key:
            entry[1] = NbtTag(TAG_BYTE, 1 if val else 0)
            return
    comp.value.append([key, NbtTag(TAG_BYTE, 1 if val else 0)])
