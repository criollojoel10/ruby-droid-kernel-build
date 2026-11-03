#!/usr/bin/env python3
"""Minimal OTA payload.bin partition extractor (no protobuf module needed)."""
import bz2, lzma, struct, subprocess, sys, io

def varint(buf, i):
    shift = 0
    val = 0
    while True:
        b = buf[i]
        i += 1
        val |= (b & 0x7F) << shift
        if not b & 0x80:
            return val, i
        shift += 7

def fields(buf):
    i = 0
    n = len(buf)
    while i < n:
        key, i = varint(buf, i)
        fno, wt = key >> 3, key & 7
        if wt == 0:
            v, i = varint(buf, i)
            yield fno, wt, v
        elif wt == 2:
            ln, i = varint(buf, i)
            yield fno, wt, buf[i:i + ln]
            i += ln
        elif wt == 5:
            yield fno, wt, buf[i:i + 4]
            i += 4
        elif wt == 1:
            yield fno, wt, buf[i:i + 8]
            i += 8
        else:
            raise SystemExit("bad wiretype %d" % wt)

def parse_manifest(m):
    parts = []
    for fno, wt, val in fields(m):
        if fno == 13 and wt == 2:
            name = None
            ops = []
            for f2, w2, v2 in fields(val):
                if f2 == 1 and w2 == 2:
                    name = v2.decode()
                elif f2 == 8 and w2 == 2:
                    t = off = ln = 0
                    dst = []
                    for f3, w3, v3 in fields(v2):
                        if f3 == 1:
                            t = v3
                        elif f3 == 2:
                            off = v3
                        elif f3 == 3:
                            ln = v3
                        elif f3 == 6 and w3 == 2:
                            sb = nb = 0
                            for f4, w4, v4 in fields(v3):
                                if f4 == 1:
                                    sb = v4
                                elif f4 == 2:
                                    nb = v4
                            dst.append((sb, nb))
                    ops.append((t, off, ln, dst))
            parts.append((name, ops))
    return parts

def decomp(t, data):
    if t == 0:
        return data
    if t == 1:
        return bz2.decompress(data)
    if t == 6 or t == 7:
        return b""
    if t == 8:
        return lzma.decompress(data)
    if t == 14:
        return subprocess.run(["zstd", "-dc"], input=data,
                              stdout=subprocess.PIPE, check=True).stdout
    raise SystemExit("unsupported op type %d" % t)

def main(payload, want):
    with open(payload, "rb") as f:
        hdr = f.read(4)
        if hdr != b"CrAU":
            raise SystemExit("not a payload (magic %r)" % hdr)
        ver, = struct.unpack(">Q", f.read(8))
        msz, = struct.unpack(">Q", f.read(8))
        if ver != 2:
            raise SystemExit("unexpected payload version %d" % ver)
        man = f.read(msz)
        base = f.tell()
        parts = parse_manifest(man)
        print("partitions:", " ".join(p[0] for p in parts), file=sys.stderr)
        for name, ops in parts:
            if name not in want:
                continue
            size = max((sb + nb for _, _, _, dst in ops for sb, nb in dst),
                       default=0) * 4096
            out = io.BytesIO(b"\0" * size)
            for t, off, ln, dst in ops:
                f.seek(base + off)
                data = f.read(ln)
                raw = decomp(t, data)
                pos = 0
                for sb, nb in dst:
                    chunk = raw[pos:pos + nb * 4096]
                    pos += nb * 4096
                    out.seek(sb * 4096)
                    out.write(chunk)
            with open(name + ".img", "wb") as o:
                o.write(out.getvalue())
            print("wrote %s.img (%d bytes)" % (name, size), file=sys.stderr)

if __name__ == "__main__":
    main(sys.argv[1], set(sys.argv[2:]))
