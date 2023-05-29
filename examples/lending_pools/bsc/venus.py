import json

from src.defi_services.abis.lending_pool.venus_lens_abi_v1 import VENUS_LENS_ABI_V1
from src.defi_services.lending_pools.bsc.venus_state_service import VenusStateService
from examples.lending_pools.bsc.lending_pools_info.venus import VENUS

if __name__ == "__main__":
    venus = VenusStateService("https://bsc-dataseed1.binance.org/")
    apy = venus.get_apy_lending_pool(
        comptroller_address=VENUS.get("comptrollerAddress"),
        lens_address=VENUS.get("lensAddress"),
        reserves_info=VENUS.get("reservesList"),
        pool_token_price=4.9,
        lens_abi=VENUS_LENS_ABI_V1,
    )
    claim = venus.get_wallet_information_in_lending_pool(
        comptroller_address=VENUS.get("comptrollerAddress"),
        lens_address=VENUS.get("lensAddress"),
        pool_token_price=4.9,
        reserves_info=VENUS.get("reservesList"),
        pool_token=VENUS.get("rewardToken"),
        wallet_address="0xb2952147dfb18bb64c208ea8bcfb198c34abf694",
    )
    with open("venus_apy.json", 'w') as f:
        f.write(json.dumps(apy, indent=1))
    with open("venus_add.json", 'w') as f:
        f.write(json.dumps(claim, indent=1))
