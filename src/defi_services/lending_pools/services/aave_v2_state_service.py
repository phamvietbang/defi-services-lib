from defi_services.abis.erc20_abi import ERC20_ABI
from defi_services.abis.lending_pool.oracle_abi import ORACLE_ABI
from defi_services.abis.lending_pool.staked_incentives_abi import STAKED_INCENTIVES_ABI
from defi_services.constants.db_constant import DBConst
from defi_services.constants.time_constant import TimeConstants
from defi_services.lending_pools.services.trava_state_service import TravaStateService
from defi_services.utils.batch_queries_service import add_rpc_call, decode_data_response
from defi_services.abis.lending_pool.lending_pool_abi import LENDING_POOL_ABI


class AaveV2StateService(TravaStateService):
    def __init__(self, provider_uri: str):
        super().__init__(provider_uri)

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
        sdebt_tokens, decimals = {}, {}
        for token_address in reserves_list:
            lower_address = token_address.lower()
            reserve_data = reserves_data[lower_address]
            interest_rate[lower_address] = {DBConst.deposit_apy: float(reserve_data[3]) / 10 ** 27,
                                            DBConst.borrow_apy: float(reserve_data[4]) / 10 ** 27}
            ttoken = reserve_data[7].lower()
            sdebt_token = reserve_data[8].lower()
            debt_token = reserve_data[9].lower()
            ttokens[lower_address] = ttoken
            debt_tokens[lower_address] = debt_token
            sdebt_tokens[lower_address] = sdebt_token
            decimals_call_id = f'decimals_{token_address}_{block_number}'.lower()
            decimals[lower_address] = decoded_data.get(decimals_call_id)

        return {
            "decimals": decimals,
            "ttokens": ttokens,
            "sdebt_tokens": sdebt_tokens,
            "debt_tokens": debt_tokens,
            "interest_rate": interest_rate
        }

    def get_reserves_info(self, pool_address: str, pool_abi: list, block_number: int = "latest"):
        reserves_list = self.get_reserves_list(pool_address, pool_abi, block_number)
        reserves_data = self.get_reserve_data_of_token_list(pool_address, reserves_list, pool_abi, block_number)
        reserves_info = {}
        for key, value in reserves_data.items():
            reserves_info[key] = {}
            reserves_info[key]["tToken"] = value[7]
            reserves_info[key]["dToken"] = value[9]
            reserves_info[key]["sdToken"] = value[8]
            risk_param = bin(value[0][0])[2:]
            reserves_info[key]["liquidationThreshold"] = int(risk_param[-31:-16], 2) / 10 ** 4
        return reserves_info

    def get_rewards_balance(
            self,
            wallet_address,
            pool_address,
            staked_incentive_address: str,
            reserves_info: dict = None,
            pool_abi: list = LENDING_POOL_ABI,
            staked_incentive_abi: list = STAKED_INCENTIVES_ABI,
            block_number: int = "latest"
    ):
        if not reserves_info:
            reserves_info = self.get_reserves_info(pool_address, pool_abi, block_number)

        tokens = []
        for key, value in reserves_info.items():
            tokens += [self.to_checksum(value["tToken"]), self.to_checksum(value["dToken"])]
        contract = self._w3.eth.contract(address=self.to_checksum(staked_incentive_address), abi=staked_incentive_abi)
        reward = contract.functions.getRewardsBalance(tokens, self.to_checksum(wallet_address)).call(
            block_identifier=block_number)
        return reward / 10 ** 18

    def get_apy_lending_pool(
            self,
            pool_address: str,
            staked_incentive_address: str,
            oracle_address: str,
            oracle_abi: list = ORACLE_ABI,
            pool_abi: list = LENDING_POOL_ABI,
            staked_incentive_abi: list = STAKED_INCENTIVES_ABI,
            reserves_info: dict = None,
            token_prices: dict = None,
            pool_token_price: float = 1,
            block_number: int = 'latest',
            wrapped_native_token_price: float = 1900,
            pool_decimals: int = 18
    ):
        if not reserves_info:
            reserves_info = self.get_reserves_info(pool_address, pool_abi, block_number)

        reserves_list = list(reserves_info.keys())
        token_prices = self.get_assets_price(oracle_address, oracle_abi, reserves_list, block_number, pool_decimals)
        list_rpc_call, list_call_id = self._encode_apy_lending_pool_function_call(
            pool_address, pool_abi, reserves_list, staked_incentive_address, staked_incentive_abi,
            oracle_address, oracle_abi, block_number,
        )
        # Decode data
        decoded_data = self._decode_apy_lending_pool_function_call(
            list_rpc_call, list_call_id, pool_address,
            reserves_list, staked_incentive_address, oracle_address, block_number
        )
        interest_rate = decoded_data["interest_rate"]
        ttokens = decoded_data["ttokens"]
        debt_tokens = decoded_data["debt_tokens"]
        decimals = decoded_data["decimals"]
        debt_and_t_tokens = list(debt_tokens.values()) + list(ttokens.values())
        total_supply_tokens = self.total_supply_of_token_list(debt_and_t_tokens)
        asset_data_tokens = self.get_asset_data_of_token_list(
            staked_incentive_address, debt_and_t_tokens, staked_incentive_abi, block_number)

        lower_addresses = [i.lower() for i in reserves_list]
        for token_address in lower_addresses:
            ttoken = ttokens.get(token_address)
            debt_token = debt_tokens.get(token_address)
            decimal = decimals.get(token_address)
            total_supply_t = total_supply_tokens.get(ttoken)
            total_supply_d = total_supply_tokens.get(debt_token)
            asset_data_t = asset_data_tokens.get(ttoken)
            asset_data_d = asset_data_tokens.get(debt_token)
            # update deposit, borrow apy
            total_supply_t = total_supply_t * wrapped_native_token_price / 10 ** decimal
            total_supply_d = total_supply_d * wrapped_native_token_price / 10 ** decimal
            eps_t = asset_data_t[1] / 10 ** 18
            eps_d = asset_data_d[1] / 10 ** 18
            token_price = token_prices.get(token_address)
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
            interest_rate[token_address].update({
                "utilization": total_supply_d / total_supply_t,
                DBConst.reward_deposit_apy: deposit_apr,
                DBConst.reward_borrow_apy: borrow_apr})
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

    def get_wallet_deposit_borrow_balance(
            self,
            wallet_address: str,
            pool_address: str,
            oracle_address: str,
            reserves_info: str = None,
            pool_abi: list = LENDING_POOL_ABI,
            oracle_abi: list = ORACLE_ABI,
            block_number: int = "latest",
            wrapped_native_token_price: float = 1900,
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


if __name__ == "__main__":
    import json
    from defi_services.lending_pools.lending_pools_info.ethereum.aave_v2_eth import AAVE_V2_ETH
    from defi_services.lending_pools.lending_pools_info.polygon.aave_v2_polygon import AAVE_V2_POLYGON
    from defi_services.abis.lending_pool.lending_pool_abi import LENDING_POOL_ABI

    service = AaveV2StateService(provider_uri="https://rpc.ankr.com/eth")
    reserve_info = service.get_reserves_info(AAVE_V2_ETH.get("address"), LENDING_POOL_ABI)
    with open("aave.json", "w") as f:
        f.write(json.dumps(reserve_info, indent=1))

    service = AaveV2StateService(provider_uri="https://rpc.ankr.com/polygon")
    reserve_info = service.get_reserves_info(AAVE_V2_POLYGON.get("address"), LENDING_POOL_ABI)
    with open("aave_polygon.json", "w") as f:
        f.write(json.dumps(reserve_info, indent=1))
