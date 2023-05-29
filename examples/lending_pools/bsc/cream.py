import json

from defi_services.lending_pools.cream_service import CreamService

if __name__ == "__main__":
    cream = CreamService("0x38", "https://bsc-dataseed1.binance.org/")
    pool_token = cream.get_pool_token()
    wrapped_native_token = cream.get_wrapped_native_token()
    apy = cream.get_apy_defi_app(pool_token_price=21.7, wrapped_native_token_price=306.17)
    deposit_borrow = cream.get_wallet_deposit_borrow_balance(
        wallet_address="0x22a65db6e25073305484989aE55aFf0687E68566",
        wrapped_native_token_price=306.17
    )
    claim = cream.get_rewards_balance(wallet_address="0x22a65db6e25073305484989aE55aFf0687E68566")
    print("claimable: ", claim)
    print("pool token: ", pool_token)
    print("wrapped_native_token", wrapped_native_token)
    with open("cream_apy.json", 'w') as f:
        f.write(json.dumps(apy, indent=1))
    with open("cream_add.json", 'w') as f:
        f.write(json.dumps(deposit_borrow, indent=1))
