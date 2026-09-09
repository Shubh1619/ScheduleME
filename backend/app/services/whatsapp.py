import requests

from ..config import get_settings


class WhatsAppError(Exception):
    def __init__(self, message: str, code: int | None = None, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.retry_after = retry_after if retry_after is not None else (
            self._default_backoff_for(code) if code is not None else None
        )

    @staticmethod
    def _default_backoff_for(code: int) -> float | None:
        if code in WhatsAppService.RATE_LIMIT_CODES or code == 429:
            return 60.0
        return None


class WhatsAppService:
    RATE_LIMIT_CODES = {130429, 131047, 131026, 613}
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def _graph_base(self) -> str:
        return f"https://graph.facebook.com/{self.settings.whatsapp_api_version}"

    def is_configured(self) -> bool:
        return bool(
            self.settings.whatsapp_app_id
            and self.settings.whatsapp_app_secret
            and self.settings.whatsapp_redirect_uri
        )

    def build_onboarding_url(self, state: str) -> str:
        if not self.is_configured():
            raise WhatsAppError(
                "WhatsApp app is not configured (WHATSAPP_APP_ID / WHATSAPP_APP_SECRET / WHATSAPP_REDIRECT_URI)"
            )
        params = {
            "client_id": self.settings.whatsapp_app_id,
            "redirect_uri": self.settings.whatsapp_redirect_uri,
            "response_type": "code",
            "scope": self.settings.whatsapp_scope,
            "state": state,
        }
        if self.settings.whatsapp_config_id:
            params["config_id"] = self.settings.whatsapp_config_id
        query = "&".join(f"{key}={requests.utils.quote(str(value), safe=':')}" for key, value in params.items())
        return f"https://www.facebook.com/{self.settings.whatsapp_api_version}/dialog/oauth?{query}"

    def exchange_code(self, code: str) -> str:
        if not self.is_configured():
            raise WhatsAppError("WhatsApp app is not configured")
        response = requests.post(
            f"{self._graph_base}/oauth/access_token",
            data={
                "client_id": self.settings.whatsapp_app_id,
                "client_secret": self.settings.whatsapp_app_secret,
                "redirect_uri": self.settings.whatsapp_redirect_uri,
                "code": code,
            },
            timeout=15,
        )
        if response.status_code != 200:
            raise WhatsAppError(f"Token exchange failed {response.status_code}: {response.text}")
        return response.json()["access_token"]

    def fetch_whatsapp_account(self, access_token: str) -> dict:
        debug = requests.get(
            f"{self._graph_base}/debug_token",
            params={"input_token": access_token, "access_token": access_token},
            timeout=15,
        )
        if debug.status_code != 200:
            raise WhatsAppError(f"debug_token failed {debug.status_code}: {debug.text}")
        user_id = debug.json()["data"].get("user_id")
        if not user_id:
            raise WhatsAppError("Could not resolve system user from token")

        waba_response = requests.get(
            f"{self._graph_base}/{user_id}/owned_whatsapp_business_accounts",
            params={"access_token": access_token},
            timeout=15,
        )
        if waba_response.status_code != 200:
            raise WhatsAppError(f"WABA lookup failed {waba_response.status_code}: {waba_response.text}")
        waba_list = waba_response.json().get("data", [])
        if not waba_list:
            raise WhatsAppError("No WhatsApp Business Account found for this user")
        waba_id = waba_list[0]["id"]

        phone_response = requests.get(
            f"{self._graph_base}/{waba_id}/phone_numbers",
            params={"access_token": access_token},
            timeout=15,
        )
        if phone_response.status_code != 200:
            raise WhatsAppError(f"Phone lookup failed {phone_response.status_code}: {phone_response.text}")
        phone_list = phone_response.json().get("data", [])
        if not phone_list:
            raise WhatsAppError("No phone numbers found in the WhatsApp Business Account")
        phone = phone_list[0]

        return {
            "waba_id": waba_id,
            "phone_number_id": phone["id"],
            "phone_number": phone.get("display_phone_number", ""),
            "display_name": phone.get("verified_name", ""),
        }

    def send_text_message(self, phone_number_id: str, access_token: str, to: str, body: str) -> str:
        response = requests.post(
            f"{self._graph_base}/{phone_number_id}/messages",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": body},
            },
            timeout=15,
        )
        if response.status_code != 200:
            code = None
            try:
                error = response.json().get("error", {})
                code = error.get("code")
            except ValueError:
                pass
            raise WhatsAppError(
                f"WhatsApp API error {response.status_code}: {response.text}",
                code=code,
            )
        return response.json()["messages"][0]["id"]