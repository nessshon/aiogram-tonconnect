import asyncio
import json
from typing import Optional

from aiohttp import ClientSession
from aiohttp_sse_client import client as sse_client
from pytonconnect.crypto import SessionCrypto

from pytonconnect.provider import BridgeProvider as BaseBridgeProvider
from pytonconnect.provider import BridgeGateway as BaseBridgeGateway
from pytonconnect.provider._bridge_session import BridgeSession  # noqa
from pytonconnect.storage import IStorage
from pytonconnect.logger import _LOGGER  # noqa


class BridgeGateway(BaseBridgeGateway):

    def __init__(
            self,
            storage: IStorage,
            bridge_url: str,
            session_id: str,
            listener,
            errors_listener,
            tonapi_token: Optional[str] = None,
    ) -> None:
        super().__init__(storage, bridge_url, session_id, listener, errors_listener)
        self.tonapi_token = tonapi_token

    async def send(self, request: str, receiver_public_key: str, topic: str, ttl: int = None):
        bridge_base = self._bridge_url.rstrip('/')
        bridge_url = f'{bridge_base}/{self.POST_PATH}?client_id={self._session_id}'
        bridge_url += f'&to={receiver_public_key}'
        bridge_url += f'&ttl={ttl if ttl else self.DEFAULT_TTL}'
        bridge_url += f'&topic={topic}'
        headers = {'Content-type': 'text/plain;charset=UTF-8'}

        if "tonapi" in bridge_base and self.tonapi_token:
            headers["Authorization"] = f"Bearer {self.tonapi_token}"

        async with ClientSession(headers=headers) as session:
            async with session.post(bridge_url, data=request):
                pass

    async def register_session(self) -> bool:
        if self._is_closed:
            return False

        bridge_base = self._bridge_url.rstrip('/')
        bridge_url = f'{bridge_base}/{self.SSE_PATH}?client_id={self._session_id}'

        last_event_id = await self._storage.get_item(IStorage.KEY_LAST_EVENT_ID)
        if last_event_id:
            bridge_url += f'&last_event_id={last_event_id}'
        _LOGGER.debug(f'Bridge url -> {bridge_url}')

        if self._handle_listen is not None:
            self._handle_listen.cancel()

        loop = asyncio.get_running_loop()
        resolve = loop.create_future()

        session = ClientSession()
        if "tonapi" in bridge_base and self.tonapi_token:
            headers = {"Authorization": f"Bearer {self.tonapi_token}"}
            session.headers.update(headers)

        self._event_source = sse_client.EventSource(
            bridge_url,
            timeout=-1,
            session=session,
            on_error=self._errors_handler
        )
        self._handle_listen = asyncio.create_task(self.listen_event_source(resolve))

        return await resolve


class BridgeProvider(BaseBridgeProvider):
    _gateway: BridgeGateway

    def __init__(self, storage: IStorage, wallet: dict, redirect_url: str = None, tonapi_token: str = None) -> None:
        self.redirect_url = redirect_url
        self.tonapi_token = tonapi_token
        super().__init__(storage, wallet)

    async def connect(self, request: dict):
        self._close_gateways()
        session_crypto = SessionCrypto()

        bridge_url = ''
        universal_url = BridgeProvider.STANDART_UNIVERSAL_URL

        if isinstance(self._wallet, dict):
            bridge_url = self._wallet['bridge_url']
            if 'universal_url' in self._wallet:
                universal_url = self._wallet['universal_url']

            self._gateway = BridgeGateway(self._storage, bridge_url, session_crypto.session_id, self._gateway_listener,
                                          self._gateway_errors_listener, tonapi_token=self.tonapi_token)

            await self._gateway.register_session()

        self._session.session_crypto = session_crypto
        self._session.bridge_url = bridge_url

        return self._generate_universal_url(universal_url, request)

    async def restore_connection(self):
        self._close_gateways()

        connection = await self._storage.get_item(IStorage.KEY_CONNECTION)
        if not connection:
            return False
        connection = json.loads(connection)

        if 'session' not in connection:
            return False
        self._session = BridgeSession(connection['session'])

        self._gateway = BridgeGateway(self._storage, self._session.bridge_url, self._session.session_crypto.session_id,
                                      self._gateway_listener, self._gateway_errors_listener,
                                      tonapi_token=self.tonapi_token)

        await self._gateway.register_session()

        for listener in self._listeners:
            listener(connection['connect_event'])

        return True

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
