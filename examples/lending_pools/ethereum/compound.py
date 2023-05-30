import json

from defi_services.lending_pools.compound_service import CompoundService

if __name__ == "__main__":
    compound = CompoundService("0x1", "https://rpc.ankr.com/eth")
    pool_token = compound.get_pool_token()
    wrapped_native_token = compound.get_wrapped_native_token()
    apy = compound.get_apy_defi_app(pool_token_price=36.96, wrapped_native_token_price=1900)
    deposit_borrow = compound.get_wallet_deposit_borrow_balance(
        wallet_address="0x19B114F57C89cf38903362Cc467587d9611C6825",
        wrapped_native_token_price=1900
    )
    claim = compound.get_rewards_balance(wallet_address="0x19B114F57C89cf38903362Cc467587d9611C6825")
    print("claimable: ", claim)
    print("pool token: ", pool_token)
    print("wrapped_native_token", wrapped_native_token)
    with open("compound_apy.json", 'w') as f:
        f.write(json.dumps(apy, indent=1))
    with open("compound_add.json", 'w') as f:
        f.write(json.dumps(deposit_borrow, indent=1))
