# tusc-swap

Built with Python 3.7.3

Prereqs:
Run `pip3 install web3 requests bottle`
Note: on linux you might need `sudo` on Windows you might need to run as admin.

Setting up an AWS node:

AMI: amzn2-ami-hvm-2.0.20190618-x86_64-gp2 (ami-0d8f6eb4f641ef691)

1. Get prereqs:
    1. `sudo yum install git gcc python3 python3-dev postgresql postgresql-libs postgresql-devel`
    1. `sudo pip3 install web3 requests bottle pyyaml psycopg2`
1. Setup db:
    1. `sudo postgresql-setup initdb`
    1. `sudo systemctl enable postgresql.service`
    1. `sudo su - postgres`
    1. `psql -U postgres`
    1. You'll be in the PSQL prompt now.
    1. Change the postgres user password
        1. `ALTER USER postgres WITH PASSWORD '{password}';`
    1. Make the tusc-swap database and tables:
        1. `create database "tusc-swap";`
        1. Run the two `create table` commands in db_access/scripts/0001-init.sql
    1. Exit psql and exit bash
        1. `\q`
        1. `exit`
1. Setup code:
    1. `mkdir swapper`
    1. `cd swapper`
    1. `git clone https://github.com/TUSCNetwork/tusc-swap.git`
1. Set the local_config.yaml settings:
    1. cd ~/swapper/tusc-swap/configs
    1. `sudo nano local_config.yaml`
    1. Ensure the db:password, eth_api:api_key, and eth_api:occ_contract_address are all set correctly.
1. Run the registerer
    1. `screen`
    1. `sudo python3 registerer_main.py`
    1. Ctrl-a, Ctrl-d (to detach from the screen running registerer)
1. Configure swapper to run every 5 minutes

 

sudo yum install python3-devel
## Design

There are two main portions to this program
1. The registration backend
2. The swapper