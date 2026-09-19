import os
import pytest
import tempfile
from app.services.storage import LocalStorage


def test_local_storage_crud():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorage(base_dir=tmpdir)
        filename = "test_folder/sample.txt"
        data = b"Hello, ContractLens!"

        # Save
        saved_path = storage.save(filename, data)
        assert os.path.exists(saved_path)
        assert storage.exists(filename)

        # Read
        content = storage.read(filename)
        assert content == data

        # Delete
        deleted = storage.delete(filename)
        assert deleted is True
        assert not storage.exists(filename)


def test_storage_path_traversal_protection():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorage(base_dir=tmpdir)
        with pytest.raises(ValueError, match="Path traversal detected"):
            storage.read("../../../etc/passwd")
