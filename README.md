# p2sh-timelock
A python script that locks funds in a P2SH address for some time and the allows user to send those funds. The redeem script creation is done manually via OP_CODES.

**Usage**

N.B 

*No extra library other than python-bitcoin-utils has been used for this project.
*This program was created according to a regtest environment
*Python virtual environment was not used to create this project (setup issues)
*Python version 3.9.1 was used to create this project
*!Since the script is not multithreaded, sometimes a query call to the local regtest via teh proxy may fail. In such a situation,
  please re-run the script.


PROCESS:

In order to run the program, the following steps are to be taken.

0. Ensure that the regtest daemon is running and your bitcoin.conf looks like this:

    regtest=1
    rpcuser=user
    rpcpassword=bitcoin  (If you decide to keep your own username + pass, ensure that you change then in both scripts as well )
    rpcPort = 18445
    fallbackfee=0.001
    acceptnonstdtxn=1

1. Create a new wallet (public key + private key)
2. Mine atleast 101 blocks (bitcoin-cli -regtest -generate 101) so your block rewards are spendable
3. Run Script 1 and follow the onscreen instructions.
    
    #SCRIPT-1

4. Be sure to set the future blocks atleast 1 block ahead because when you send funds to the P2SH Address (bitcoin-cli -regtest sendtoaddress <address> <BTC>), you
   have to generate atleast 1 block (bitcoin-cli -regtest -generate 1) so the transaction funding it is mined and it actually has UTXOs to spend.
5. Be sure to import the P2SH address to the wallet (bitcoin-cli -regtest importaddress <p2sh_address>)

    #SCRIPT-2

6. After running script 1 and following the above and the onscreen instructions, run script 2.
7. Follow the onscreen instructions
8. When you are prompted to enter an address to send the funds to, this address is a legacy P2PKH address.
   You can generate it using (bitcoin-cli -regtest getnewaddress "" legacy)
9. You will notice that we do not use any change address. The consequnce of this is that all remaining BTC (if we transfer an amount less than total - estimated fee),
   is sent to miners as fee. This results in very high fee being sent to miners and the mempoolaccept check for our txn will fail due reason: "max_fee_exceeded".
   This is why we need to transfer almost all funds and leave only appropriate fee's worth.


