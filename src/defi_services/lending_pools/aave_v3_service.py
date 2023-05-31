from defi_services.constants.chain_constant import Chain
from defi_services.defi_service import DefiService
from defi_services.lending_pools.lending_pools_info.arbitrum.aave_v3_arbitrum import AAVE_V3_ARB
from defi_services.lending_pools.lending_pools_info.ethereum.aave_v3_eth import AAVE_V3_ETH
from defi_services.lending_pools.lending_pools_info.fantom.aave_v3_ftm import AAVE_V3_FTM
from defi_services.lending_pools.lending_pools_info.optimism.aave_v3_optimism import AAVE_V3_OPTIMISM
from defi_services.lending_pools.lending_pools_info.polygon.aave_v3_polygon import AAVE_V3_POLYGON
from defi_services.lending_pools.services.aave_v3_state_service import AaveV3StateService


class AaveV3Service(DefiService):
    name = "aave v3 lending pool"

    def __init__(self, chain_id: str, provider_uri: str):
        super().__init__(chain_id, provider_uri)
        self.state_service = AaveV3StateService(provider_uri)
        self.defi_constant = self._get_constant()
        self.address = self.defi_constant.get("address")

    def _get_constant(self):
        if self.chain_id == Chain.arbitrum:
            return AAVE_V3_ARB
        elif self.chain_id == Chain.fantom:
            return AAVE_V3_FTM
        elif self.chain_id == Chain.polygon:
            return AAVE_V3_POLYGON
        elif self.chain_id == Chain.ethereum:
            return AAVE_V3_ETH
        elif self.chain_id == Chain.optimism:
            return AAVE_V3_OPTIMISM

        return None

    def get_apy_defi_app(self, block_number: int = "latest"):
        return self.state_service.get_apy_lending_pool(
            pool_address=self.defi_constant.get("address"),
            incentive_address=self.defi_constant.get("incentiveAddress"),
            oracle_address=self.defi_constant.get("oracleAddress"),
            block_number=block_number,
            reserves_info=self.defi_constant.get("reservesList"),
            rewards_list=self.defi_constant.get("rewardTokensList")
        )

    def get_rewards_balance(self, wallet_address: str, block_number: int = "latest"):
        reward = self.state_service.get_rewards_balance(
            wallet_address=wallet_address,
            pool_address=self.defi_constant.get("address"),
            incentive_address=self.defi_constant.get("incentiveAddress"),
            block_number=block_number,
            reserves_info=self.defi_constant.get("reservesList")
        )
        return reward

    def get_wallet_deposit_borrow_balance(self, wallet_address: str, block_number: int = "latest"):
        return self.state_service.get_wallet_deposit_borrow_balance(
            wallet_address=wallet_address,
            pool_address=self.defi_constant.get("address"),
            oracle_address=self.defi_constant.get("oracleAddress"),
            block_number=block_number,
            reserves_info=self.defi_constant.get("reservesList"),
        )
