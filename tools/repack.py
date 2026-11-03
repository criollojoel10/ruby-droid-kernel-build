#!/usr/bin/env python3
"""Repack an Android boot.img v2 (MTK) replacing only the gzip kernel."""
import gzip, struct, sys

PAGE = 2048
HDR_OFF = 8  # kernel_size field offset in the boot header


def pad(n, p=PAGE):
    return (n + p - 1) // p * p


def main(orig_path, image_path, out_path):
    boot = open(orig_path, "rb").read()
    page_size, = struct.unpack("<I", boot[36:40])
    assert page_size == PAGE, "unexpected page size %d" % page_size
    old_kernel_size, = struct.unpack("<I", boot[8:12])
    ramdisk_size, = struct.unpack("<I", boot[16:20])
    second_size, = struct.unpack("<I", boot[24:28])
    rec_dtbo_size, = struct.unpack("<I", boot[1632:1636])
    header_size, = struct.unpack("<I", boot[1644:1648])
    dtb_size, = struct.unpack("<I", boot[1648:1652])
    rest_off = PAGE + pad(old_kernel_size)
    rest = boot[rest_off:]
    print("orig: kernel=%d ramdisk=%d second=%d rec_dtbo=%d dtb=%d header_size=%d rest=%d"
          % (old_kernel_size, ramdisk_size, second_size, rec_dtbo_size,
             dtb_size, header_size, len(rest)))

    with open(image_path, "rb") as f:
        image = f.read()
    gz = gzip.compress(image, compresslevel=9, mtime=0)
    print("Image %d bytes -> gzip %d bytes" % (len(image), len(gz)))

    header = bytearray(boot[:PAGE])
    header[HDR_OFF:HDR_OFF + 4] = struct.pack("<I", len(gz))
    out = bytes(header) + gz
    out += b"\0" * (pad(len(out), page_size) - len(out))
    out += rest


    print("rest starts with: %r"
          % (rest[:4],))
    out = out + b"\0" * (len(boot) - len(out))
    open(out_path, "wb").write(out)
    print("wrote %s (%d bytes)" % (out_path, len(out)))


if __name__ == "__main__":
    main(*sys.argv[1:4])
