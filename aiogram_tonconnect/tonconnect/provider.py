from pytonconnect.provider import BridgeProvider as BaseBridgeProvider


class BridgeProvider(BaseBridgeProvider):

    def _generate_tg_universal_url(self, universal_url: str, request: dict):
        universal_url = universal_url.replace("attach=wallet", "startattach=")
        link = self._generate_regular_universal_url('about:blank', request)
        link_params = link.split('?')[1]
        start_attach = (
                'tonconnect-' + link_params
                .replace('.', '%2E')
                .replace('-', '%2D')
                .replace('_', '%5F')
                .replace('&', '-')
                .replace('=', '__')
                .replace('%', '--')
                .replace('+', '')
        )
        return universal_url + start_attach
