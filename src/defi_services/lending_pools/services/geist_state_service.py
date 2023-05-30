from defi_services.lending_pools.services.valas_state_service import ValasStateService


class GeistStateService(ValasStateService):
    def __init__(self, provider_uri: str):
        super().__init__(provider_uri)


if __name__ == "__main__":
    import json
    from defi_services.lending_pools.lending_pools_info.fantom.geist_ftm import GEIST_ETH
    from defi_services.abis.lending_pool.lending_pool_abi import LENDING_POOL_ABI

    service = GeistStateService(provider_uri="https://rpc.ankr.com/fantom")
    reserve_info = service.get_reserves_info(GEIST_ETH.get("address"), LENDING_POOL_ABI)
    with open("geist.json", "w") as f:
        f.write(json.dumps(reserve_info, indent=1))
