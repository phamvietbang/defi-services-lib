from defi_services.constants.chain_constant import Chain
from defi_services.defi_service import DefiService
from defi_services.lending_pools.lending_pools_info.ethereum.compound_eth import COMPOUND_ETH
from defi_services.lending_pools.services.compound_state_service import CompoundStateService


class CompoundService(DefiService):
    name = "compound lending pool"

    def __init__(self, chain_id: str, provider_uri: str):
        super().__init__(chain_id, provider_uri)
        self.state_service = CompoundStateService(provider_uri)
        self.defi_constant = self._get_constant()

    def _get_constant(self):
        if self.chain_id == Chain.ethereum:
            return COMPOUND_ETH
        return None

    def get_pool_token(self):
        return self.defi_constant.get("rewardToken")

    def get_apy_defi_app(self, block_number: int = "latest", **kwargs):
        return self.state_service.get_apy_lending_pool(
            comptroller_address=self.defi_constant.get("comptrollerAddress"),
            lens_address=self.defi_constant.get("lensAddress"),
            pool_token_price=float(kwargs.get("pool_token_price")),
            wrapped_native_token_price=1,
            block_number=block_number
        )

    def get_rewards_balance(self, wallet_address: str, block_number: int = "latest"):
        return self.state_service.get_rewards_balance(
            wallet_address=wallet_address,
            comptroller_address=self.defi_constant.get("comptrollerAddress"),
            lens_address=self.defi_constant.get("lensAddress"),
            pool_token=self.defi_constant.get("rewardToken"),
            block_number=block_number
        )

    def get_wallet_deposit_borrow_balance(self, wallet_address: str, block_number: int = "latest", **kwargs):
        return self.state_service.get_wallet_deposit_borrow_balance(
            wallet_address=wallet_address,
            lens_address=self.defi_constant.get("lensAddress"),
            reserves_info=self.defi_constant.get("reservesList"),
            wrapped_native_token_price=1,
            block_number=block_number,
            wrapped_native_token=self.get_wrapped_native_token()
        )
