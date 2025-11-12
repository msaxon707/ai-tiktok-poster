import json
import os
import tempfile
import unittest
from pathlib import Path

from app.config import load_config
from app.upload import VideoUploader


class VideoUploadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        tmp_path = Path(self.tmp.name)
        os.environ["DATA_ROOT"] = str(tmp_path / "data")
        os.environ["BACKUPS_DIR"] = str(tmp_path / "backups")
        os.environ.pop("TIKTOK_SESSION_ID", None)

    def tearDown(self) -> None:
        for key in ("DATA_ROOT", "BACKUPS_DIR"):
            os.environ.pop(key, None)
        self.tmp.cleanup()

    def test_upload_skips_without_session_and_leaves_registry_empty(self) -> None:
        config = load_config()
        uploader = VideoUploader(config)

        video_path = Path(self.tmp.name) / "video.mp4"
        video_path.write_bytes(b"0" * 10)

        result = uploader.upload(video_path, "Test caption")
        self.assertFalse(result)

        registry_file = config.paths.backups_dir / "uploads_registry.json"
        if registry_file.exists():
            data = json.loads(registry_file.read_text())
            self.assertEqual(data, {})


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
