import json

from defi_services.lending_pools.bsc.lending_pools_info.valas import VAlAS
from defi_services.lending_pools.bsc.valas_state_service import ValasStateService

if __name__ == "__main__":
    trava = ValasStateService("https://rpc.ankr.com/bsc")
    apy = trava.get_apy_lending_pool(
        pool_address=VAlAS.get("address"),
        chef_incentive_address=VAlAS.get("chefIncentiveAddress"),
        oracle_address=VAlAS.get("oracleAddress"),
    )
    claim = trava.get_wallet_information_in_lending_pool(
        wallet_address="0xa3CDBDCa01719Faf5fEBFF95c868Fd200F946808",
        multi_fee_address=VAlAS.get("multiFeeAddress"),
        reserves_info=VAlAS.get("reservesList"),
        oracle_address=VAlAS.get("oracleAddress"),
        staked_token_price=0.00041267
    )
    with open("valas_apy.json", 'w') as f:
        f.write(json.dumps(apy, indent=1))
    with open("valas_add.json", 'w') as f:
        f.write(json.dumps(claim, indent=1))