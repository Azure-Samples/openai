import argparse
import pyodbc
from azure.core.exceptions import HttpResponseError
from azure.identity import AzureDeveloperCliCredential
from azure.mgmt.sql import SqlManagementClient
from azure.mgmt.sql.models import FirewallRule
import pandas as pd
from requests import get
from time import sleep

parser = argparse.ArgumentParser(
    description="pre-populate SQL Database with required starter data.",
    epilog="Example: populate_sql.py --sql_connection_string <SQL-CONNECTION-STRING>"
)
parser.add_argument("--sqlconnectionstring", help="The connection string to the SQL Database.")
parser.add_argument("--subscriptionid", help="The subscription id of the Azure subscription containing the SQL resource.")
parser.add_argument("--resourcegroup", help="The name of the Azure resource group containing the SQL resource.")
parser.add_argument("--servername", help="The name of the SQL Server.")
parser.add_argument("--tenantid", required=False, help="Optional. Use this to define the Azure directory where to authenticate.")
parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output.")
args = parser.parse_args()

# Add Firewall rule to SQL Server
if args.verbose: print("Adding firewall rule to SQL Server")
external_ip_address = get('https://api.ipify.org').content.decode('utf8')
azd_credential = AzureDeveloperCliCredential() if args.tenantid == None else AzureDeveloperCliCredential(
    tenant_id=args.tenantid)
client = SqlManagementClient(azd_credential, args.subscriptionid)
firewall_rule_name = 'prepopulation_client_access'
params = FirewallRule(
  name=firewall_rule_name, 
  start_ip_address=external_ip_address, 
  end_ip_address=external_ip_address)
client.firewall_rules.create_or_update(args.resourcegroup, args.servername, firewall_rule_name, params)

if args.verbose: print("Polling for firewall rule to be created...")
firewall_rule = None
for _ in range(10):
  try:
    firewall_rule = client.firewall_rules.get(args.resourcegroup, args.servername, firewall_rule_name)
  except HttpResponseError as e:
    if e.status_code == 404:
      sleep(1)
    else:
      raise Exception(f"Error while polling for firewall rule: {e}")

if firewall_rule == None:
  raise Exception("Timed out while waiting for firewall rule to be created.")

# Connect to SQL Database
if args.verbose: print("Connecting to SQL Database")
cnxn = pyodbc.connect(args.sqlconnectionstring)
cursor = cnxn.cursor()

if args.verbose: print("Creating Tables")
# CREATE TABLES
cursor.execute("""
CREATE TABLE Customers (
  cust_id INTEGER,
  cust_name VARCHAR(1000),
  cust_email VARCHAR(1000),
  cust_phone VARCHAR(1000),
  cust_address VARCHAR(1000),
  PRIMARY KEY (cust_id)
);

CREATE TABLE Products (
  prod_id INTEGER,
  prod_name VARCHAR(1000),
  price FLOAT,
  category VARCHAR(1000),
  PRIMARY KEY (prod_id)
);

CREATE TABLE Merchants (
  merchant_id INTEGER,
  merchant_name VARCHAR(1000),
  merchant_region VARCHAR(1000),
  merchant_address VARCHAR(1000),
  PRIMARY KEY (merchant_id)
);

CREATE TABLE Stock (
  prod_id INTEGER,
  merchant_id INTEGER,
  stock INTEGER,
  PRIMARY KEY (prod_id, merchant_id),
  FOREIGN KEY (merchant_id) REFERENCES Merchants(merchant_id),
  FOREIGN KEY (prod_id) REFERENCES Products(prod_id)
);

CREATE TABLE Sales (
    sale_id INTEGER,
    cust_id INTEGER,
    merchant_id INTEGER,
    date DATETIME,
    total_price FLOAT,
    PRIMARY KEY (sale_id),
    FOREIGN KEY (cust_id) REFERENCES Customers(cust_id),
    FOREIGN KEY (merchant_id) REFERENCES Merchants(merchant_id)
);

CREATE TABLE Sales_Detail (
  sales_id INTEGER,
  prod_id INTEGER,
  quantity INTEGER,
  PRIMARY KEY (sales_id, prod_id),
  FOREIGN KEY (sales_id) REFERENCES Sales(sale_id),
  FOREIGN KEY (prod_id) REFERENCES Products(prod_id)
);
""") 


# Populate Data
if args.verbose: print("Populating Data")

def insert_data(cursor, inject_query, data_path):
    data = pd.read_csv (data_path)   
    df = pd.DataFrame(data)
    data = df.values.tolist()

    cursor.fast_executemany = True
    cursor.executemany(inject_query, data)

insert_data(cursor, "INSERT INTO Customers (cust_id,cust_name,cust_email,cust_phone,cust_address) VALUES (?,?,?,?,?)", './scripts/prepopulate/sql_data/customers.csv')
insert_data(cursor, "INSERT INTO Products (prod_id, prod_name, price, category) VALUES (?,?,?,?)", './scripts/prepopulate/sql_data/products.csv')
insert_data(cursor, "INSERT INTO Merchants (merchant_id,merchant_name,merchant_region,merchant_address) VALUES (?,?,?,?)", './scripts/prepopulate/sql_data/merchants.csv')
insert_data(cursor, "INSERT INTO Stock (prod_id,merchant_id,stock) VALUES (?,?,?)", './scripts/prepopulate/sql_data/stock.csv')
insert_data(cursor, "INSERT INTO Sales (sale_id,cust_id,merchant_id,date,total_price) VALUES (?,?,?,?,?)", './scripts/prepopulate/sql_data/sales.csv')
insert_data(cursor, "INSERT INTO Sales_Detail (sales_id,prod_id,quantity) VALUES (?,?,?)", './scripts/prepopulate/sql_data/sales_detail.csv')

cnxn.commit()

if args.verbose: print("Deleting firewall rule from SQL Server")
client.firewall_rules.delete(args.resourcegroup, args.servername, firewall_rule_name)