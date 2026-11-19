"""Fetch and verify the Google MediaPipe models used by KruGoZor."""
import hashlib
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

BASE = "https://storage.googleapis.com/mediapipe-models/"
MODELS = (
    ("face_landmarker/face_landmarker/float16/1/face_landmarker.task", 3758596,
     "64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff"),
    ("image_segmenter/selfie_segmenter/float16/1/selfie_segmenter.tflite", 249537,
     "191ac9529ae506ee0beefa6b2c945a172dab9d07d1e802a290a4e4038226658b"),
)


def fetch_model(root: Path, resource: str, size: int, sha256: str) -> None:
    destination = root / resource.rsplit("/", 1)[-1]
    if destination.exists():
        with destination.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != sha256:
            raise ValueError(f"{destination.name}: файл отличается от версии Google")
        print(f"{destination.name}: SHA-256 OK")
        return

    with urlopen(BASE + resource, timeout=30) as response:
        data = response.read(size + 1)
    if len(data) != size or hashlib.sha256(data).hexdigest() != sha256:
        raise ValueError(f"{destination.name}: скачанный файл не прошёл проверку SHA-256")

    with NamedTemporaryFile(dir=root, suffix=".download", delete=False) as stream:
        temporary = Path(stream.name)
    try:
        temporary.write_bytes(data)
        if destination.exists():
            raise FileExistsError(destination)
        temporary.rename(destination)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"{destination.name}: скачан и проверен")


if __name__ == "__main__":
    for resource, size, sha256 in MODELS:
        fetch_model(Path(__file__).resolve().parent, resource, size, sha256)
