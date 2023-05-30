from defi_services.lending_pools.services.valas_state_service import ValasStateService


class RadiantStateService(ValasStateService):
    def __init__(self, provider_uri: str):
        super().__init__(provider_uri)


if __name__ == "__main__":
    import json
    from defi_services.lending_pools.lending_pools_info.bsc.radiant_bsc import RADIANT_BSC
    from defi_services.lending_pools.lending_pools_info.arbitrum.radiant_arbitrum import RADIANT_ARB
    from defi_services.abis.lending_pool.lending_pool_abi import LENDING_POOL_ABI

    service = RadiantStateService(provider_uri="https://rpc.ankr.com/bsc")
    reserve_info = service.get_reserves_info(RADIANT_BSC.get("address"), LENDING_POOL_ABI)
    with open("radiant.json", "w") as f:
        f.write(json.dumps(reserve_info, indent=1))
    service = RadiantStateService(provider_uri="https://rpc.ankr.com/arbitrum")
    reserve_info = service.get_reserves_info(RADIANT_ARB.get("address"), LENDING_POOL_ABI)
    with open("radiant.json", "w") as f:
        f.write(json.dumps(reserve_info, indent=1))
