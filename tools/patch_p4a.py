"""Menyisipkan <receiver> widget ke template AndroidManifest milik python-for-android.

Dipakai oleh workflow GitHub Actions sebelum build:
    python3 tools/patch_p4a.py <folder python-for-android> widget_res/receiver.xml

Kenapa begini: python-for-android tidak punya opsi untuk menambah elemen di dalam
<application> (opsi --extra-manifest-application-xml hanya usulan, belum pernah
digabung), sehingga template-nya yang diubah langsung.
"""
import pathlib
import sys

MARK = "</application>"


def main():
    root = pathlib.Path(sys.argv[1])
    xml = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8").strip()
    xml = "\n".join("    " + line for line in xml.splitlines())
    patched = 0
    for f in sorted(root.rglob("AndroidManifest.tmpl.xml")):
        text = f.read_text(encoding="utf-8")
        if "ShiftWidgetProvider" in text:
            patched += 1
            continue
        if text.count(MARK) != 1:
            print("lewati (tidak ada tepat satu %s): %s" % (MARK, f))
            continue
        f.write_text(text.replace(MARK, xml + "\n    " + MARK), encoding="utf-8")
        print("dipatch:", f)
        patched += 1
    if not patched:
        sys.exit("GAGAL: tidak ada AndroidManifest.tmpl.xml yang bisa dipatch di %s" % root)


if __name__ == "__main__":
    main()
