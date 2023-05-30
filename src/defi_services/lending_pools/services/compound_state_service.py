from defi_services.lending_pools.services.cream_state_service import CreamStateService
from defi_services.utils.batch_queries_service import add_rpc_call, decode_data_response
from defi_services.abis.lending_pool.cream_lens_abi import CREAM_LENS_ABI
from defi_services.abis.lending_pool.cream_comptroller_abi import CREAM_COMPTROLLER_ABI


class CompoundStateService(CreamStateService):
    def __init__(self, provider_uri: str):
        super().__init__(provider_uri)

    def get_rewards_balance(
            self,
            wallet_address: str,
            lens_address: str,
            comptroller_address: str,
            pool_token: str,
            lens_abi: list = CREAM_LENS_ABI,
            block_number: int = "latest",
    ):
        list_rpc_call = []
        list_call_id = []
        fn_paras = [self.to_checksum(pool_token),
                    self.to_checksum(comptroller_address),
                    self.to_checksum(wallet_address)]
        add_rpc_call(abi=lens_abi,
                     fn_paras=fn_paras,
                     contract_address=lens_address,
                     fn_name="getCompBalanceMetadataExt", block_number=block_number,
                     list_call_id=list_call_id, list_rpc_call=list_rpc_call)
        get_reward_id = f"getCompBalanceMetadataExt_{lens_address}_{fn_paras}_{block_number}".lower()
        data_response = self.client_querier.sent_batch_to_provider(list_rpc_call, batch_size=100)
        decoded_data = decode_data_response(data_response, list_call_id)
        reward = decoded_data[get_reward_id][-1] / 10 ** 18
        return reward

    def get_apy_lending_pool(
            self,
            lens_address: str,
            comptroller_address: str,
            pool_token_price: float,
            lens_abi: list = CREAM_LENS_ABI,
            comptroller_abi: list = CREAM_COMPTROLLER_ABI,
            pool_decimals: int = 18,
            block_number: int = "latest",
            wrapped_native_token_price: float = 310
    ):
        tokens_interest_rates = dict()
        ctokens = self.get_all_markets(comptroller_address, comptroller_abi, block_number)
        list_rpc_call, list_call_id = self._encode_apy_lending_pool_function_call(
            lens_address, lens_abi, comptroller_address, comptroller_abi, ctokens, block_number)
        decode_data = self._decode_apy_lending_pool_function_call(
            list_rpc_call, list_call_id, lens_address, comptroller_address, ctokens, block_number,
            wrapped_native_token_price)
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


if __name__ == "__main__":
    import json
    from defi_services.lending_pools.lending_pools_info.ethereum.compound_eth import COMPOUND_ETH

    service = CompoundStateService(provider_uri="https://rpc.ankr.com/eth")
    reserve_info = service.get_reserves_info(
        lens_address=COMPOUND_ETH.get("lensAddress"),
        comptroller_address=COMPOUND_ETH.get("comptrollerAddress"),
        lens_abi=CREAM_LENS_ABI,
        comptroller_abi=CREAM_COMPTROLLER_ABI
    )
    with open("compound_bsc.json", "w") as f:
        f.write(json.dumps(reserve_info, indent=1))
