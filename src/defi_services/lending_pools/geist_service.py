from defi_services.constants.chain_constant import Chain
from defi_services.defi_service import DefiService
from defi_services.lending_pools.lending_pools_info.fantom.geist_ftm import GEIST_ETH
from defi_services.lending_pools.services.geist_state_service import GeistStateService


class GeistService(DefiService):
    name = "geist lending pool"

    def __init__(self, chain_id: str, provider_uri: str):
        super().__init__(chain_id, provider_uri)
        self.state_service = GeistStateService(provider_uri)
        self.defi_constant = self._get_constant()

    def _get_constant(self):
        if self.chain_id == Chain.fantom:
            return GEIST_ETH
        return None

    def get_apy_defi_app(self, block_number: int = "latest"):
        return self.state_service.get_apy_lending_pool(
            pool_address=self.defi_constant.get("address"),
            chef_incentive_address=self.defi_constant.get("chefIncentiveAddress"),
            oracle_address=self.defi_constant.get("oracleAddress"),
            block_number=block_number
        )

    def get_rewards_balance(self, wallet_address: str, block_number: int = "latest"):
        return self.state_service.get_rewards_balance(
            wallet_address=wallet_address,
            pool_address=self.defi_constant.get("address"),
            multi_fee_address=self.defi_constant.get("multiFeeAddress"),
            block_number=block_number,
            reserves_info=self.defi_constant.get("reservesList")
        )

    def get_wallet_deposit_borrow_balance(self, wallet_address: str, block_number: int = "latest"):
        return self.state_service.get_wallet_deposit_borrow_balance(
            wallet_address=wallet_address,
            pool_address=self.defi_constant.get("address"),
            oracle_address=self.defi_constant.get("oracleAddress"),
            block_number=block_number,
            reserves_info=self.defi_constant.get("reservesList")
        )
