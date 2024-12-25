import pytest
from datetime import datetime
from pathlib import Path
from app.core.email import (
    send_email,
    send_verification_email,
    send_password_reset_email,
    send_password_change_notification,
    send_welcome_email
)

pytestmark = pytest.mark.asyncio

class TestEmailService:
    async def test_send_email_success(self, mocker):
        """Test successful email sending."""
        mock_fastmail = mocker.patch("app.core.email.fastmail.send_message")
        mock_fastmail.return_value = None
        
        result = await send_email(
            email_to="test@example.com",
            subject="Test Email",
            template_name="verification_email",
            template_data={
                "verification_url": "http://test/verify",
                "app_name": "Test App",
                "support_email": "support@test.com"
            }
        )
        
        assert result is True
        mock_fastmail.assert_called_once()

    async def test_send_email_failure(self, mocker):
        """Test email sending failure."""
        mock_fastmail = mocker.patch("app.core.email.fastmail.send_message")
        mock_fastmail.side_effect = Exception("SMTP Error")
        
        result = await send_email(
            email_to="test@example.com",
            subject="Test Email",
            template_name="verification_email",
            template_data={
                "verification_url": "http://test/verify",
                "app_name": "Test App",
                "support_email": "support@test.com"
            }
        )
        
        assert result is False

    async def test_verification_email(self, mocker):
        """Test verification email sending."""
        mock_send_email = mocker.patch("app.core.email.send_email")
        mock_send_email.return_value = True
        
        result = await send_verification_email(
            email_to="test@example.com",
            token="test-token"
        )
        
        assert result is True
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args[1]
        assert call_args["template_name"] == "verification_email"
        assert "verification_url" in call_args["template_data"]

    async def test_password_reset_email(self, mocker):
        """Test password reset email sending."""
        mock_send_email = mocker.patch("app.core.email.send_email")
        mock_send_email.return_value = True
        
        result = await send_password_reset_email(
            email_to="test@example.com",
            token="test-token"
        )
        
        assert result is True
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args[1]
        assert call_args["template_name"] == "reset_password_email"
        assert "reset_url" in call_args["template_data"]

    async def test_welcome_email(self, mocker):
        """Test welcome email sending."""
        mock_send_email = mocker.patch("app.core.email.send_email")
        mock_send_email.return_value = True
        
        result = await send_welcome_email(
            email_to="test@example.com",
            user_name="Test User"
        )
        
        assert result is True
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args[1]
        assert call_args["template_name"] == "welcome_email"
        assert call_args["template_data"]["user_name"] == "Test User"

    async def test_password_change_notification(self, mocker):
        """Test password change notification email."""
        mock_send_email = mocker.patch("app.core.email.send_email")
        mock_send_email.return_value = True
        
        result = await send_password_change_notification(
            email_to="test@example.com"
        )
        
        assert result is True
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args[1]
        assert call_args["template_name"] == "password_changed_email"

    def test_email_templates_exist(self):
        """Test that all required email templates exist."""
        template_dir = Path(__file__).parent.parent / "app" / "templates"
        required_templates = [
            "verification_email.html",
            "reset_password_email.html",
            "welcome_email.html",
            "password_changed_email.html",
            "base_email.html"
        ]
        
        for template in required_templates:
            assert (template_dir / template).exists(), f"Template {template} non trovato"

    def test_template_rendering(self, mocker):
        """Test that templates can be rendered correctly."""
        env = mocker.patch("app.core.email.template_env")
        mock_template = mocker.MagicMock()
        env.get_template.return_value = mock_template
        
        async def test():
            await send_verification_email("test@example.com", "test-token")
            mock_template.render.assert_called_once()
            template_data = mock_template.render.call_args[1]
            assert "verification_url" in template_data
            assert "app_name" in template_data
            assert "support_email" in template_data
        
        pytest.mark.asyncio(test()) 