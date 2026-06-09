#!/usr/bin/env python3
"""Pack a .bmxml into a self-contained PowerShell writer.

Browser downloads tend to corrupt .bmxml (re-encoding / BOM loss), so instead we
ship a PowerShell script that carries the exact bytes as gzip+base64 and writes
them back verbatim with WriteAllBytes. The script always round-trips (decode ==
original) before emitting, so what lands in Downloads is byte-identical.

Usage:
    python pack_ps1.py <song.bmxml> [out.ps1]

If out.ps1 is omitted, writes Write-<SongName>.ps1 next to the .bmxml.
The generated script writes the song into the user's Downloads folder.
"""
import sys, os, gzip, base64

def pack(bmxml_path, ps1_path=None, dest_name=None):
    raw = open(bmxml_path, "rb").read()
    name = dest_name or os.path.basename(bmxml_path)
    if ps1_path is None:
        stem = os.path.splitext(os.path.basename(bmxml_path))[0]
        ps1_path = os.path.join(os.path.dirname(os.path.abspath(bmxml_path)),
                                "Write-%s.ps1" % stem)

    b64 = base64.b64encode(gzip.compress(raw, 9)).decode()
    assert gzip.decompress(base64.b64decode(b64)) == raw, "round-trip mismatch"

    ps = "$ErrorActionPreference='Stop'\n$b64=@'\n" + b64 + "\n'@\n" + r"""$bytes=[Convert]::FromBase64String($b64)
$ms=New-Object System.IO.MemoryStream(,$bytes)
$gz=New-Object System.IO.Compression.GZipStream($ms,[IO.Compression.CompressionMode]::Decompress)
$out=New-Object System.IO.MemoryStream; $gz.CopyTo($out); $gz.Close()
$dest=Join-Path $env:USERPROFILE 'Downloads\__NAME__'
[IO.File]::WriteAllBytes($dest,$out.ToArray()); Write-Host "Wrote $dest ($($out.Length) bytes)"
""".replace("__NAME__", name)

    open(ps1_path, "w", encoding="utf-8").write(ps)
    print("WROTE %s (embeds %s, %d bytes)" % (ps1_path, name, len(raw)))
    return ps1_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    pack(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
