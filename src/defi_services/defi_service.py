from defi_services.state_service import StateService


class DefiService:
    def __init__(self, chain_id: str, provider_uri: str):
        self.provider_uri = provider_uri
        self.chain_id = chain_id

    def _get_constant(self):
        pass

    def get_apy_defi_app(self, block_number: int = "latest"):
        pass

    def get_rewards_balance(self, wallet_address: str, block_number: int = "latest"):
        pass

    def get_wallet_deposit_borrow_balance(self, wallet_address: str, block_number: int = "latest"):
        pass

