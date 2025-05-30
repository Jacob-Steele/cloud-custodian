from azure.appconfiguration import AzureAppConfigurationClient
from azure.identity import DefaultAzureCredential
from c7n_azure.provider import resources
from c7n_azure.resources.arm import ChildResourceManager, ChildArmResourceManager
from c7n_azure.query import ChildTypeInfo
from azure.appconfiguration.provider import load
from azure.appconfiguration.provider import SettingSelector

class AppConfigurationKeysChildResource(ChildResourceManager):

    class resource_type(ChildTypeInfo):
        doc_groups = ['Integration']

        parent_spec = ('app-configuration', True)
        parent_manager_name = 'app-configuration'
        raise_on_exception = False
        annotate_parent = True

    def get_data_client(self, parent_resource):
        print(parent_resource)
        print(parent_resource['properties']['endpoint'])
        config = load(
                    endpoint=parent_resource['properties']['endpoint'],
                    credential=DefaultAzureCredential(),
                    selects=[SettingSelector(key_filter="*")])
        return config

@resources.register('app-configuration-keys')
class AppConfigurationKeys(AppConfigurationKeysChildResource):
    """App Configuration Keys Resource using Data Plane API"""
    
    def enumerate_resources(self, parent_resource, type_info, vault_url=None, **params):
        data_client = self.get_data_client(parent_resource)
        print("DATA")
        print(data_client.keys())
        print(data_client.items())
        print(data_client["message"])
        return []

    # class resource_type(ChildTypeInfo):
    #     doc_groups = ['Integration']
    #     parent_spec = ('app-configuration', True)
    #     parent_manager_name = 'app-configuration'
    #     raise_on_exception = False
    #     annotate_parent = True
        
    #     # service = 'azure.mgmt.appconfiguration'
    #     # client = 'AppConfigurationManagementClient'
    #     diagnostic_settings_enabled = False
    #     # enum_spec = ('configuration_stores', 'list', None)
    #     # parent_manager_name = 'app-configuration'
    #     resource_type = 'Microsoft.AppConfiguration/configurationStores/keyValues'

    def get_resources(self, resource_ids=None):
        """Get all key-values using App Configuration Data Plane API"""
        resources = []
        print("HER - get_resources")
        parent_manager = self.get_parent_manager()
        app_configs = parent_manager.get_resources()

        credential = DefaultAzureCredential()
        for app_config in app_configs:
            try:
                # Get the endpoint URL
                endpoint = f"https://{app_config['name']}.azconfig.io"
                
                # Create data plane client
                client = AzureAppConfigurationClient(
                    base_url=endpoint,
                    credential=credential
                )
                
                # List all configuration settings (key-values)
                settings = client.list_configuration_settings()
                
                for setting in settings:
                    kv_data = {
                        'key': setting.key,
                        'value': setting.value,
                        'label': setting.label,
                        'content_type': setting.content_type,
                        'etag': setting.etag,
                        'last_modified': setting.last_modified.isoformat() if setting.last_modified else None,
                        'locked': setting.read_only,
                        'tags': setting.tags,
                        'parent_configuration_store': app_config['name'],
                        'parent_resource_group': app_config['resourceGroup'],
                        'endpoint': endpoint
                    }
                    resources.append(kv_data)
                    
            except Exception as e:
                self.log.warning(f"Failed to get keys for App Configuration {app_config['name']}: {e}")
                
        return resources