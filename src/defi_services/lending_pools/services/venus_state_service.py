from defi_services.abis.erc20_abi import ERC20_ABI
from defi_services.abis.lending_pool.ctoken_abi import CTOKEN_ABI
from defi_services.abis.lending_pool.venus_comptroller_abi import VENUS_COMPTROLLER_ABI
from defi_services.abis.lending_pool.venus_lens_abi import VENUS_LENS_ABI
from defi_services.constants.contract_address import ContractAddresses, AbnormalVenusPool, WrappedNativeTokens
from defi_services.lending_pools.services.cream_state_service import CreamStateService
from defi_services.utils.batch_queries_service import add_rpc_call, decode_data_response


class VenusStateService(CreamStateService):
    def __init__(self, provider_uri):
        super().__init__(provider_uri)

    def vtoken_metadata_all(
            self, lens_address: str, lens_abi: list, token_addresses: list, block_number: int = 'latest'):
        lens_contract = self._w3.eth.contract(
            address=self.to_checksum(lens_address), abi=lens_abi
        )
        tokens = [self.to_checksum(i) for i in token_addresses]
        reserve_tokens_info = lens_contract.functions.vTokenMetadataAll(tokens).call(block_identifier=block_number)
        return reserve_tokens_info

    def vtoken_underlying_price_all(
            self, lens_address: str, lens_abi: list, token_addresses: list, bnb_price: float,
            block_number: int = 'latest'):
        lens_contract = self._w3.eth.contract(
            address=self.to_checksum(lens_address), abi=lens_abi
        )
        tokens = [self.to_checksum(i) for i in token_addresses]
        reserve_tokens_info = lens_contract.functions.vTokenUnderlyingPriceAll(tokens).call(
            block_identifier=block_number)
        for price_token in reserve_tokens_info:
            reserve_tokens_info[price_token[0].lower()] = price_token[1] * bnb_price
        return reserve_tokens_info

    def get_reserves_info(
            self,
            comptroller_address: str,
            comptroller_abi: list,
            lens_address: str,
            lens_abi: list,
            block_number: int = 'latest'):
        ctokens = self.get_all_markets(comptroller_address, comptroller_abi, block_number)
        metadata = self.vtoken_metadata_all(lens_address, lens_abi, ctokens, block_number)
        reserves_info = {}
        for data in metadata:
            underlying = data[11].lower()
            ctoken = data[0].lower()
            lt = data[10] / 10 ** 18
            reserves_info[underlying] = {
                "cToken": ctoken,
                "liquidationThreshold": lt
            }

        return reserves_info

    def get_token_speed(
            self, token_addresses: list, comptroller: str,
            comptroller_abi: list = VENUS_COMPTROLLER_ABI, block_number: int = 'latest'):
        list_rpc_call = []
        list_call_id = []
        for token_address in token_addresses:
            add_rpc_call(
                abi=comptroller, fn_name='venusSpeeds', contract_address=comptroller_abi,
                block_number=block_number, fn_paras=token_address, list_rpc_call=list_rpc_call,
                list_call_id=list_call_id
            )
        data_response = self.client_querier.sent_batch_to_provider(list_rpc_call, batch_size=100)
        decoded_data = decode_data_response(data_response, list_call_id)
        result = {}
        for token_address in token_addresses:
            get_asset_data_call_id = f'venusSpeeds_{comptroller}_{token_address}_{block_number}'.lower()
            result[token_address.lower()] = decoded_data.get(get_asset_data_call_id)

        return result

    @staticmethod
    def _encode_apy_lending_pool_function_call(
            lens_address: str,
            lens_abi: list,
            comptroller_address: str,
            comptroller_abi: list,
            token_addresses: list,
            block_number: int = "latest"
    ):
        list_call_id, list_rpc_call = [], []
        for token_address in token_addresses:
            add_rpc_call(abi=lens_abi, contract_address=lens_address, fn_paras=token_address, block_number=block_number,
                         list_call_id=list_call_id, list_rpc_call=list_rpc_call, fn_name="vTokenMetadata")
            add_rpc_call(abi=lens_abi, contract_address=lens_address, fn_paras=token_address,
                         block_number=block_number,
                         list_call_id=list_call_id, list_rpc_call=list_rpc_call, fn_name="vTokenUnderlyingPrice")
            add_rpc_call(
                abi=comptroller_abi, fn_name='venusSpeeds', contract_address=comptroller_address,
                block_number=block_number, fn_paras=token_address, list_rpc_call=list_rpc_call,
                list_call_id=list_call_id
            )
        return list_rpc_call, list_call_id

    def _decode_apy_lending_pool_function_call(
            self,
            list_rpc_call: list,
            list_call_id: list,
            lens_address: str,
            comptroller_address: str,
            token_addresses: list,
            block_number: int = "latest",
            wrapped_native_token_price: float = 310
    ):
        data_response = self.client_querier.sent_batch_to_provider(list_rpc_call, batch_size=100)
        decoded_data = decode_data_response(data_response, list_call_id)
        ctoken_speeds, borrow_paused_tokens, mint_paused_tokens = {}, {}, {}
        underlying_prices, reserve_tokens_info = {}, []
        for token_address in token_addresses:
            lower_address = token_address.lower()
            metadata_id = f"vTokenMetadata_{lens_address}_{token_address}_{block_number}".lower()
            speeds_call_id = f'venusSpeeds_{comptroller_address}_{token_address}_{block_number}'.lower()
            reserve_tokens_info.append(decoded_data.get(metadata_id))
            underlying_id = f"vTokenUnderlyingPrice_{lens_address}_{token_address}_{block_number}".lower()
            price_token = decoded_data.get(underlying_id)
            underlying_decimals = decoded_data.get(metadata_id)[-1]
            underlying_prices[lower_address] = price_token[1]
            if lower_address in AbnormalVenusPool.decimals.keys():
                underlying_prices[lower_address] /= 10 ** AbnormalVenusPool.decimals.get(lower_address)
            elif underlying_decimals == 8:
                underlying_prices[lower_address] /= 10 ** 20
            elif underlying_decimals == 6:
                underlying_prices[lower_address] /= 10 ** 24
            ctoken_speeds[token_address.lower()] = decoded_data.get(speeds_call_id)
            borrow_paused_tokens[token_address.lower()] = False
            mint_paused_tokens[token_address.lower()] = False

        return {
            "reserve_tokens_info": reserve_tokens_info,
            "ctoken_speeds": ctoken_speeds,
            "borrow_paused_tokens": borrow_paused_tokens,
            "mint_paused_tokens": mint_paused_tokens,
            "underlying_prices": underlying_prices
        }

    def get_apy_lending_pool(
            self,
            lens_address: str,
            comptroller_address: str,
            pool_token_price: float,
            lens_abi: list = VENUS_LENS_ABI,
            comptroller_abi: list = VENUS_COMPTROLLER_ABI,
            pool_decimals: int = 18,
            block_number: int = "latest",
            wrapped_native_token_price: float = 310
    ):
        tokens_interest_rates = dict()
        ctokens = self.get_all_markets(comptroller_address, comptroller_abi, block_number)
        for token in ctokens:
            if token in [ContractAddresses.LUNA.lower(), ContractAddresses.UST.lower(), ContractAddresses.LUNA,
                         ContractAddresses.UST]:
                ctokens.remove(token)
        list_rpc_call, list_call_id = self._encode_apy_lending_pool_function_call(
            lens_address, lens_abi, comptroller_address, comptroller_abi, ctokens, block_number)
        decode_data = self._decode_apy_lending_pool_function_call(
            list_rpc_call, list_call_id, lens_address, comptroller_address, ctokens, block_number)
        mint_paused_tokens = decode_data["mint_paused_tokens"]
        borrow_paused_tokens = decode_data["borrow_paused_tokens"]
        reserve_tokens_info = decode_data["reserve_tokens_info"]
        ctoken_speeds = decode_data["ctoken_speeds"]
        for data in reserve_tokens_info:
            address = data[0].lower()
            underlying_token_price = float(decode_data["underlying_prices"][address]) / 10 ** int(data[13])
            token_info = {
                "token": address,
                "token_decimals": data[12],
                "borrow_rate": data[3],
                "supply_rate": data[2],
                "supply": data[7],
                "borrow": data[5],
                "exchange_rate": data[1],
                "underlying": data[11].lower(),
                "underlying_price": underlying_token_price,
                "underlying_decimals": data[13],
                "speed": ctoken_speeds[address]
            }
            underlying_token = token_info['underlying']
            token_info["mint_paused"] = mint_paused_tokens[address]
            token_info["borrow_paused"] = borrow_paused_tokens[address]
            tokens_interest_rates[underlying_token] = self._calculate_interest_rates(
                token_info, pool_decimals, pool_token_price)

        return tokens_interest_rates

    def get_rewards_balance(
            self,
            wallet_address: str,
            lens_address: str,
            comptroller_address: str,
            pool_token: str = None,
            lens_abi: list = VENUS_LENS_ABI,
            block_number: int = "latest",
    ):
        list_rpc_call = []
        list_call_id = []
        fn_paras = [self.to_checksum(wallet_address), self.to_checksum(comptroller_address)]
        add_rpc_call(abi=lens_abi,
                     fn_paras=fn_paras, block_number=block_number,
                     contract_address=lens_address, fn_name="pendingVenus",
                     list_call_id=list_call_id, list_rpc_call=list_rpc_call)
        get_reward_id = f"pendingVenus_{lens_address}_{fn_paras}_{block_number}".lower()
        data_response = self.client_querier.sent_batch_to_provider(list_rpc_call, batch_size=100)
        decoded_data = decode_data_response(data_response, list_call_id)
        reward = decoded_data[get_reward_id] / 10 ** 18
        return reward

    def get_wallet_deposit_borrow_balance(
            self,
            wallet_address: str,
            lens_address: str,
            reserves_info: dict,
            lens_abi: list = VENUS_LENS_ABI,
            block_number: int = "latest",
            wrapped_native_token_price: float = 310,
            wrapped_native_token: str = None
    ):
        list_rpc_call = []
        list_call_id = []
        for token in reserves_info:
            underlying = token
            value = reserves_info[token]
            if token == WrappedNativeTokens.NATIVE_TOKEN:
                underlying = wrapped_native_token
            add_rpc_call(abi=lens_abi, contract_address=lens_address, fn_paras=value["cToken"],
                         block_number=block_number,
                         list_call_id=list_call_id, list_rpc_call=list_rpc_call, fn_name="vTokenUnderlyingPrice")
            add_rpc_call(abi=CTOKEN_ABI, contract_address=value["cToken"], fn_name="borrowBalanceCurrent",
                         block_number=block_number,
                         fn_paras=wallet_address, list_call_id=list_call_id, list_rpc_call=list_rpc_call)
            add_rpc_call(abi=CTOKEN_ABI, contract_address=value["cToken"], fn_name="balanceOfUnderlying",
                         block_number=block_number,
                         fn_paras=wallet_address, list_call_id=list_call_id, list_rpc_call=list_rpc_call)
            add_rpc_call(abi=ERC20_ABI, contract_address=underlying, fn_name="decimals", block_number=block_number,
                         list_call_id=list_call_id, list_rpc_call=list_rpc_call)

        data_response = self.client_querier.sent_batch_to_provider(list_rpc_call, batch_size=100)
        decoded_data = decode_data_response(data_response, list_call_id)
        total_borrow, result = 0, {
            "borrow_amount_in_usd": 0,
            "deposit_amount_in_usd": 0,
            "health_factor": 0,
            'reserves_data': {}
        }
        for token in reserves_info:
            underlying = token
            value = reserves_info[token]
            if token == WrappedNativeTokens.NATIVE_TOKEN:
                underlying = wrapped_native_token
            get_total_deposit_id = f"balanceOfUnderlying_{value['cToken']}_{wallet_address}_{block_number}".lower()
            get_total_borrow_id = f"borrowBalanceCurrent_{value['cToken']}_{wallet_address}_{block_number}".lower()
            get_decimals_id = f"decimals_{underlying}_{block_number}".lower()
            decimals = decoded_data[get_decimals_id]
            deposit_amount = decoded_data[get_total_deposit_id] / 10 ** decimals
            borrow_amount = decoded_data[get_total_borrow_id] / 10 ** decimals
            get_underlying_token_price = f"vTokenUnderlyingPrice_{lens_address}_{value['cToken']}_{block_number}".lower()
            token_price = decoded_data.get(get_underlying_token_price)[1] / 10 ** decimals
            if value['cToken'] in AbnormalVenusPool.decimals.keys():
                token_price /= 10 ** AbnormalVenusPool.decimals.get(value['cToken'])

            deposit_amount_in_usd = deposit_amount * token_price
            borrow_amount_in_usd = borrow_amount * token_price
            total_borrow += borrow_amount_in_usd
            result['health_factor'] += deposit_amount_in_usd * value["liquidationThreshold"]
            result['borrow_amount_in_usd'] += borrow_amount_in_usd
            result['deposit_amount_in_usd'] += deposit_amount_in_usd
            if (borrow_amount > 0) or (deposit_amount > 0):
                result['reserves_data'][token] = {
                    "borrow_amount": borrow_amount,
                    "borrow_amount_in_usd": borrow_amount_in_usd,
                    "deposit_amount": deposit_amount,
                    "deposit_amount_in_usd": deposit_amount_in_usd,
                }
        if total_borrow != 0:
            result['health_factor'] /= total_borrow
        else:
            result['health_factor'] = 100
        return result


if __name__ == "__main__":
    import json
    from defi_services.lending_pools.lending_pools_info.bsc.venus_bsc import VENUS_BSC

    service = VenusStateService(provider_uri="https://rpc.ankr.com/bsc")
    reserve_info = service.get_reserves_info(
        lens_address=VENUS_BSC.get("lensAddress"),
        comptroller_address=VENUS_BSC.get("comptrollerAddress"),
        lens_abi=VENUS_LENS_ABI,
        comptroller_abi=VENUS_COMPTROLLER_ABI
    )
    with open("venus_bsc.json", "w") as f:
        f.write(json.dumps(reserve_info, indent=1))
