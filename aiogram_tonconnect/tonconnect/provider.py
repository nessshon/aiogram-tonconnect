from pytonconnect.provider import BridgeProvider as BaseBridgeProvider
from pytonconnect.storage import IStorage


class BridgeProvider(BaseBridgeProvider):

    def __init__(self, storage: IStorage, wallet: dict, redirect_url: str = None) -> None:
        self.redirect_url = redirect_url
        super().__init__(storage, wallet)

    def _generate_tg_universal_url(self, universal_url: str, request: dict):
        universal_url = universal_url.replace("attach=wallet", "startattach=")
        link = self._generate_regular_universal_url('about:blank', request)
        link_params = link.split('?')[1]

        link_params += f"&ret={self.redirect_url}" if self.redirect_url else "&ret=back"

        start_attach = (
                'tonconnect-' + link_params
                .replace('.', '%2E')
                .replace('-', '%2D')
                .replace('_', '%5F')
                .replace('&', '-')
                .replace('=', '__')
                .replace('%', '--')
                .replace('+', '')
                .replace(':', '--3A')
                .replace('/', '--2F')
        )
        return universal_url + start_attach
