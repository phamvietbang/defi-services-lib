import json

from defi_services.lending_pools.valas_service import ValasService

if __name__ == "__main__":
    trava = ValasService("0x38","https://rpc.ankr.com/bsc")
    apy = trava.get_apy_defi_app()
    deposit_borrow = trava.get_wallet_deposit_borrow_balance(
        wallet_address="0xa3CDBDCa01719Faf5fEBFF95c868Fd200F946808",
    )
    claim = trava.get_rewards_balance(wallet_address="0xa3CDBDCa01719Faf5fEBFF95c868Fd200F946808")
    print(claim)
    with open("valas_apy.json", 'w') as f:
        f.write(json.dumps(apy, indent=1))
    with open("valas_add.json", 'w') as f:
        f.write(json.dumps(deposit_borrow, indent=1))