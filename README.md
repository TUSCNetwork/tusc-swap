# tusc-swap

Built with Python 3.7.3

Prereqs:
Run `pip3 install web3 requests bottle`
Note: on linux you might need `sudo` on Windows you might need to run as admin.

Setting up an AWS node:

AMI: amzn2-ami-hvm-2.0.20190618-x86_64-gp2 (ami-0d8f6eb4f641ef691)

1. `sudo yum install git gcc python3 python3-dev`
1. `sudo pip3 install web3 requests bottle pyyaml`
1. `mkdir swapper`
1. `cd swapper`

sudo yum install python3-devel
## Design

There are two main portions to this program
1. The registration backend
2. The swapper