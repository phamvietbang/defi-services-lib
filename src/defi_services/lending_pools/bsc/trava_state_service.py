import logging

from defi_services.abis.erc20_abi import ERC20_ABI
from defi_services.abis.lending_pool.oracle_abi import ORACLE_ABI
from defi_services.abis.lending_pool.staked_incentives_abi import STAKED_INCENTIVES_ABI
from defi_services.abis.lending_pool.trava_lending_pool_abi import TRAVA_LENDING_POOL_ABI
from defi_services.constants.db_constant import DBConst
from defi_services.constants.time_constant import TimeConstants
from defi_services.state_service import StateService
from defi_services.utils.batch_queries_service import add_rpc_call, decode_data_response

logger = logging.getLogger("Trava Lending Pool State Service")


class TravaStateService(StateService):
    def __init__(self, provider_uri: str):
        super().__init__(provider_uri)

    def get_reserves_list(self, pool_address: str, pool_abi: list = TRAVA_LENDING_POOL_ABI,
                          block_number: int = 'latest'):
        contract = self._w3.eth.contract(address=self.to_checksum(pool_address), abi=pool_abi)
        return contract.functions.getReservesList().call(block_identifier=block_number)

    def get_reserve_data(self, pool_address: str, token_address: str,
                         pool_abi: list = TRAVA_LENDING_POOL_ABI, block_number: int = 'latest'):
        contract = self._w3.eth.contract(address=self.to_checksum(pool_address), abi=pool_abi)
        return contract.functions.getReserveData(self.to_checksum(token_address)).call(block_identifier=block_number)

    def get_reserve_data_of_token_list(self, pool_address: str, token_addresses: list,
                                       pool_abi: list = TRAVA_LENDING_POOL_ABI, block_number: int = 'latest'):
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
                       stake_incentive_abi: list = STAKED_INCENTIVES_ABI, block_number: int = 'latest'):
        contract = self._w3.eth.contract(address=self.to_checksum(stake_incentive_address), abi=stake_incentive_abi)
        return contract.functions.getAssetData(self.to_checksum(token_address)).call(block_identifier=block_number)

    def get_asset_data_of_token_list(self, stake_incentive_address: str, token_addresses: list,
                                     stake_incentive_abi: list = STAKED_INCENTIVES_ABI, block_number: int = 'latest'):
        list_rpc_call, list_call_id = [], []
        for token_address in token_addresses:
            add_rpc_call(
                abi=stake_incentive_abi, fn_name='getAssetData', contract_address=stake_incentive_address,
                block_number=block_number, fn_paras=token_address, list_rpc_call=list_rpc_call,
                list_call_id=list_call_id

            )
        data_response = self.client_querier.sent_batch_to_provider(list_rpc_call, batch_size=100)
        decoded_data = decode_data_response(data_response, list_call_id)
        result = {}
        for token_address in token_addresses:
            get_reserve_data_call_id = f'getAssetData_{stake_incentive_address}_{token_address}_{block_number}'.lower()
            result[token_address.lower()] = decoded_data.get(get_reserve_data_call_id)

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

    def _encode_apy_lending_pool_function_call(
            self,
            pool_address: str,
            pool_abi: list,
            reserves_list: list,
            reserves_info: dict = None,
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
                    abi=stake_incentive_abi, fn_name='getAssetData', contract_address=stake_incentive_address,
                    block_number=block_number, fn_paras=self.to_checksum(ttoken), list_rpc_call=list_rpc_call,
                    list_call_id=list_call_id
                )
                add_rpc_call(
                    abi=stake_incentive_abi, fn_name='getAssetData', contract_address=stake_incentive_address,
                    block_number=block_number, fn_paras=self.to_checksum(debt_token), list_rpc_call=list_rpc_call,
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
        total_supply_tokens, asset_data_tokens = {}, {}
        for token_address in reserves_list:
            lower_address = token_address.lower()
            reserve_data = reserves_data[lower_address]
            interest_rate[lower_address] = {DBConst.deposit_apy: float(reserve_data[3]) / 10 ** 27,
                                            DBConst.borrow_apy: float(reserve_data[4]) / 10 ** 27}
            ttoken = reserve_data[6].lower()
            debt_token = reserve_data[7].lower()
            ttokens[lower_address] = ttoken
            debt_tokens[lower_address] = debt_token
            decimals_call_id = f'decimals_{token_address}_{block_number}'.lower()
            decimals[lower_address] = decoded_data.get(decimals_call_id)
            if reserves_info:
                ttoken_total_supply_call_id = f'totalSupply_{ttoken}_{block_number}'.lower()
                debt_token_total_supply_call_id = f'totalSupply_{debt_token}_{block_number}'.lower()
                ttoken_asset_data_call_id = f'getAssetData_{stake_incentive_address}_{ttoken}_{block_number}'.lower()
                debt_asset_data_supply_call_id = f'getAssetData_{stake_incentive_address}_{debt_token}_{block_number}'.lower()
                total_supply_tokens[ttoken] = decoded_data.get(ttoken_total_supply_call_id)
                total_supply_tokens[debt_token] = decoded_data.get(debt_token_total_supply_call_id)
                asset_data_tokens[ttoken] = decoded_data.get(ttoken_asset_data_call_id)
                asset_data_tokens[debt_token] = decoded_data.get(debt_asset_data_supply_call_id)

        return {
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
            staked_incentive_address: str,
            oracle_address: str,
            oracle_abi: list = ORACLE_ABI,
            pool_abi: list = TRAVA_LENDING_POOL_ABI,
            staked_incentive_abi: list = STAKED_INCENTIVES_ABI,
            reserves_info: dict = None,
            token_prices: dict = None,
            pool_token_price: float = 1,
            block_number: int = 'latest',
    ):

        if not reserves_info:
            reserves_list = self.get_reserves_list(pool_address, pool_abi, block_number)
        else:
            reserves_list = list(reserves_info.keys())
        if not token_prices:
            token_prices = self.get_assets_price(oracle_address, oracle_abi, reserves_list, block_number)

        list_rpc_call, list_call_id = self._encode_apy_lending_pool_function_call(
            pool_address, pool_abi, reserves_list, reserves_info, staked_incentive_address, staked_incentive_abi,
            oracle_address, oracle_abi, block_number,
        )
        # Decode data
        decoded_data = self._decode_apy_lending_pool_function_call(
            list_rpc_call, list_call_id, pool_address,
            reserves_list, reserves_info,
            staked_incentive_address, oracle_address, block_number
        )
        interest_rate = decoded_data["interest_rate"]
        ttokens = decoded_data["ttokens"]
        debt_tokens = decoded_data["debt_tokens"]
        decimals = decoded_data["decimals"]
        total_supply_tokens = decoded_data["total_supply_tokens"]
        asset_data_tokens = decoded_data["asset_data_tokens"]
        debt_and_t_tokens = list(debt_tokens.values()) + list(ttokens.values())
        if not total_supply_tokens:
            total_supply_tokens = self.total_supply_of_token_list(debt_and_t_tokens)
        if not asset_data_tokens:
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
            total_supply_t = total_supply_t / 10 ** decimal
            total_supply_d = total_supply_d / 10 ** decimal
            eps_t = asset_data_t[1] / 10 ** 18
            eps_d = asset_data_d[1] / 10 ** 18
            token_price = token_prices.get(token_address)
            deposit_apr = eps_t * TimeConstants.A_YEAR * pool_token_price / (
                    total_supply_t * token_price)
            borrow_apr = eps_d * TimeConstants.A_YEAR * pool_token_price / (
                    total_supply_d * token_price)
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

    def get_wallet_information_in_lending_pool(
            self,
            wallet_address: str,
            staked_incentive_address: str,
            oracle_address: str,
            staked_token_price: float,
            reserves_info: dict,
            oracle_abi: list = ORACLE_ABI,
            staked_incentive_abi: list = STAKED_INCENTIVES_ABI,
            token_prices: dict = None,
            block_number: int = 'latest',
    ):
        list_rpc_call = []
        list_call_id = []
        td_token = []
        token_addresses = list(reserves_info.keys())
        if not token_prices:
            token_prices = self.get_assets_price(oracle_address, oracle_abi, token_addresses, block_number)
        for token in reserves_info:
            value = reserves_info[token]
            td_token += [self.to_checksum(value["tToken"]), self.to_checksum(value["dToken"])]
            add_rpc_call(abi=ERC20_ABI, contract_address=value["tToken"], fn_paras=wallet_address,
                         block_number=block_number,
                         list_call_id=list_call_id, list_rpc_call=list_rpc_call, fn_name="balanceOf")
            add_rpc_call(abi=ERC20_ABI, contract_address=value["dToken"], fn_paras=wallet_address,
                         block_number=block_number,
                         list_call_id=list_call_id, list_rpc_call=list_rpc_call, fn_name="balanceOf")
            add_rpc_call(abi=ERC20_ABI, contract_address=token, fn_name="decimals", block_number=block_number,
                         list_call_id=list_call_id, list_rpc_call=list_rpc_call)
        add_rpc_call(abi=staked_incentive_abi, contract_address=staked_incentive_address, fn_name="getRewardsBalance",
                     block_number=block_number, fn_paras=[td_token, wallet_address],
                     list_call_id=list_call_id, list_rpc_call=list_rpc_call)

        data_response = self.client_querier.sent_batch_to_provider(list_rpc_call)
        decoded_data = decode_data_response(data_response, list_call_id)
        reward_id = f'getRewardsBalance_{staked_incentive_address}_{[td_token, wallet_address]}_{block_number}'.lower()
        total_borrow, result = 0, {
            "reward_amount": decoded_data[reward_id] / 10 ** 18,
            "reward_amount_in_usd": decoded_data[reward_id] * staked_token_price / 10 ** 18,
            "borrow_amount_in_usd": 0,
            "deposit_amount_in_usd": 0,
            "health_factor": 0,
            "reserves_data": {}
        }
        get_assets_prices_id = f'getAssetsPrices_{oracle_address}_{token_addresses}_{block_number}'.lower()
        reserves_prices = decoded_data.get(get_assets_prices_id)
        if reserves_prices:
            token_prices = {}
            for pos in range(len(token_addresses)):
                token_prices[token_addresses[pos]] = reserves_prices[pos]

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
