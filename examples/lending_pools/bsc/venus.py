import json

from defi_services.abis.lending_pool.venus_lens_abi_v1 import VENUS_LENS_ABI_V1
from defi_services.lending_pools.venus_service import VenusService

if __name__ == "__main__":
    venus = VenusService("0x38","https://bsc-dataseed1.binance.org/")
    pool_token = venus.get_pool_token()
    apy = venus.get_apy_defi_app(
        pool_token_price=4.9,
    )
    deposit_borrow = venus.get_wallet_deposit_borrow_balance(
        wallet_address="0xb2952147dfb18bb64c208ea8bcfb198c34abf694",
    )
    claim = venus.get_rewards_balance(
        wallet_address="0xb2952147dfb18bb64c208ea8bcfb198c34abf694"
    )
    print("claimable: ", claim)
    print("pool token: ", pool_token)
    with open("venus_apy.json", 'w') as f:
        f.write(json.dumps(apy, indent=1))
    with open("venus_add.json", 'w') as f:
        f.write(json.dumps(deposit_borrow, indent=1))
