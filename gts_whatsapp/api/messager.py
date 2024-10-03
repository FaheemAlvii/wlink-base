from typing import Any, Optional, Dict
from PIL import Image
import requests
import time
import qrcode
import base64
import mimetypes
import re


BASE_URL: str = 'https://whatapi.geektechsol.com'


class Messager:
    def __init__(self,
                 client_secret: str,
                 webhook_url: str = 'https://webhook.site/2778607e-15e4-4af3-95a2-ee91f371be8e') -> None:
        self.client_secret: str = client_secret
        self.webhook_url: str = webhook_url
        self.opened_chat_id: Optional[str] = None
        self.number: Optional[str] = None

    @staticmethod
    def validate_number(number):
        matches = re.match(r'^\+?(\d{1,3})?[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}$', str(number))
        if not matches:
            raise ChildProcessError('Invalid phone number!')

    def set_receiver(self, number: str) -> None:
        self.validate_number(number)
        self.number = number.removeprefix('+').replace(' ', '')
        self.opened_chat_id = f'{self.number}@c.us'

    def send_message(self, message: str) -> None:
        self.validate_number(self.number)
        return self.request('sendText', self.get_payload(text=message, session=''))

    def reply(self, _message_id: str, text: str) -> None:
        file: Dict[str, str] = {"mimetype": "image/jpeg", "filename": "image.jpeg", "url": '#'}
        payload: Dict[str, Any] = self.get_payload(file=file, caption=f'Here is a picture of a {text}')
        return self.request('sendImage', payload)

    def send_seen(self, message_id: str, participant: str) -> None:
        return self.request('sendSeen', self.get_payload(messageId=message_id, participant=participant))

    def logout(self) -> None:
        return self.request('sessions/logout', {"name": '<session>'}, return_value=False)

    def start_typing(self) -> None:
        return self.request('startTyping', self.get_payload())

    def stop_typing(self) -> None:
        return self.request('stopTyping', self.get_payload())

    def typing(self, seconds: int) -> None:
        self.start_typing()
        time.sleep(seconds)
        self.stop_typing()

    def send_file(self, data: bytes, filename: str = 'image', filetype: str = 'jpg', caption: str = '', include_prefix: bool = True, already_in_base64: bool = False, link_path: str = 'sendFile') -> None:
        self.validate_number(self.number)
        base64_file: str = self.string_to_base64(data) if not already_in_base64 else data
        mimetype: str = self.get_mimetype(filetype)

        prefix = f'data:{mimetype};base64,' if include_prefix else ''

        payload: dict[str, Any] = self.get_payload(file={"mimetype": mimetype,
                                                         "filename": f'{filename}.{filetype}',
                                                         "data": f"{prefix}{base64_file}"}, caption=caption)

        return self.request(link_path, payload)

    def send_pdf(self, data: bytes, filename: str = 'document', caption: str = '', already_in_base64: bool = False):
        return self.send_file(data, filename, 'pdf', caption, False, already_in_base64=already_in_base64)

    def send_image(self, data: bytes, filename: str = 'image', caption: str = '', filetype: str = 'jpg', already_in_base64: bool = False):
        return self.send_file(data, filename, filetype, caption, True, already_in_base64=already_in_base64)

    def request(self, place: str, payload: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, log_request: bool = False, request_type='post', return_value: bool = True, **kwargs: Any) -> None:
        headers = self.get_headers() if headers is None else headers
        payload = self.get_payload() if payload is None else payload

        if log_request:
            print(f'[GTS-Whatsapp] Sent request with headers: {headers}, And with payload: {payload}')

        func = getattr(requests, request_type)
        response: requests.Response = func(f'{BASE_URL}/api/{place}', headers=headers, json=payload, **kwargs)

        try:
            response.raise_for_status()
        except Exception as e:
            if str(e).__contains__('Failed to establish a new connection: [Errno -3] Temporary failure in '):
                raise ChildProcessError("You're sending too many requests! Please try again later.")
            raise

        if return_value:
            return response.json()

    def get_headers(self) -> Dict[str, str]:
        return {'ClientSecret': self.client_secret, 'Content-Type': 'application/json'}

    def get_payload(self, chat_info: bool = True, **kwargs: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {'chatId': self.opened_chat_id, 'session': self.client_secret} if chat_info else {}
        payload.update(kwargs)

        return payload

    def authenticate(self) -> Image.Image:
        self.logout()
        self.start_session()
        return self.text_to_qrcode_image(self.get_qrcode())

    @staticmethod
    def text_to_qrcode_image(text: str) -> Image.Image:
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(text)
        qr.make(fit=True)

        return qr.make_image(fill='black', back_color='white')

    @staticmethod
    def string_to_base64(text: bytes) -> str:
        text_base64 = base64.b64encode(text)
        return text_base64.decode('utf-8')

    def is_logged_in(self) -> bool:
        headers = {'ClientSecret': self.client_secret, 'Content-Type': 'application/json'}
        request = requests.get(BASE_URL + f'/api/sessions/<session>/me', headers=headers)

        if request.status_code == 500:
            return False

        try:
            info = request.json()
        except requests.JSONDecodeError:
            return False

        if info == {'error': 'Invalid ClientSecret'}:
            raise ChildProcessError("Your client secret is invalid. Check again.")

        return info.get('status', 'LOGGED OUT') == 'WORKING'

    @staticmethod
    def get_mimetype(extension: str) -> str:
        return mimetypes.guess_type(f"file.{extension}")[0]

    def start_session(self) -> None:
        """
        Starts a whatsapp session. Each device can have a session. Session's
        initially don't have any information, But scanning a qr code will set up the session and
        insert passwords, keys, etc
        """
        payload: Dict[str, Any] = {
            "name": '',
            "config": {
                "proxy": None,
                "noweb": {
                    "store": {
                        "enabled": True,
                        "fullSync": False
                    }
                },
                "webhooks": [
                    {
                        "url": self.webhook_url,
                        "events": [
                            "message",
                            "session.status"
                        ],
                        "hmac": None,
                        "retries": None,
                        "customHeaders": None
                    }
                ],
                "debug": False
            }
        }

        self.request('sessions/start', payload)

    def get_qrcode(self) -> Optional[str]:
        while True:
            response: requests.Response = requests.get(
                url=f'{BASE_URL}/api/<session>/auth/qr?format=raw',
                headers=self.get_headers()
            )

            result: Dict[str, Any] = response.json()

            if 'error' in list(result.keys()) and result['error'] == 'Unprocessable Entity':
                time.sleep(5)
                continue

            if response.status_code != 200:
                raise ChildProcessError(f"Failed to fetch QR Code. Status code: {response.status_code}, Response: \n{response.json()}")

            return response.json().get('value')

    @property
    def requests_info(self):
        return self.request('usage', payload=self.get_payload(), headers=self.get_headers(), request_type='get')