import json

from defi_services.lending_pools.aave_v3_service import AaveV3Service

if __name__ == "__main__":
    aave = AaveV3Service("0xa4b1", "")
    apy = aave.get_apy_defi_app(wrapped_native_token_price=1900)
    wrapped_native_token = aave.get_wrapped_native_token()
    deposit_borrow = aave.get_wallet_deposit_borrow_balance(
        wallet_address="0x83d8a9988756fee758ab9f73d0f0cdd4242bd16a",
        wrapped_native_token_price=1900
    )
    claim = aave.get_rewards_balance(
        wallet_address="0x83d8a9988756fee758ab9f73d0f0cdd4242bd16a",
    )
    print(claim)
    with open("aave_v2_apy.json", 'w') as f:
        f.write(json.dumps(apy, indent=1))
    with open("aave_v2_add.json", 'w') as f:
        f.write(json.dumps(deposit_borrow, indent=1))