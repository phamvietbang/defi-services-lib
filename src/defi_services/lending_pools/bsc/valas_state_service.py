from src.defi_services.abis.erc20_abi import ERC20_ABI
from src.defi_services.abis.lending_pool.chef_incentives_controller import CHEF_INCENTIVES_CONTROLLER
from src.defi_services.abis.lending_pool.lending_pool_abi import LENDING_POOL_ABI
from src.defi_services.abis.lending_pool.oracle_abi import ORACLE_ABI
from src.defi_services.abis.lending_pool.valas_multi_fee_distribution import VALAS_MULTI_FEE_DISTRIBUTION
from src.defi_services.constants.db_constant import DBConst
from src.defi_services.constants.time_constant import TimeConstants
from src.defi_services.lending_pools.bsc.trava_state_service import TravaStateService
import logging

from src.defi_services.utils.batch_queries_service import add_rpc_call, decode_data_response

_LOGGER = logging.getLogger("AaveLendingPoolS")


class ValasStateService(TravaStateService):
    def __int__(self, provider_uri: str):
        super().__init__(provider_uri)

    def rewards_per_second(self, chef_incentive_address: str, chef_incentives_abi: list = CHEF_INCENTIVES_CONTROLLER,
                           block_number: int = 'latest'):
        contract = self._w3.eth.contract(self.to_checksum(chef_incentive_address), chef_incentives_abi)
        return contract.functions.rewardsPerSecond().call(block_identifier=block_number)

    def total_alloc_point(self, chef_incentive_address: str, chef_incentives_abi: list = CHEF_INCENTIVES_CONTROLLER,
                          block_number: int = 'latest'):
        contract = self._w3.eth.contract(self.to_checksum(chef_incentive_address), chef_incentives_abi)
        return contract.functions.totalAllocPoint().call(block_identifier=block_number)

    def pool_info_of_token_list(self, chef_incentive_address: str, token_addresses: list,
                                chef_incentives_abi: list = CHEF_INCENTIVES_CONTROLLER, block_number: int = 'latest'):
        list_rpc_call = []
        list_call_id = []
        for token_address in token_addresses:
            add_rpc_call(
                abi=chef_incentives_abi, fn_name='poolInfo', contract_address=chef_incentive_address,
                block_number=block_number, fn_paras=token_address, list_rpc_call=list_rpc_call,
                list_call_id=list_call_id
            )
        data_response = self.client_querier.sent_batch_to_provider(list_rpc_call, batch_size=100)
        decoded_data = decode_data_response(data_response, list_call_id)
        result = {}
        for token_address in token_addresses:
            get_asset_data_call_id = f'poolInfo_{chef_incentive_address}_{token_address}_{block_number}'.lower()
            result[token_address.lower()] = decoded_data.get(get_asset_data_call_id)

        return result

    def _encode_apy_lending_pool_function_call(
            self,
            pool_address: str,
            pool_abi: list,
            reserves_list: list,
            reserves_info: dict = None,
            chef_incentive_address: str = None,
            chef_incentives_abi: list = None,
            oracle_address: str = None,
            oracle_abi: list = None,
            block_number: int = "latest",
    ):
        list_rpc_call, list_call_id = [], []
        add_rpc_call(
            abi=chef_incentives_abi, fn_name='rewardsPerSecond', contract_address=chef_incentive_address,
            block_number=block_number, list_rpc_call=list_rpc_call, list_call_id=list_call_id
        )
        add_rpc_call(
            abi=chef_incentives_abi, fn_name='totalAllocPoint', contract_address=chef_incentive_address,
            block_number=block_number, list_rpc_call=list_rpc_call, list_call_id=list_call_id
        )
        for token_address in reserves_list:
            add_rpc_call(
                abi=pool_abi, fn_name='getReserveData', contract_address=pool_address,
                block_number=block_number, fn_paras=token_address,
                list_rpc_call=list_rpc_call, list_call_id=list_call_id)
            add_rpc_call(
                abi=ERC20_ABI, fn_name='decimals', contract_address=self.to_checksum(token_address),
                block_number=block_number, list_rpc_call=list_rpc_call, list_call_id=list_call_id
            )
            if reserves_info:
                ttoken = reserves_info[token_address]['tToken']
                debt_token = reserves_info[token_address]['debtToken']
                add_rpc_call(
                    abi=ERC20_ABI, fn_name='totalSupply', contract_address=self.to_checksum(ttoken),
                    block_number=block_number, list_rpc_call=list_rpc_call, list_call_id=list_call_id
                )
                add_rpc_call(
                    abi=ERC20_ABI, fn_name='totalSupply', contract_address=self.to_checksum(debt_token),
                    block_number=block_number, list_rpc_call=list_rpc_call, list_call_id=list_call_id
                )
                add_rpc_call(
                    abi=chef_incentives_abi, fn_name='poolInfo', contract_address=chef_incentive_address,
                    block_number=block_number, fn_paras=token_address, list_rpc_call=list_rpc_call,
                    list_call_id=list_call_id
                )
                add_rpc_call(
                    abi=chef_incentives_abi, fn_name='poolInfo', contract_address=chef_incentive_address,
                    block_number=block_number, fn_paras=token_address, list_rpc_call=list_rpc_call,
                    list_call_id=list_call_id
                )

        return list_rpc_call, list_call_id

    def _decode_apy_lending_pool_function_call(
            self,
            list_rpc_call: list,
            list_call_id: list,
            pool_address: str,
            reserves_list: list,
            reserves_info: dict = None,
            chef_incentive_address: str = None,
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
        total_supply_tokens, asset_data_tokens = {}, {}
        for token_address in reserves_list:
            lower_address = token_address.lower()
            reserve_data = reserves_data[lower_address]
            interest_rate[lower_address] = {DBConst.deposit_apy: float(reserve_data[3]) / 10 ** 27,
                                            DBConst.borrow_apy: float(reserve_data[4]) / 10 ** 27}
            ttoken = reserve_data[7].lower()
            debt_token = reserve_data[9].lower()
            ttokens[lower_address] = ttoken
            debt_tokens[lower_address] = debt_token
            decimals_call_id = f'decimals_{token_address}_{block_number}'.lower()
            decimals[lower_address] = decoded_data.get(decimals_call_id)
            if reserves_info:
                ttoken_total_supply_call_id = f'totalSupply_{ttoken}_{block_number}'.lower()
                debt_token_total_supply_call_id = f'totalSupply_{debt_token}_{block_number}'.lower()
                ttoken_asset_data_call_id = f'poolInfo_{chef_incentive_address}_{ttoken}_{block_number}'.lower()
                debt_asset_data_supply_call_id = f'poolInfo_{chef_incentive_address}_{debt_token}_{block_number}'.lower()
                total_supply_tokens[ttoken] = decoded_data.get(ttoken_total_supply_call_id)
                total_supply_tokens[debt_token] = decoded_data.get(debt_token_total_supply_call_id)
                asset_data_tokens[ttoken] = decoded_data.get(ttoken_asset_data_call_id)
                asset_data_tokens[debt_token] = decoded_data.get(debt_asset_data_supply_call_id)

        rewards_per_second_id = f"rewardsPerSecond_{chef_incentive_address}_{block_number}".lower()
        total_alloc_point_id = f"totalAllocPoint_{chef_incentive_address}_{block_number}".lower()
        rewards_per_second = decoded_data.get(rewards_per_second_id)
        total_alloc_point = decoded_data.get(total_alloc_point_id)

        return {
            "rewards_per_second": rewards_per_second,
            "total_alloc_point": total_alloc_point,
            "total_supply_tokens": total_supply_tokens,
            "asset_data_tokens": asset_data_tokens,
            "decimals": decimals,
            "ttokens": ttokens,
            "debt_tokens": debt_tokens,
            "interest_rate": interest_rate
        }

    def get_apy_lending_pool(
            self,
            pool_address: str,
            oracle_address: str,
            chef_incentive_address: str,
            chef_incentive_abi: list = CHEF_INCENTIVES_CONTROLLER,
            pool_abi: list = LENDING_POOL_ABI,
            oracle_abi: list = ORACLE_ABI,
            reserves_info: dict = None,
            block_number: int = 'latest',
            token_prices: dict = None,
            pool_token_price: float = 1):
        if not reserves_info:
            reserves_list = self.get_reserves_list(pool_address, pool_abi, block_number)
        else:
            reserves_list = list(reserves_info.keys())
        if not token_prices:
            token_prices = self.get_assets_price(oracle_address, oracle_abi, reserves_list, block_number, 18)
        list_rpc_call, list_call_id = self._encode_apy_lending_pool_function_call(
            pool_address, pool_abi, reserves_list, reserves_info, chef_incentive_address, chef_incentive_abi,
            oracle_address, oracle_abi, block_number,
        )
        decoded_data = self._decode_apy_lending_pool_function_call(
            list_rpc_call, list_call_id, pool_address,
            reserves_list, reserves_info,
            chef_incentive_address, oracle_address, block_number
        )
        interest_rate = decoded_data["interest_rate"]
        ttokens = decoded_data["ttokens"]
        debt_tokens = decoded_data["debt_tokens"]
        decimals = decoded_data["decimals"]
        total_supply_tokens = decoded_data["total_supply_tokens"]
        asset_data_tokens = decoded_data["asset_data_tokens"]
        rewards_per_second = decoded_data["rewards_per_second"]
        total_alloc_point = decoded_data["total_alloc_point"]
        debt_and_t_tokens = list(debt_tokens.values()) + list(ttokens.values())
        if not total_supply_tokens:
            total_supply_tokens = self.total_supply_of_token_list(debt_and_t_tokens)
        if not asset_data_tokens:
            asset_data_tokens = self.pool_info_of_token_list(
                chef_incentive_address, debt_and_t_tokens, chef_incentive_abi, block_number)
        # Decode data
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
            total_supply_t = total_supply_t / 10 ** decimal
            total_supply_d = total_supply_d / 10 ** decimal
            eps_t = rewards_per_second * asset_data_t[1] / (total_alloc_point * 10 ** 18)
            eps_d = rewards_per_second * asset_data_d[1] / (total_alloc_point * 10 ** 18)
            token_price = token_prices.get(token_address)
            deposit_apr = eps_t * TimeConstants.A_YEAR * pool_token_price / (
                    total_supply_t * token_price)
            borrow_apr = eps_d * TimeConstants.A_YEAR * pool_token_price / (
                    total_supply_d * token_price)
            # update deposit, borrow reward apr
            interest_rate[token_address].update({DBConst.reward_deposit_apy: deposit_apr,
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

    def get_wallet_information_in_lending_pool(
            self,
            wallet_address: str,
            reserves_info: dict,
            multi_fee_address: str,
            oracle_address: str,
            staked_token_price: float,
            oracle_abi: list = ORACLE_ABI,
            multi_fee_distribution: list = VALAS_MULTI_FEE_DISTRIBUTION,
            token_prices: dict = None,
            block_number: int = "latest",
    ):
        list_rpc_call = []
        list_call_id = []
        if not token_prices:
            reserves_list = list(reserves_info.keys())
            token_prices = self.get_assets_price(oracle_address, oracle_abi, reserves_list, block_number, 18)

        for token in reserves_info:
            value = reserves_info[token]
            add_rpc_call(abi=ERC20_ABI, contract_address=value["tToken"], fn_paras=wallet_address,
                         block_number=block_number,
                         list_call_id=list_call_id, list_rpc_call=list_rpc_call, fn_name="balanceOf")
            add_rpc_call(abi=ERC20_ABI, contract_address=value["dToken"], fn_paras=wallet_address,
                         block_number=block_number,
                         list_call_id=list_call_id, list_rpc_call=list_rpc_call, fn_name="balanceOf")
            add_rpc_call(abi=ERC20_ABI, contract_address=token, fn_name="decimals", block_number=block_number,
                         list_call_id=list_call_id, list_rpc_call=list_rpc_call)

        add_rpc_call(abi=multi_fee_distribution, contract_address=multi_fee_address,
                     fn_name="earnedBalances", fn_paras=wallet_address,
                     block_number=block_number, list_call_id=list_call_id, list_rpc_call=list_rpc_call)

        data_response = self.client_querier.sent_batch_to_provider(list_rpc_call)
        decoded_data = decode_data_response(data_response, list_call_id)
        total_borrow, result = 0, {
            "reward_amount": 0,
            "reward_amount_in_usd": 0,
            "borrow_amount_in_usd": 0,
            "deposit_amount_in_usd": 0,
            "health_factor": 0,
            "reserves_data": {}
        }
        reward_data = decoded_data.get(f"earnedBalances_{multi_fee_address}_{wallet_address}_{block_number}".lower())
        result["reward_amount"] = reward_data[0] / 10 ** 18
        result["reward_amount_in_usd"] = result["reward_amount"] * staked_token_price
        for token in reserves_info:
            value = reserves_info[token]
            get_total_deposit_id = f"balanceOf_{value['tToken']}_{wallet_address}_{block_number}".lower()
            get_total_borrow_id = f"balanceOf_{value['dToken']}_{wallet_address}_{block_number}".lower()
            get_decimals_id = f"decimals_{token}_{block_number}".lower()
            decimals = decoded_data[get_decimals_id]
            deposit_amount = decoded_data[get_total_deposit_id] / 10 ** decimals
            borrow_amount = decoded_data[get_total_borrow_id] / 10 ** decimals
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
