import json

from defi_services.lending_pools.geist_service import GeistService

if __name__ == "__main__":
    trava = GeistService("0xfa", "https://rpc.ankr.com/fantom")
    apy = trava.get_apy_defi_app()
    deposit_borrow = trava.get_wallet_deposit_borrow_balance(
        wallet_address="0xDC18517d7f2EffC6ccE195f5a2Bf64AB52367AD3",
    )
    claim = trava.get_rewards_balance(wallet_address="0xDC18517d7f2EffC6ccE195f5a2Bf64AB52367AD3")
    print(claim)
    with open("geist_apy.json", 'w') as f:
        f.write(json.dumps(apy, indent=1))
    with open("geist_add.json", 'w') as f:
        f.write(json.dumps(deposit_borrow, indent=1))
