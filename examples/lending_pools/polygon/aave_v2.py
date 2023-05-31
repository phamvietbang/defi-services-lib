import json

from defi_services.lending_pools.aave_v2_service import AaveV2Service

if __name__ == "__main__":
    aave = AaveV2Service("0x89", "https://rpc.ankr.com/polygon")
    apy = aave.get_apy_defi_app(ethereum_price=1900)
    wrapped_native_token = aave.get_wrapped_native_token()
    deposit_borrow = aave.get_wallet_deposit_borrow_balance(
        wallet_address="0x6d16749cEfb3892A101631279A8fe7369A281D0E",
        ethereum_price=1900
    )
    claim = aave.get_rewards_balance(
        wallet_address="0x6d16749cEfb3892A101631279A8fe7369A281D0E",
    )
    print(claim)
    with open("aave_v2_apy.json", 'w') as f:
        f.write(json.dumps(apy, indent=1))
    with open("aave_v2_add.json", 'w') as f:
        f.write(json.dumps(deposit_borrow, indent=1))
