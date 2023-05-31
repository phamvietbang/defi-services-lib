import json

from defi_services.lending_pools.trava_service import TravaService

if __name__ == "__main__":
    trava = TravaService("0x1", "https://rpc.ankr.com/eth")
    apy = trava.get_apy_defi_app()
    deposit_borrow = trava.get_wallet_deposit_borrow_balance(
        wallet_address="0x13c0c2F7Eb2799a515aae280832443365E54B511",
    )
    claim = trava.get_rewards_balance(wallet_address="0x13c0c2F7Eb2799a515aae280832443365E54B511")
    print(claim)
    with open("trava_apy.json", 'w') as f:
        f.write(json.dumps(apy, indent=1))
    with open("trava_add.json", 'w') as f:
        f.write(json.dumps(deposit_borrow, indent=1))
