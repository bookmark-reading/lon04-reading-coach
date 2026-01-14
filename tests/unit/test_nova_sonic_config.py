"""Simple unit test for Nova Sonic Reading Agent configuration."""

import pytest
from src.infrastructure.nova_sonic_reading_agent import NovaSonicConfig


def test_nova_config_creation():
    """Test that Nova Sonic configuration can be created."""
    config = NovaSonicConfig(
        region="us-west-2",
        model_id="amazon.nova-sonic-v1:0",
        aws_access_key_id="test-key",
        aws_secret_access_key="test-secret",
        aws_session_token="test-token",
    )
    
    assert config.region == "us-west-2"
    assert config.model_id == "amazon.nova-sonic-v1:0"
    assert config.aws_access_key_id == "test-key"
    assert config.aws_secret_access_key == "test-secret"
    assert config.aws_session_token == "test-token"


def test_nova_config_defaults():
    """Test Nova Sonic configuration defaults."""
    config = NovaSonicConfig()
    
    assert config.region == "us-east-1"
    assert config.model_id == "amazon.nova-sonic-v1:0"
    assert config.max_tokens == 1024
    assert config.temperature == 0.7
    assert config.top_p == 0.9
    assert config.sample_rate_hz == 16000
    assert config.channels == 1
    assert config.aws_access_key_id is None
    assert config.aws_secret_access_key is None
    assert config.aws_session_token is None


def test_nova_config_with_credentials():
    """Test Nova Sonic configuration with custom credentials."""
    config = NovaSonicConfig(
        region="us-east-1",
        aws_access_key_id="ASIAZRSR2DGJJIP45VAR",
        aws_secret_access_key="secret123",
        aws_session_token="token456",
        max_tokens=2048,
        temperature=0.8,
    )
    
    assert config.region == "us-east-1"
    assert config.aws_access_key_id == "ASIAZRSR2DGJJIP45VAR"
    assert config.aws_secret_access_key == "secret123"
    assert config.aws_session_token == "token456"
    assert config.max_tokens == 2048
    assert config.temperature == 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
