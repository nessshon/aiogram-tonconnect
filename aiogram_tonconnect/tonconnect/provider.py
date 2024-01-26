import json

from pytonconnect.provider import BridgeProvider as BaseBridgeProvider
from pytonconnect.storage import IStorage
from pytonconnect.logger import _LOGGER  # noqa


class BridgeProvider(BaseBridgeProvider):

    def __init__(self, storage: IStorage, wallet: dict, redirect_url: str = None) -> None:
        self.redirect_url = redirect_url
        super().__init__(storage, wallet)

    async def _gateway_listener(self, bridge_incoming_message):
        wallet_message = json.loads(
            self._session.session_crypto.decrypt(bridge_incoming_message['message'], bridge_incoming_message['from'])
        )

        _LOGGER.debug(f'Wallet message received: {wallet_message}')

        if 'event' not in wallet_message:
            if 'id' in wallet_message:
                id_ = wallet_message['id']
                if id_ not in self._pending_requests:
                    _LOGGER.debug(f"Response id {id_} doesn't match any request's id")
                    return

                self._pending_requests[id_].set_result(wallet_message)
                del self._pending_requests[id_]
            return

        if 'id' in wallet_message:
            id_ = int(wallet_message['id'])
            connection = json.loads(await self._storage.get_item(IStorage.KEY_CONNECTION, '{}'))
            last_id = connection['last_wallet_event_id'] if 'last_wallet_event_id' in connection else 0

            if last_id and id_ <= last_id:
                id_ = id_ - 1 if id_ == last_id else id_ - 2
                _LOGGER.error(
                    f'Received event id (={id_}) must be greater than stored last wallet event id (={last_id})')

            if 'event' in wallet_message and wallet_message['event'] != 'connect':
                connection['last_wallet_event_id'] = id_
                await self._storage.set_item(IStorage.KEY_CONNECTION, json.dumps(connection))

        # self.listeners might be modified in the event handler
        listeners = self._listeners.copy()

        if wallet_message['event'] == 'connect':
            await self._update_session(wallet_message, bridge_incoming_message['from'])

        elif wallet_message['event'] == 'disconnect':
            await self._remove_session()

        for listener in listeners:
            listener(wallet_message)

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
