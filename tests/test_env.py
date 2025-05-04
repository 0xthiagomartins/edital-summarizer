import os
import pytest
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse


@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables before running tests."""
    load_dotenv()


@pytest.fixture(scope="session")
def gemini_client():
    """Initialize Gemini client."""
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    model_name = os.getenv("MODEL", "gemini/gemini-1.5-pro").split("/")[-1]
    return genai.GenerativeModel(model_name)


def test_gemini_api_connection(gemini_client):
    """Test if we can successfully connect and get a response from Gemini."""
    try:
        response = gemini_client.generate_content(
            "Respond with 'OK' if you can read this message."
        )

        assert isinstance(response, GenerateContentResponse), "Invalid response type"
        assert response.text is not None, "Response text is None"
        assert len(response.text) > 0, "Response text is empty"

        print(f"\nGemini API Response: {response.text}")

    except Exception as e:
        pytest.fail(f"Failed to connect to Gemini API: {str(e)}")


def test_model_env_var():
    """Test if MODEL environment variable is set and valid."""
    model = os.getenv("MODEL")
    assert model is not None, "MODEL environment variable is not set"
    assert model in [
        "gemini/gemini-1.5-pro",
        "gemini/gemini-1.5-flash",
    ], f"Invalid MODEL value: {model}. Must be 'gemini/gemini-1.5-pro' or 'gemini/gemini-1.5-flash'"


def test_api_key_env_var():
    """Test if GEMINI_API_KEY environment variable is set and valid."""
    api_key = os.getenv("GEMINI_API_KEY")
    assert api_key is not None, "GEMINI_API_KEY environment variable is not set"
    assert len(api_key) > 0, "GEMINI_API_KEY cannot be empty"
    assert api_key.startswith("AI"), "GEMINI_API_KEY should start with 'AI'"
    assert len(api_key) > 20, "GEMINI_API_KEY seems too short to be valid"


def test_env_file_exists():
    """Test if .env file exists in project root."""
    from pathlib import Path

    env_path = Path(".env")
    assert env_path.exists(), ".env file not found in project root"
    assert env_path.is_file(), ".env is not a file"


def test_env_file_content():
    """Test if .env file contains required variables."""
    from pathlib import Path

    env_content = Path(".env").read_text()

    assert "MODEL=" in env_content, "MODEL variable not found in .env file"
    assert (
        "GEMINI_API_KEY=" in env_content
    ), "GEMINI_API_KEY variable not found in .env file"

    # Check if variables are not empty
    for line in env_content.splitlines():
        if line.startswith("MODEL="):
            assert len(line) > 6, "MODEL value is empty in .env file"
        elif line.startswith("GEMINI_API_KEY="):
            assert len(line) > 14, "GEMINI_API_KEY value is empty in .env file"
