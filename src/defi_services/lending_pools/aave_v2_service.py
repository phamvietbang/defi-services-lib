from defi_services.constants.chain_constant import Chain
from defi_services.defi_service import DefiService
from defi_services.lending_pools.lending_pools_info.ethereum.aave_v2_eth import AAVE_V2_ETH
from defi_services.lending_pools.lending_pools_info.polygon.aave_v2_polygon import AAVE_V2_POLYGON
from defi_services.lending_pools.services.aave_v2_state_service import AaveV2StateService


class AaveV2Service(DefiService):
    name = "aave v2 lending pool"

    def __init__(self, chain_id: str, provider_uri: str):
        super().__init__(chain_id, provider_uri)
        self.state_service = AaveV2StateService(provider_uri)
        self.defi_constant = self._get_constant()

    def _get_constant(self):
        if self.chain_id == Chain.polygon:
            return AAVE_V2_POLYGON
        elif self.chain_id == Chain.ethereum:
            return AAVE_V2_ETH

        return None

    def get_apy_defi_app(self, block_number: int = "latest", **kwargs):
        return self.state_service.get_apy_lending_pool(
            pool_address=self.defi_constant.get("address"),
            staked_incentive_address=self.defi_constant.get("stakedIncentiveAddress"),
            oracle_address=self.defi_constant.get("oracleAddress"),
            block_number=block_number,
            reserves_info=self.defi_constant.get("reservesList"),
            wrapped_native_token_price=kwargs.get("wrapped_native_token_price"),
        )

    def get_rewards_balance(self, wallet_address: str, block_number: int = "latest"):
        return self.state_service.get_rewards_balance(
            wallet_address=wallet_address,
            pool_address=self.defi_constant.get("address"),
            staked_incentive_address=self.defi_constant.get("stakedIncentiveAddress"),
            block_number=block_number,
            reserves_info=self.defi_constant.get("reservesList")
        )

    def get_wallet_deposit_borrow_balance(self, wallet_address: str, block_number: int = "latest", **kwargs):
        return self.state_service.get_wallet_deposit_borrow_balance(
            wallet_address=wallet_address,
            pool_address=self.defi_constant.get("address"),
            oracle_address=self.defi_constant.get("oracleAddress"),
            block_number=block_number,
            reserves_info=self.defi_constant.get("reservesList"),
            wrapped_native_token_price=kwargs.get("wrapped_native_token_price"),
        )
