import json

from src.defi_services.lending_pools.bsc.cream_state_service import CreamStateService
from examples.lending_pools.bsc.lending_pools_info.cream import CREAM

if __name__ == "__main__":
    cream = CreamStateService("https://bsc-dataseed1.binance.org/")
    apy = cream.get_apy_lending_pool(
        comptroller_address=CREAM.get("comptrollerAddress"),
        lens_address=CREAM.get("lensAddress"),
        pool_token_price=24.7,
        wrapped_native_token_price=306.17,
    )
    claim = cream.get_wallet_information_in_lending_pool(
        comptroller_implementation_address=CREAM.get("comptrollerImplementationAddress"),
        lens_address=CREAM.get("lensAddress"),
        pool_token_price=4.9,
        reserves_info=CREAM.get("reservesList"),
        pool_token=CREAM.get("rewardToken"),
        wallet_address="0x22a65db6e25073305484989aE55aFf0687E68566",
        wrapped_native_token_price=306.17
    )
    with open("cream_apy.json", 'w') as f:
        f.write(json.dumps(apy, indent=1))
    with open("cream_add.json", 'w') as f:
        f.write(json.dumps(claim, indent=1))
