from os import environ


def get_config():
    cluster_param = environ.get('SOLANA_CLUSTER')
    assert cluster_param is not None, "SOLANA_CLUSTER environment variable must be set"
    switch={
        'mainnet':{'cluster': 'mainnet', 'cluster_label': 'Mainnet'},
        'testnet':{'cluster': 'testnet', 'cluster_label': 'Testnet'},
        'devnet':{'cluster': 'devnet', 'cluster_label': 'Devnet'},
    }
    config = switch.get(cluster_param.lower())
    assert config is not None, f"No Config for " + cluster_param
    return config
