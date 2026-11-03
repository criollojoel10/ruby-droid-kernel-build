# ruby-droid-kernel-build

Bootable kernel builds for the **Redmi Note 12 Pro / Pro+ 5G / Discovery Edition**
(codename `ruby`, MTK Dimensity 1200 / MT6877) with **KernelSU-Next** and
**DroidSpaces** support, based on the RubyxLabs `lineage-24.0` kernel tree
(6.6.143) and matching the Infinity X 4.1 ROM kernel vermagic.

## Device

| Item | Value |
|------|-------|
| Device | Redmi Note 12 Pro / Pro+ 5G / Discovery Edition |
| Codename | `ruby` |
| SoC | MediaTek Dimensity 1200 (MT6877) |
| ROM tested | Infinity X 4.1 (Android 15) |
| Kernel | `6.6.143-android15-8-4k-Singularity-gbe1aa8ecec91` |
| Root | KernelSU-Next |
| Container runtime | DroidSpaces (SYSVIPC kABI variant `6_7_8`) |

## Downloads

- **Boot image (flashable)**: https://drive.google.com/open?id=1PdotuRdrOswusBQLQ0FD89mGhaYIFSFj
- **vbmeta (stock)**: https://drive.google.com/open?id=1GTctpuZ6mMH7woC2Wb812jdNtpvpDMfd
- **Raw Image**: https://drive.google.com/open?id=1PdotuRdrOswusBQLQ0FD89mGhaYIFSFj (see folder `ruby-kernel-ksu-droidspaces`)

The current build enables **IPv6 NAT** (`CONFIG_IP6_NF_NAT=y` and
`CONFIG_IP6_NF_TARGET_MASQUERADE=y`), so `--net=nat` containers get IPv6 too.
Build run: https://github.com/criollojoel10/ruby-droid-kernel-build/actions/runs/41656352913

## Flashing

From a host with `fastboot` (device in bootloader):

```sh
fastboot flash boot boot-ksu-droidspaces-ruby.img
fastboot reboot
```

If AVB rejects the modified image:

```sh
fastboot --disable-verity --disable-verification flash vbmeta vbmeta-ruby-stock.img
fastboot flash boot boot-ksu-droidspaces-ruby.img
fastboot reboot
```

After boot, verify:

```sh
uname -r   # 6.6.143-android15-8-4k-Singularity-gbe1aa8ecec91
```

## DroidSpaces

All required/recommended/optional checks pass except IPv6 NAT in the first build;
the in-progress build enables it. Run the checker on the device:

```sh
droidspaces check
```

## Build from source (GitHub Actions)

The workflow `.github/workflows/build.yml`:

1. Checks out `RubyxLabs/android_kernel_xiaomi_mt6877` at the ROM commit
   `be1aa8ecec91d1793024db1d7a88e621b74e633e` (for exact vermagic parity).
2. Sets up KernelSU-Next and applies the DroidSpaces SYSVIPC kABI patch
   (tries `6_7_8` -> `3_4_5` -> `1_2_3`).
3. Applies `ruby_defconfig` + DroidSpaces + KSU config via `scripts/config`.
4. Self-heals missing `#include` paths (up to 25 attempts).
5. Vendors `mtk_iommu_ext.h` and pins `CONFIG_MTK_IOMMU_PGTABLE_EXT=32`.
6. Pins the release string (no `-dirty`) and verifies it matches the ROM.

Trigger manually:

```sh
gh workflow run build.yml -R criollojoel10/ruby-droid-kernel-build
```

## Repacking a boot image

`tools/magiskboot` + `tools/repack.py` rebuild an MTK `boot.img` (v2) from the
ROM's `boot.img`, replacing only the kernel. See `tools/repack.py`.

## License

Kernel sources are GPL-2.0 (RubyxLabs). Build scripts and tooling in this repo
are provided as-is.
