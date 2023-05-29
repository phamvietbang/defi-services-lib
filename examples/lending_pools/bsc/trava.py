import json

from examples.lending_pools.bsc.lending_pools_info.trava import TRAVA
from src.defi_services.lending_pools.bsc.trava_state_service import TravaStateService

if __name__ == "__main__":
    trava = TravaStateService("https://rpc.ankr.com/bsc")
    apy = trava.get_apy_lending_pool(
        pool_address=TRAVA.get("address"),
        staked_incentive_address=TRAVA.get("stakedIncentiveAddress"),
        oracle_address=TRAVA.get("oracleAddress"),
    )
    claim = trava.get_wallet_information_in_lending_pool(
        wallet_address="0x13c0c2F7Eb2799a515aae280832443365E54B511",
        staked_incentive_address=TRAVA.get("stakedIncentiveAddress"),
        reserves_info=TRAVA.get("reservesList"),
        oracle_address=TRAVA.get("oracleAddress"),
        staked_token_price=0.00041267
    )
    with open("trava_apy.json", 'w') as f:
        f.write(json.dumps(apy, indent=1))
    with open("trava_add.json", 'w') as f:
        f.write(json.dumps(claim, indent=1))
