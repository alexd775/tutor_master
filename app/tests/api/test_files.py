import pytest
from pathlib import Path
from app.core.config import settings

@pytest.fixture
def test_file(tmp_path):
    """Create a test file."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("Test content")
    return file_path

def test_upload_file(client, superuser_token_headers, test_file):
    """Test file upload."""
    with open(test_file, "rb") as f:
        response = client.post(
            f"{settings.API_V1_STR}/files/upload",
            headers=superuser_token_headers,
            files={"file": ("test.txt", f, "text/plain")},
            data={
                "title": "Test File",
                "description": "Test Description"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test File"
    assert data["filename"] == "test.txt"
    assert data["content_type"] == "text/plain"

def test_upload_invalid_file(client, superuser_token_headers, test_file):
    """Test uploading file with invalid extension."""
    test_file = Path(test_file).with_suffix('.invalid')
    with open(test_file, "wb") as f:
        f.write(b"Invalid content")
    
    with open(test_file, "rb") as f:
        response = client.post(
            f"{settings.API_V1_STR}/files/upload",
            headers=superuser_token_headers,
            files={"file": ("test.invalid", f, "application/octet-stream")},
            data={"title": "Invalid File"}
        )
    
    assert response.status_code == 400
    assert "File type not allowed" in response.json()["detail"]

def test_get_file(client, superuser_token_headers, db, test_file):
    """Test file retrieval."""
    # First upload a file
    with open(test_file, "rb") as f:
        upload_response = client.post(
            f"{settings.API_V1_STR}/files/upload",
            headers=superuser_token_headers,
            files={"file": ("test.txt", f, "text/plain")},
            data={"title": "Test File"}
        )
    
    file_id = upload_response.json()["id"]
    
    # Now try to get it
    response = client.get(
        f"{settings.API_V1_STR}/files/{file_id}",
        headers=superuser_token_headers
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8" 

def test_list_files(client, superuser_token_headers, db, test_file):
    """Test listing files."""
    # First upload some files
    files_to_create = 3
    for i in range(files_to_create):
        with open(test_file, "rb") as f:
            client.post(
                f"{settings.API_V1_STR}/files/upload",
                headers=superuser_token_headers,
                files={"file": (f"test_{i}.txt", f, "text/plain")},
                data={"title": f"Test File {i}"}
            )
    
    # List files
    response = client.get(
        f"{settings.API_V1_STR}/files",
        headers=superuser_token_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) == files_to_create
    assert data["total"] == files_to_create
    
    # Test pagination
    response = client.get(
        f"{settings.API_V1_STR}/files?skip=1&limit=1",
        headers=superuser_token_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total"] == files_to_create  # Total should still be the same 