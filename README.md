# BAE SmartMaaS NGSI Plugin
[![Documentation badge](https://img.shields.io/readthedocs/business-api-ecosystem.svg)](https://business-api-ecosystem.rtfd.io)
[![NGSI-LD badge](https://img.shields.io/badge/NGSI-LD-red.svg)](https://www.etsi.org/deliver/etsi_gs/CIM/001_099/009/01.02.01_60/gs_cim009v010201p.pdf)
[![NGSI v2](https://nexus.lab.fiware.org/repository/raw/public/badges/specifications/ngsiv2.svg)](http://fiware-ges.github.io/orion/api/v2/stable/)

This plugin for the <b>Business API Ecosystem</b> supports both the <b>Tenant-Manager</b> authorization process and 
the <b>Keyrock</b> to allow API access to NGSIv2 and NGSI-LD in APInf.  It is specifically designed for the architecture
of the FIWARE SmartMaaS platform.

The plugin checks whether a seller in the marketplace in Tenant Manager is authorized to sell the corresponding product 
for his logged in organization (tenant).
 
The product specific role that a seller specifies during the product creation is the role that is assigned to the buyer 
during the buying process to allow access to the data via keyrock.
In addition, for access to the NGSIv2 and NGSI-LD APIs in APInf, the buyer is assigned a data consumer role in the 
tenant manager of the respective organization (tenant).

Who can sell the products?
1) The owner of an organization (tenant)
2) A member of an organization (tenant) who has the role <b>data-provider</b> in the tenant manager. The sale can be executed 
by the seller switching to the organization (tenant) in the marketplace.


## Installation

* Create zip file

```bash
sudo apt install zip

zip smartmaas-ngsi-query.zip smartmaas_ngsi_query.py keyrock_client.py package.json settings.py tenant_manager_client.py
```

* Copy zip file into business-ecosystem-charging-backend container

```bash
sudo docker cp smartmaas-ngsi-query.zip <container-id>:/business-ecosystem-charging-backend/src/plugins/
```

* Load Plugin

```bash
./manage.py loadplugin ./plugins/smartmaas-ngsi-query.zip
```

## Plugin Management

* List available plugins

```bash
python manage.py listplugins
```

This command will return the list of available plugins including the id that have been generated for them

* Uninstallation

```bash
python manage.py removeplugin <plugin-id>
```