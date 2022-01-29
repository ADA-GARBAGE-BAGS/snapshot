import json
import subprocess
from blockfrost import BlockFrostApi, ApiUrls, ApiError

# policy ids
POLICY_IDS = {
    "bag": "e3fe2263817d7e1f3bd3559d615c7ec6428b17755f332576046aebb0",
    "pfp": "bd1abcb0014b6025d0dc305a31777a434087dbbb8555ee726eeff64c",
    "bills": "11b5680e5117ece0b477aaa3e76949d9dbf66dbcfc61f61f611ad035",
}
DISTRIBUTION_COUNT = {"bag": 4347826087, "bills": 3000000000, "pfp": 1190476190}


api = BlockFrostApi(
    project_id="",
    base_url=ApiUrls.mainnet.value,
)


def fetch_addresses(policy_id, count):
    try:
        addys = []
        for i in range(count):
            assets = api.assets_policy(policy_id, page=i + 1)

            for asset in assets:
                addy = api.asset_addresses(asset.asset)[0]
                final_addy = ""
                # dao wallet
                # skip since itll get the remaining tokens
                if (
                    addy.address
                    == "addr1qypvuf2ex7dlsql59yeqq9qhfzzpuevd9lqclrfsxjw46l5k8sklhukchdqmuc9mwrmctl0q3lyglfqpyvwfsgywj2aqr0astu"
                ):
                    continue

                # is smart contract_addy
                if addy.address.startswith("addr1w"):
                    # newest first
                    transactions = api.asset_transactions(asset.asset, order="desc")
                    # fetch transaction before latest
                    # "asset listing"
                    proper_tx = None
                    for tx in transactions:
                        specific_tx = api.transaction_utxos(tx.tx_hash)
                        if not specific_tx.inputs[0].address.startswith("addr1w"):
                            proper_tx = specific_tx.inputs[0].address
                            break

                    final_addy = proper_tx
                else:
                    final_addy = addy.address

                addys.append(final_addy)
        return addys
    except ApiError as e:
        print(e)


def dump_list():
    stake_addys = {}

    final_list = {"bag": [], "bills": [], "pfp": []}
    print("fetching baags")
    bag_addresses = fetch_addresses(POLICY_IDS["bag"], 3)
    print("fetching bills")
    bills_addresses = fetch_addresses(POLICY_IDS["bills"], 2)
    print("fetching pfps")
    pfp_addresses = fetch_addresses(POLICY_IDS["pfp"], 5)

    final_list["bag"].extend(bag_addresses)
    final_list["bills"].extend(bills_addresses)
    final_list["pfp"].extend(pfp_addresses)

    for key in list(final_list.keys()):
        for addy in final_list[key]:
            fetched_addy = api.address(addy)
            stake_address = fetched_addy.stake_address
            if stake_address in stake_addys:
                stake_addys[stake_address]["tokens"] += DISTRIBUTION_COUNT[key]
                stake_addys[stake_address]["addys"].append(addy)
            else:
                stake_addys[stake_address] = {}
                stake_addys[stake_address]["tokens"] = DISTRIBUTION_COUNT[key]
                stake_addys[stake_address]["addys"] = []
                stake_addys[stake_address]["addys"].append(addy)

    with open("count.json", "w", encoding="utf-8") as json_file:
        json.dump(stake_addys, json_file, ensure_ascii=False, indent=4)


def contruct_airdrop_transaction(start, end):
    data = None
    with open("count.json", "r") as f:
        data = json.load(f)

    keys = list(data.keys())[start:end]
    tx_outs = []
    total_token_sum = 0
    total_dust_fee = 0

    for key in keys:
        print(
            f'{key} is receiving {data[key]["tokens"]} trash tokens through {data[key]["addys"][0]}'
        )

        tx_outs.append("--tx-out")
        tx_out_string = f"{data[key]['addys'][0]}+1400000+{data[key]['tokens']} d22965688923872616453710f5e00a8f71ed644dbc6c6c06863b5579.TRASH"
        tx_outs.append(tx_out_string)
        total_dust_fee += 1400000
        total_token_sum += data[key]["tokens"]

    commands = [
        "cardano-cli",
        "transaction",
        "build-raw",
        "--tx-in",
        "hash#index",
        "--tx-out",
        "addy+0+0 d22965688923872616453710f5e00a8f71ed644dbc6c6c06863b5579.TRASH",
    ]
    commands.extend(tx_outs)
    commands.extend(["--fee", "0", "--out-file", "matx.raw"])
    subprocess.run(commands)

    print(total_dust_fee)
    print(total_token_sum)
    print(len(keys))


contruct_airdrop_transaction(0, 100)
contruct_airdrop_transaction(100, 250)
