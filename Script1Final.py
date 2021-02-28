from bitcoinutils.setup import setup
from bitcoinutils.keys import P2shAddress, PublicKey
from bitcoinutils.script import Script
from bitcoinutils.proxy import NodeProxy

def main():
    
#Connect to the regtest
    setup('regtest')
    proxy = NodeProxy('user','bitcoin').get_proxy()

#Accept a Public Key from User and derive a P2PKH address from it
    pk = PublicKey.from_hex(input('Please input your Public Key\n'))
    pk_p2pkh_addr = pk.get_address()

#Accept future absolute block amount from User
    current_blocks = proxy.getblockcount()
    absolute_blocks = int(input(f'\nPlease input the future block height. The current block height is: {current_blocks}\n'))

#Set the timelock sequence and create a redeemScript accordingly
    
    redeem_script = Script([absolute_blocks,
    'OP_CHECKLOCKTIMEVERIFY', 'OP_DROP', 
    'OP_DUP', 'OP_HASH160',pk_p2pkh_addr.to_hash160(), 
    'OP_EQUALVERIFY', 'OP_CHECKSIG'])

#Generate a P2SH Address from the redeemScript and show it
    p2sh_addr = P2shAddress.from_script(redeem_script)
    print(f'\nThe P2SH Address is:\n{p2sh_addr.to_string()} Now, go on and send some funds to it.\n')

if __name__ == "__main__":
    main()
