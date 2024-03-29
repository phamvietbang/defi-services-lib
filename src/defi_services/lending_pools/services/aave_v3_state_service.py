from defi_services.abis.erc20_abi import ERC20_ABI
from defi_services.abis.lending_pool.aave_v3_oracle_abi import AAVE_V3_ORACLE_ABI
from defi_services.abis.lending_pool.aave_v3_lending_pool_abi import AAVE_V3_LENDING_POOL_ABI
from defi_services.constants.db_constant import DBConst
from defi_services.constants.time_constant import TimeConstants
from defi_services.lending_pools.services.trava_state_service import TravaStateService
from defi_services.utils.batch_queries_service import add_rpc_call, decode_data_response
from defi_services.abis.lending_pool.aave_v3_incentives_abi import AAVE_V3_INCENTIVES_ABI


class AaveV3StateService(TravaStateService):
    def __init__(self, provider_uri: str):
        super().__init__(provider_uri)

    def get_rewards_list(self, incentive_address: str, incentive_abi: list, block_number: int = "latest"):
        contract = self._w3.eth.contract(address=self.to_checksum(incentive_address), abi=incentive_abi)
        return contract.functions.getRewardsList().call(block_identifier=block_number)

    def get_reserves_list(self, pool_address: str, pool_abi: list = AAVE_V3_LENDING_POOL_ABI,
                          block_number: int = 'latest'):
        contract = self._w3.eth.contract(address=self.to_checksum(pool_address), abi=pool_abi)
        return contract.functions.getReservesList().call(block_identifier=block_number)

    def get_reserve_data(self, pool_address: str, token_address: str,
                         pool_abi: list = AAVE_V3_LENDING_POOL_ABI, block_number: int = 'latest'):
        contract = self._w3.eth.contract(address=self.to_checksum(pool_address), abi=pool_abi)
        return contract.functions.getReserveData(self.to_checksum(token_address)).call(block_identifier=block_number)

    def get_reserve_data_of_token_list(self, pool_address: str, token_addresses: list,
                                       pool_abi: list = AAVE_V3_LENDING_POOL_ABI, block_number: int = 'latest'):
        list_rpc_call, list_call_id = [], []
        for token_address in token_addresses:
            add_rpc_call(
                abi=pool_abi, fn_name='getReserveData', contract_address=pool_address,
                block_number=block_number, fn_paras=token_address,
                list_rpc_call=list_rpc_call, list_call_id=list_call_id)

        data_response = self.client_querier.sent_batch_to_provider(list_rpc_call, batch_size=100)
        decoded_data = decode_data_response(data_response, list_call_id)
        result = {}
        for token_address in token_addresses:
            get_reserve_data_call_id = f'getReserveData_{pool_address}_{token_address}_{block_number}'.lower()
            result[token_address.lower()] = decoded_data.get(get_reserve_data_call_id)

        return result

    def get_asset_data(self, stake_incentive_address: str, token_address: str,
                       stake_incentive_abi: list = AAVE_V3_INCENTIVES_ABI, block_number: int = 'latest'):
        contract = self._w3.eth.contract(address=self.to_checksum(stake_incentive_address), abi=stake_incentive_abi)
        return contract.functions.getAssetData(self.to_checksum(token_address)).call(block_identifier=block_number)

    def get_asset_data_of_token_list(
            self, incentive_address: str, token_addresses: list, rewards_list: list = None,
            incentive_abi: list = AAVE_V3_INCENTIVES_ABI, block_number: int = 'latest'):
        list_rpc_call, list_call_id = [], []
        for token_address in token_addresses:
            for reward_address in rewards_list:
                fn_paras = [self.to_checksum(token_address), self.to_checksum(reward_address)]
                add_rpc_call(
                    abi=incentive_abi, fn_name='getRewardsData', contract_address=incentive_address,
                    block_number=block_number, fn_paras=fn_paras, list_rpc_call=list_rpc_call,
                    list_call_id=list_call_id

                )
        data_response = self.client_querier.sent_batch_to_provider(list_rpc_call, batch_size=100)
        decoded_data = decode_data_response(data_response, list_call_id)
        result = {}
        for token_address in token_addresses:
            result[token_address.lower()] = {}
            for reward_address in rewards_list:
                fn_paras = [self.to_checksum(token_address), self.to_checksum(reward_address)]
                get_reserve_data_call_id = f'getRewardsData_{incentive_address}_{fn_paras}_{block_number}'.lower()
                result[token_address.lower()][reward_address] = decoded_data.get(get_reserve_data_call_id)

        return result

    def get_assets_price(
            self,
            oracle_address: str,
            oracle_abi: list,
            reserves: list,
            block_number: int = 'latest',
            pool_decimals: int = 8
    ):
        contract = self._w3.eth.contract(address=self.to_checksum(oracle_address), abi=oracle_abi)
        tokens = [self.to_checksum(i) for i in reserves]
        prices = contract.functions.getAssetsPrices(tokens).call(block_identifier=block_number)
        result = {}
        for i in range(len(reserves)):
            result[reserves[i].lower()] = prices[i] / 10 ** pool_decimals

        return result

    def get_reserves_info(self, pool_address: str, pool_abi: list, block_number: int = "latest"):
        reserves_list = self.get_reserves_list(pool_address, pool_abi, block_number)
        reserves_data = self.get_reserve_data_of_token_list(pool_address, reserves_list, pool_abi, block_number)
        reserves_info = {}
        for key, value in reserves_data.items():
            reserves_info[key] = {}
            reserves_info[key]["tToken"] = value[8]
            reserves_info[key]["sdToken"] = value[9]
            reserves_info[key]["dToken"] = value[10]
            risk_param = bin(value[0][0])[2:]
            reserves_info[key]["liquidationThreshold"] = int(risk_param[-31:-16], 2) / 10 ** 4
        return reserves_info

    def _encode_apy_lending_pool_function_call(
            self,
            pool_address: str,
            pool_abi: list,
            reserves_list: list,
            stake_incentive_address: str = None,
            stake_incentive_abi: list = None,
            oracle_address: str = None,
            oracle_abi: list = None,
            block_number: int = "latest",
    ):
        list_rpc_call, list_call_id = [], []
        for token_address in reserves_list:
            add_rpc_call(
                abi=pool_abi, fn_name='getReserveData', contract_address=pool_address,
                block_number=block_number, fn_paras=token_address,
                list_rpc_call=list_rpc_call, list_call_id=list_call_id)
            add_rpc_call(
                abi=ERC20_ABI, fn_name='decimals', contract_address=self.to_checksum(token_address),
                block_number=block_number, list_rpc_call=list_rpc_call, list_call_id=list_call_id
            )

        return list_rpc_call, list_call_id

    def _decode_apy_lending_pool_function_call(
            self,
            list_rpc_call: list,
            list_call_id: list,
            pool_address: str,
            reserves_list: list,
            stake_incentive_address: str = None,
            oracle_address: str = None,
            block_number: int = "latest",
    ):
        data_response = self.client_querier.sent_batch_to_provider(list_rpc_call, batch_size=100)
        decoded_data = decode_data_response(data_response, list_call_id)
        reserves_data = {}
        for token in reserves_list:
            get_reserve_data_call_id = f'getReserveData_{pool_address}_{token}_{block_number}'.lower()
            reserves_data[token.lower()] = decoded_data.get(get_reserve_data_call_id)

        interest_rate, ttokens, debt_tokens, decimals = {}, {}, {}, {}
        for token_address in reserves_list:
            lower_address = token_address.lower()
            reserve_data = reserves_data[lower_address]
            interest_rate[lower_address] = {
                DBConst.deposit_apy: float(reserve_data[2]) / 10 ** 27,
                DBConst.borrow_apy: float(reserve_data[4]) / 10 ** 27,
                DBConst.stable_borrow_apy: float(reserve_data[5]) / 10 ** 27
            }
            ttoken = reserve_data[8].lower()
            debt_token = reserve_data[10].lower()
            ttokens[lower_address] = ttoken
            debt_tokens[lower_address] = debt_token
            decimals_call_id = f'decimals_{token_address}_{block_number}'.lower()
            decimals[lower_address] = decoded_data.get(decimals_call_id)

        return {
            "decimals": decimals,
            "ttokens": ttokens,
            "debt_tokens": debt_tokens,
            "interest_rate": interest_rate
        }

    def get_apy_lending_pool(
            self,
            pool_address: str,
            incentive_address: str,
            oracle_address: str,
            oracle_abi: list = AAVE_V3_ORACLE_ABI,
            pool_abi: list = AAVE_V3_LENDING_POOL_ABI,
            incentive_abi: list = AAVE_V3_INCENTIVES_ABI,
            rewards_list: list = None,
            reserves_info: dict = None,
            token_prices: dict = None,
            pool_token_price: float = 1,
            block_number: int = 'latest',
            pool_decimals: int = 8,
            wrapped_native_token_price: float = 1,
    ):
        if not reserves_info:
            reserves_info = self.get_reserves_info(pool_address, pool_abi, block_number)

        reserves_list = list(reserves_info.keys())
        token_prices = self.get_assets_price(oracle_address, oracle_abi, reserves_list, block_number, pool_decimals)
        list_rpc_call, list_call_id = self._encode_apy_lending_pool_function_call(
            pool_address, pool_abi, reserves_list, incentive_address, incentive_abi,
            oracle_address, oracle_abi, block_number,
        )
        # Decode data
        decoded_data = self._decode_apy_lending_pool_function_call(
            list_rpc_call, list_call_id, pool_address,
            reserves_list, incentive_address, oracle_address, block_number
        )
        interest_rate = decoded_data["interest_rate"]
        ttokens = decoded_data["ttokens"]
        debt_tokens = decoded_data["debt_tokens"]
        decimals = decoded_data["decimals"]
        debt_and_t_tokens = list(debt_tokens.values()) + list(ttokens.values())
        total_supply_tokens = self.total_supply_of_token_list(debt_and_t_tokens)
        asset_data_tokens = self.get_asset_data_of_token_list(
            incentive_address, debt_and_t_tokens, rewards_list, incentive_abi, block_number)

        lower_addresses = [i.lower() for i in reserves_list]
        for token_address in lower_addresses:
            ttoken = ttokens.get(token_address)
            debt_token = debt_tokens.get(token_address)
            decimal = decimals.get(token_address)
            total_supply_t = total_supply_tokens.get(ttoken)
            total_supply_d = total_supply_tokens.get(debt_token)
            total_supply_t = total_supply_t * wrapped_native_token_price / 10 ** decimal
            total_supply_d = total_supply_d * wrapped_native_token_price / 10 ** decimal
            token_price = token_prices.get(token_address)
            interest_rate[token_address].update({
                "utilization": total_supply_d / total_supply_t,
            })
            if rewards_list:
                interest_rate[token_address][DBConst.reward_deposit_apy] = {}
                interest_rate[token_address][DBConst.reward_borrow_apy] = {}
                asset_data_t = asset_data_tokens.get(ttoken)
                asset_data_d = asset_data_tokens.get(debt_token)
                # update deposit, borrow apy
                for reward_address in rewards_list:
                    eps_t = asset_data_t[reward_address][1] / 10 ** 18
                    eps_d = asset_data_d[reward_address][1] / 10 ** 18
                    if total_supply_t:
                        deposit_apr = eps_t * TimeConstants.A_YEAR * pool_token_price / (
                                total_supply_t * token_price)
                    else:
                        deposit_apr = 0
                    if total_supply_d:
                        borrow_apr = eps_d * TimeConstants.A_YEAR * pool_token_price / (
                                total_supply_d * token_price)
                    else:
                        borrow_apr = 0
                    interest_rate[token_address][DBConst.reward_deposit_apy].update({
                        DBConst.reward_borrow_apy: deposit_apr}
                    )
                    interest_rate[token_address][DBConst.reward_borrow_apy].update({
                        reward_address: borrow_apr}
                    )
            # update liquidity
            liquidity_log = {
                DBConst.total_borrow: {
                    DBConst.amount: total_supply_d,
                    DBConst.value_in_usd: total_supply_d * token_price},
                DBConst.total_deposit: {
                    DBConst.amount: total_supply_t,
                    DBConst.value_in_usd: total_supply_t * token_price}
            }
            interest_rate[token_address].update({DBConst.liquidity_change_logs: liquidity_log})

        return interest_rate

    def get_rewards_balance(
            self,
            wallet_address,
            pool_address,
            incentive_address: str,
            reserves_info: dict = None,
            pool_abi: list = AAVE_V3_LENDING_POOL_ABI,
            incentive_abi: list = AAVE_V3_INCENTIVES_ABI,
            block_number: int = "latest"
    ):
        if not reserves_info:
            reserves_info = self.get_reserves_info(pool_address, pool_abi, block_number)

        tokens = []
        for key, value in reserves_info.items():
            tokens += [self.to_checksum(value["tToken"]), self.to_checksum(value["dToken"])]
        contract = self._w3.eth.contract(address=self.to_checksum(incentive_address), abi=incentive_abi)
        rewards = contract.functions.getAllUserRewards(tokens, self.to_checksum(wallet_address)).call(
            block_identifier=block_number)
        result = dict(zip(*rewards))
        return result

    def get_wallet_deposit_borrow_balance(
            self,
            wallet_address: str,
            pool_address: str,
            oracle_address: str,
            reserves_info: str = None,
            pool_abi: list = AAVE_V3_LENDING_POOL_ABI,
            oracle_abi: list = AAVE_V3_ORACLE_ABI,
            block_number: int = "latest",
            wrapped_native_token_price: float = 1,
            pool_decimals: int = 18
    ):
        if not reserves_info:
            reserves_info = self.get_reserves_info(pool_address, pool_abi)
        reserves_list = list(reserves_info.keys())
        token_prices = self.get_assets_price(oracle_address, oracle_abi, reserves_list, block_number, pool_decimals)
        list_rpc_call = []
        list_call_id = []
        for token in reserves_info:
            value = reserves_info[token]
            add_rpc_call(abi=ERC20_ABI, contract_address=value["tToken"], fn_paras=wallet_address,
                         block_number=block_number,
                         list_call_id=list_call_id, list_rpc_call=list_rpc_call, fn_name="balanceOf")
            add_rpc_call(abi=ERC20_ABI, contract_address=value["dToken"], fn_paras=wallet_address,
                         block_number=block_number,
                         list_call_id=list_call_id, list_rpc_call=list_rpc_call, fn_name="balanceOf")
            add_rpc_call(abi=ERC20_ABI, contract_address=value["sdToken"], fn_paras=wallet_address,
                         block_number=block_number,
                         list_call_id=list_call_id, list_rpc_call=list_rpc_call, fn_name="balanceOf")
            add_rpc_call(abi=ERC20_ABI, contract_address=token, fn_name="decimals", block_number=block_number,
                         list_call_id=list_call_id, list_rpc_call=list_rpc_call)
        data_response = self.client_querier.sent_batch_to_provider(list_rpc_call, batch_size=100)
        decoded_data = decode_data_response(data_response, list_call_id)
        total_borrow, result = 0, {
            "borrow_amount_in_usd": 0,
            "deposit_amount_in_usd": 0,
            "health_factor": 0,
            "reserves_data": {}
        }
        for token in reserves_info:
            value = reserves_info[token]
            get_total_deposit_id = f"balanceOf_{value['tToken']}_{wallet_address}_{block_number}".lower()
            get_total_borrow_id = f"balanceOf_{value['dToken']}_{wallet_address}_{block_number}".lower()
            get_total_stable_borrow_id = f"balanceOf_{value['sdToken']}_{wallet_address}_{block_number}".lower()
            get_decimals_id = f"decimals_{token}_{block_number}".lower()
            decimals = decoded_data[get_decimals_id]
            deposit_amount = decoded_data[get_total_deposit_id] / 10 ** decimals
            borrow_amount = decoded_data[get_total_borrow_id] / 10 ** decimals
            borrow_amount += decoded_data[get_total_stable_borrow_id] / 10 ** decimals
            deposit_amount *= wrapped_native_token_price
            borrow_amount *= wrapped_native_token_price
            deposit_amount_in_usd = deposit_amount * token_prices.get(token, 0)
            borrow_amount_in_usd = borrow_amount * token_prices.get(token, 0)
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

    def get_token_deposit_borrow_balance(
            self,
            pool_address: str,
            oracle_address: str,
            reserves_info: str = None,
            pool_abi: list = AAVE_V3_LENDING_POOL_ABI,
            oracle_abi: list = AAVE_V3_ORACLE_ABI,
            block_number: int = "latest",
            wrapped_native_token_price: float = 1,
            pool_decimals: int = 18
    ):
        if not reserves_info:
            reserves_info = self.get_reserves_info(pool_address, pool_abi)
        reserves_list = list(reserves_info.keys())
        token_prices = self.get_assets_price(oracle_address, oracle_abi, reserves_list, block_number, pool_decimals)
        list_rpc_call = []
        list_call_id = []
        for token in reserves_info:
            value = reserves_info[token]
            add_rpc_call(abi=ERC20_ABI, contract_address=value["tToken"],
                         block_number=block_number,
                         list_call_id=list_call_id, list_rpc_call=list_rpc_call, fn_name="totalSupply")
            add_rpc_call(abi=ERC20_ABI, contract_address=value["dToken"],
                         block_number=block_number,
                         list_call_id=list_call_id, list_rpc_call=list_rpc_call, fn_name="totalSupply")
            add_rpc_call(abi=ERC20_ABI, contract_address=value["sdToken"],
                         block_number=block_number,
                         list_call_id=list_call_id, list_rpc_call=list_rpc_call, fn_name="totalSupply")
            add_rpc_call(abi=ERC20_ABI, contract_address=token, fn_name="decimals", block_number=block_number,
                         list_call_id=list_call_id, list_rpc_call=list_rpc_call)
            if token != '0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2'.lower():
                add_rpc_call(abi=ERC20_ABI, contract_address=token, fn_name="symbol", block_number=block_number,
                             list_call_id=list_call_id, list_rpc_call=list_rpc_call)
        data_response = self.client_querier.sent_batch_to_provider(list_rpc_call, batch_size=100)
        decoded_data = decode_data_response(data_response, list_call_id)
        result = {
            "borrow_amount_in_usd": 0,
            "deposit_amount_in_usd": 0,
            "reserves_data": {}
        }
        for token in reserves_info:
            value = reserves_info[token]
            get_total_deposit_id = f"totalSupply_{value['tToken']}_{block_number}".lower()
            get_total_borrow_id = f"totalSupply_{value['dToken']}_{block_number}".lower()
            get_total_stable_borrow_id = f"totalSupply_{value['sdToken']}_{block_number}".lower()
            get_decimals_id = f"decimals_{token}_{block_number}".lower()
            if token == '0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2'.lower():
                symbol = "MKR"
            else:
                get_symbol_id = f"symbol_{token}_{block_number}".lower()
                symbol = decoded_data[get_symbol_id]
            decimals = decoded_data[get_decimals_id]
            deposit_amount = decoded_data[get_total_deposit_id] / 10 ** decimals
            borrow_amount = decoded_data[get_total_borrow_id] / 10 ** decimals
            borrow_amount += decoded_data[get_total_stable_borrow_id] / 10 ** decimals
            deposit_amount *= wrapped_native_token_price
            borrow_amount *= wrapped_native_token_price
            deposit_amount_in_usd = deposit_amount * token_prices.get(token, 0)
            borrow_amount_in_usd = borrow_amount * token_prices.get(token, 0)
            result['borrow_amount_in_usd'] += borrow_amount_in_usd
            result['deposit_amount_in_usd'] += deposit_amount_in_usd
            if (borrow_amount > 0) or (deposit_amount > 0):
                result['reserves_data'][token] = {
                    "symbol": symbol,
                    "borrow_amount": borrow_amount,
                    "borrow_amount_in_usd": borrow_amount_in_usd,
                    "deposit_amount": deposit_amount,
                    "deposit_amount_in_usd": deposit_amount_in_usd,
                }

        return result


