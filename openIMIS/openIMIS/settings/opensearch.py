import os 



os_hosts = os.environ.get("OPENSEARCH_HOSTS", "opensearch:9200")


OPEN_SEARCH_HTTP_PORT = os.environ.get("OPEN_SEARCH_HTTP_PORT", "9200")
OPENSEARCH_DSL_AUTOSYNC = os.environ.get('OPENSEARCH_DSL_AUTOSYNC', 'True') == 'True' 

OPENSEARCH_DSL = {
    'default': {
        'hosts': os_hosts.split(','),
        'http_auth': (
            f"{os.environ.get('OPENSEARCH_ADMIN')}",
            f"{os.environ.get('OPENSEARCH_PASSWORD')}"
        ),
        'timeout': 120,
    }
}
