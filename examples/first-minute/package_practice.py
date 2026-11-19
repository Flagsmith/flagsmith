"""Package the offline drill reproducibly so its reviewed checksum can be verified."""

from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

root = Path(__file__).resolve().parent
archive = BytesIO()
entry = ZipInfo("first-minute.html", date_time=(1980, 1, 1, 0, 0, 0))
entry.create_system = 3
entry.external_attr = 0o100644 << 16
with ZipFile(archive, "w") as package:
    package.writestr(
        entry,
        (root / "dist/first-minute.html").read_bytes(),
        compress_type=ZIP_DEFLATED,
    )
(root / "media/first-minute.zip").write_bytes(archive.getvalue())