if __name__ == "__main__":
    import json
    from defi_services.lending_pools.lending_pools_info.arbitrum.aave_v3_arbitrum import AAVE_V3_ARB
    from defi_services.lending_pools.lending_pools_info.fantom.aave_v3_ftm import AAVE_V3_FTM
    from defi_services.lending_pools.lending_pools_info.ethereum.aave_v3_eth import AAVE_V3_ETH
    from defi_services.lending_pools.lending_pools_info.polygon.aave_v3_polygon import AAVE_V3_POLYGON
    from defi_services.lending_pools.lending_pools_info.optimism.aave_v3_optimism import AAVE_V3_OPTIMISM

    # service = AaveV3StateService(provider_uri="https://rpc.ankr.com/arbitrum")
    # # reserve_info = service.get_reserves_info(AAVE_V3_ARB.get("address"), AAVE_V3_LENDING_POOL_ABI)
    # reserve_info = service.get_rewards_list(AAVE_V3_ARB.get("incentiveAddress"), AAVE_V3_INCENTIVES_ABI)
    # with open("aave_v3_arb.json", "w") as f:
    #     f.write(json.dumps(reserve_info, indent=1))
    #
    # service = AaveV3StateService(provider_uri="https://rpc.ankr.com/eth")
    # # reserve_info = service.get_reserves_info(AAVE_V3_ETH.get("address"), AAVE_V3_LENDING_POOL_ABI)
    # reserve_info = service.get_rewards_list(AAVE_V3_ETH.get("incentiveAddress"), AAVE_V3_INCENTIVES_ABI)
    # with open("aave_v3_eth.json", "w") as f:
    #     f.write(json.dumps(reserve_info, indent=1))
    #
    # service = AaveV3StateService(provider_uri="https://rpc.ankr.com/fantom")
    # # reserve_info = service.get_reserves_info(AAVE_V3_FTM.get("address"), AAVE_V3_LENDING_POOL_ABI)
    # reserve_info = service.get_rewards_list(AAVE_V3_FTM.get("incentiveAddress"), AAVE_V3_INCENTIVES_ABI)
    # with open("aave_v3_ftm.json", "w") as f:
    #     f.write(json.dumps(reserve_info, indent=1))
    #
    # service = AaveV3StateService(provider_uri="https://rpc.ankr.com/polygon")
    # # reserve_info = service.get_reserves_info(AAVE_V3_POLYGON.get("address"), AAVE_V3_LENDING_POOL_ABI)
    # reserve_info = service.get_rewards_list(AAVE_V3_POLYGON.get("incentiveAddress"), AAVE_V3_INCENTIVES_ABI)
    # with open("aave_v3_pol.json", "w") as f:
    #     f.write(json.dumps(reserve_info, indent=1))
    #
    # service = AaveV3StateService(provider_uri="https://rpc.ankr.com/optimism")
    # # reserve_info = service.get_reserves_info(AAVE_V3_OPTIMISM.get("address"), AAVE_V3_LENDING_POOL_ABI)
    # reserve_info = service.get_rewards_list(AAVE_V3_OPTIMISM.get("incentiveAddress"), AAVE_V3_INCENTIVES_ABI)
    # with open("aave_v3_op.json", "w") as f:
    #     f.write(json.dumps(reserve_info, indent=1))

    service = AaveV3StateService(provider_uri="https://rpc.ankr.com/eth")
    reserve_info = service.get_token_deposit_borrow_balance(
        pool_address=AAVE_V3_ETH.get("address"),
        oracle_address=AAVE_V3_ETH.get("oracleAddress"),
        reserves_info=AAVE_V3_ETH.get("reservesList"),
        pool_abi=AAVE_V3_LENDING_POOL_ABI,
        oracle_abi=AAVE_V3_ORACLE_ABI,
        wrapped_native_token_price=1,
        pool_decimals=8
    )
    with open("../../../../test/aave_v3_eth.json", "w") as f:
        f.write(json.dumps(reserve_info, indent=1))

    service = AaveV3StateService(provider_uri="https://rpc.ankr.com/polygon")
    reserve_info = service.get_token_deposit_borrow_balance(
        pool_address=AAVE_V3_POLYGON.get("address"),
        oracle_address=AAVE_V3_POLYGON.get("oracleAddress"),
        reserves_info=AAVE_V3_POLYGON.get("reservesList"),
        pool_abi=AAVE_V3_LENDING_POOL_ABI,
        oracle_abi=AAVE_V3_ORACLE_ABI,
        wrapped_native_token_price=1,
        pool_decimals=8
    )
    with open("../../../../test/aave_v3_polygon.json", "w") as f:
        f.write(json.dumps(reserve_info, indent=1))

    service = AaveV3StateService(provider_uri="https://rpc.ankr.com/fantom")
    reserve_info = service.get_token_deposit_borrow_balance(
        pool_address=AAVE_V3_FTM.get("address"),
        oracle_address=AAVE_V3_FTM.get("oracleAddress"),
        reserves_info=AAVE_V3_FTM.get("reservesList"),
        pool_abi=AAVE_V3_LENDING_POOL_ABI,
        oracle_abi=AAVE_V3_ORACLE_ABI,
        wrapped_native_token_price=1,
        pool_decimals=8
    )
    with open("../../../../test/aave_v3_ftm.json", "w") as f:
        f.write(json.dumps(reserve_info, indent=1))

    service = AaveV3StateService(provider_uri="https://rpc.ankr.com/arbitrum")
    reserve_info = service.get_token_deposit_borrow_balance(
        pool_address=AAVE_V3_ARB.get("address"),
        oracle_address=AAVE_V3_ARB.get("oracleAddress"),
        reserves_info=AAVE_V3_ARB.get("reservesList"),
        pool_abi=AAVE_V3_LENDING_POOL_ABI,
        oracle_abi=AAVE_V3_ORACLE_ABI,
        wrapped_native_token_price=0,
        pool_decimals=8
    )
    with open("../../../../test/aave_v3_arb.json", "w") as f:
        f.write(json.dumps(reserve_info, indent=1))

    service = AaveV3StateService(provider_uri="https://rpc.ankr.com/optimism")
    reserve_info = service.get_token_deposit_borrow_balance(
        pool_address=AAVE_V3_OPTIMISM.get("address"),
        oracle_address=AAVE_V3_OPTIMISM.get("oracleAddress"),
        reserves_info=AAVE_V3_OPTIMISM.get("reservesList"),
        pool_abi=AAVE_V3_LENDING_POOL_ABI,
        oracle_abi=AAVE_V3_ORACLE_ABI,
        wrapped_native_token_price=1,
        pool_decimals=8
    )
    with open("../../../../test/aave_v3_optimism.json", "w") as f:
        f.write(json.dumps(reserve_info, indent=1))
