import json

from defi_services.lending_pools.radiant_service import RadiantService

if __name__ == "__main__":
    radiant = RadiantService("0x38","https://rpc.ankr.com/bsc")
    apy = radiant.get_apy_defi_app()
    deposit_borrow = radiant.get_wallet_deposit_borrow_balance(
        wallet_address="0x8A4390649869Cf349B08f9800Fce5C15C1FFFE88",
    )
    claim = radiant.get_rewards_balance(wallet_address="0x8A4390649869Cf349B08f9800Fce5C15C1FFFE88")
    print(claim)
    with open("radiant_apy.json", 'w') as f:
        f.write(json.dumps(apy, indent=1))
    with open("radiant_add.json", 'w') as f:
        f.write(json.dumps(deposit_borrow, indent=1))