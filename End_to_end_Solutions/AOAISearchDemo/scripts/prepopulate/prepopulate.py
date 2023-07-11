import argparse
import yaml
from azure.core.credentials import AzureKeyCredential
from azure.identity import AzureDeveloperCliCredential
from common.contracts.access_rule import Member, MemberType, Resource
from common.contracts.group import User
from common.contracts.resource import ResourceTypes
from data.managers.entities.api.manager import EntitiesManager
from data.managers.permissions.manager import PermissionsManager
from typing import List, Set

def read_yaml(file_path, verbose) -> dict:
    if verbose: print(f"Reading YAML file: {file_path}")
    with open(file_path, "r") as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise Exception(f"Error reading YAML file: {exc}")
        
parser = argparse.ArgumentParser(
    description="pre-populate Cosmos DB containers with required starter data.",
    epilog="Example: prepopulate.py --entities_path ./entries/entities.yaml --permissions_path ./entries/permissions.yaml"
)
parser.add_argument("--entitiespath", help="The path to the YAML file containing the entities to prepopulate the DB with.")
parser.add_argument("--permissionspath", help="The path to the YAML file containing the permissions to prepopulate the DB with.")
parser.add_argument("--cosmosdbendpoint", help="The endpoint for the Cosmos database to prepopulate.")
parser.add_argument("--cosmosdbkey", required=False, help="Optional. The key for the Cosmos database to prepopulate.")
parser.add_argument("--cosmosdbname", help="The name of the Cosmos database to prepopulate.")
parser.add_argument("--cosmosdbentitiescontainername", help="The name of the Cosmos container to prepopulate with entities.")
parser.add_argument("--cosmosdbpermissionscontainername", help="The name of the Cosmos container to prepopulate with permissions.")
parser.add_argument("--tenantid", required=False, help="Optional. Use this to define the Azure directory where to authenticate.")
parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output.")
args = parser.parse_args()
        
entities = read_yaml(args.entitiespath, args.verbose)
permissions = read_yaml(args.permissionspath, args.verbose)
# Use the current user identity to connect to Azure services unless a key is explicitly set for any of them
azd_credential = AzureDeveloperCliCredential() if args.tenantid == None else AzureDeveloperCliCredential(
    tenant_id=args.tenantid)
cosmos_creds = azd_credential if args.cosmosdbkey == None else AzureKeyCredential(args.cosmosdbkey)

if args.verbose: print("Initializing data managers...")

entities_manager = EntitiesManager(args.cosmosdbendpoint, cosmos_creds, args.cosmosdbname, args.cosmosdbentitiescontainername)
permissions_manager = PermissionsManager(args.cosmosdbendpoint, cosmos_creds, args.cosmosdbname, args.cosmosdbpermissionscontainername)

# Prepopulate entities container

if args.verbose: print("Prepopulating entities container...")
for user in entities["users"]:
    user_id = user["user_id"]
    user_name = user["user_name"]
    description = user["description"]
    sample_questions = user["sample_questions"]
    entities_manager.create_user_profile(user_id, user_name, description, sample_questions)

for group in entities["groups"]:
    group_id = group["group_id"]
    group_name = group["group_name"]
    users: Set[User] = set()
    for user in group["users"]:
        users.add(User(user["user_id"]))
    entities_manager.create_user_group(group_id, group_name, users)

for resource in entities["resources"]:
    resource_id = resource["resource_id"]
    resource_type = ResourceTypes(resource["resource_type"])
    entities_manager.create_resource(resource_id, resource_type)

# Prepopulate permissions container

if args.verbose: print("Prepopulating permissions container...")
for access_rule in permissions["access_rules"]:
    rule_id = access_rule["rule_id"]
    resources: List[Resource] = []
    for resource in access_rule["resources"]:
        resources.append(Resource(resource["resource_id"]))
    members: List[Member] = []
    for member in access_rule["members"]:
        members.append(Member(member["id"], MemberType(member["member_type"])))
    permissions_manager.create_access_rule(rule_id, resources, members)

if args.verbose: print("Done.")