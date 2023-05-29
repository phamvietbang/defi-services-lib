import logging
from query_state_lib.client.client_querier import ClientQuerier
from web3 import Web3
from web3.middleware import geth_poa_middleware
from defi_services.abis.erc20_abi import ERC20_ABI
from defi_services.utils.batch_queries_service import add_rpc_call, decode_data_response
from defi_services.utils.graph_operations import BlockTimestampGraph, GraphOperations
from defi_services.utils.market_service import MarketService
from defi_services.utils.memory_storage import MemoryStorage

_LOGGER = logging.getLogger("StateService")


class StateService:
    def __init__(self, provider_uri: str):
        self._w3 = Web3(Web3.HTTPProvider(provider_uri))
        self.client_querier = ClientQuerier(provider_url=provider_uri)
        self._w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        timestamp_graph = BlockTimestampGraph(self._w3)
        self._market_service = MarketService()
        self._graph_operations = GraphOperations(timestamp_graph)
        self.memory_storage = MemoryStorage.get_instance()

    def get_latest_block(self):
        return self._w3.eth.block_number

    def get_block_nearest_timestamp(self, timestamp: int):
        try:
            start_block_bounds = self._graph_operations.get_bounds_for_y_coordinate(timestamp)
        except Exception as ex:
            _LOGGER.exception(ex)
            start_block_bounds = (0, 0)
        return start_block_bounds[0]

    def to_checksum(self, address: str):
        return self._w3.toChecksumAddress(address.lower())

    def balance_of(self, address: str, token: str, block_number: int = 'latest'):
        token_contract = self._w3.eth.contract(self.to_checksum(token), abi=ERC20_ABI)
        decimals = token_contract.functions.decimals().call()
        balance = token_contract.functions.balanceOf(self.to_checksum(address)).call(
            block_identifier=block_number)
        return balance / 10 ** decimals

    def total_supply(self, token_address: str, block_number: int = 'latest'):
        token_contract = self._w3.eth.contract(self.to_checksum(token_address), abi=ERC20_ABI)
        decimals = token_contract.functions.decimals().call()
        total_supply = token_contract.functions.totalSupply().call(block_identifier=block_number) / 10 ** decimals
        return total_supply

    def decimals(self, token_address: str):
        token_contract = self._w3.eth.contract(self.to_checksum(token_address), abi=ERC20_ABI)
        decimals = token_contract.functions.decimals().call()
        return decimals

    def decimals_of_token_list(self, token_addresses: list, block_number: int = 'latest'):
        list_rpc_call, list_call_id = [], []
        for token_address in token_addresses:
            add_rpc_call(
                abi=ERC20_ABI, fn_name='decimals', contract_address=self.to_checksum(token_address),
                block_number=block_number, list_rpc_call=list_rpc_call, list_call_id=list_call_id
            )
        data_response = self.client_querier.sent_batch_to_provider(list_rpc_call, batch_size=100)
        decoded_data = decode_data_response(data_response, list_call_id)
        result = {}
        for token_address in token_addresses:
            decimals_call_id = f'decimals_{token_address}_{block_number}'.lower()
            result[token_address.lower()] = decoded_data.get(decimals_call_id)

        return result

    def total_supply_of_token_list(self, token_addresses: list, block_number: int = 'latest'):
        list_rpc_call, list_call_id = [], []
        for token_address in token_addresses:
            add_rpc_call(
                abi=ERC20_ABI, fn_name='totalSupply', contract_address=self.to_checksum(token_address),
                block_number=block_number, list_rpc_call=list_rpc_call, list_call_id=list_call_id
            )
        data_response = self.client_querier.sent_batch_to_provider(list_rpc_call, batch_size=100)
        decoded_data = decode_data_response(data_response, list_call_id)
        result = {}
        for token_address in token_addresses:
            total_supply_call_id = f'totalSupply_{token_address}_{block_number}'.lower()
            result[token_address.lower()] = decoded_data.get(total_supply_call_id)

        return result