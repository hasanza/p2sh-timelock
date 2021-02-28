from bitcoinutils.setup import setup
from bitcoinutils.utils import to_satoshis
from bitcoinutils.transactions import Transaction, TxInput, TxOutput, Sequence, Locktime
from bitcoinutils.keys import P2pkhAddress, P2shAddress, PrivateKey
from bitcoinutils.script import Script
from bitcoinutils.proxy import NodeProxy
from bitcoinutils.constants import TYPE_ABSOLUTE_TIMELOCK
from decimal import Decimal

def main():

#Connect to the regtest network
    setup('regtest')
    proxy = NodeProxy('user', 'bitcoin').get_proxy()

#Accept absolute future block amount User
    current_blocks = proxy.getblockcount()
    absolute_blocks = int(input(f'\nPlease input the future block height. The current block height is: {current_blocks}.\nIt must match the one in the redeem script from which the P2SH address (with the locked funds) was derived\n'))

#Accept the Private Key from User
    sk = PrivateKey(input('\nPlease enter your Private Key (used to create the address from which the P2SH Address was derived)\n'))

#Accept the P2SH Address with the funds
    p2sh_addr = input('\nPlease enter the P2SH address which has the locked funds\n')
    
#Import the address into the wallet
    proxy.importaddress(f'{p2sh_addr}')
    print(f'\nThe P2SH address {p2sh_addr} has been imported into the wallet.\n')

#Get all UTXOs for this address
    all_utxos = proxy.listunspent(1, 9999999, [f'{p2sh_addr}'])
    print(f'\nAll the UTXO Objects for this address are:\n{all_utxos}\n')

#Calculate total funds available. Aggregate all UTXO amounts.
    def totalFunds():
        total = Decimal(0)
        for utxo in all_utxos:
            total += Decimal(utxo["amount"])
        return total

    total_funds = totalFunds()
    print("Total funds available: ", total_funds)    

#Instantiate the timelock sequence
    seq = Sequence(TYPE_ABSOLUTE_TIMELOCK, absolute_blocks)

#Create an array of inputs from these UTXOs
    def getInputs():
        inputs = []
        count = 0
        for utxo in all_utxos:
            #create inputs and append them into an array
            #First, create an input
            utxo = all_utxos[count]
            txin = TxInput(utxo["txid"], utxo["vout"], sequence=seq.for_input_sequence())
            #then, append it to the array
            inputs.append(txin)
            ++count
        return inputs
    
    inputs = getInputs()
    
    print(f'The inputs created from these outputs are:\n {inputs}') 

#Use User's Secret Key (Accepted above) to recreate the Public Key
    pk = sk.get_public_key()

#We recreate the P2PKH Addr to recreate the other half of the redeemScript
    p2pkh_addr = pk.get_address()

#We recreate the redeem script
    redeem_script = Script([absolute_blocks,
    'OP_CHECKLOCKTIMEVERIFY', 'OP_DROP',
    'OP_DUP', 'OP_HASH160', p2pkh_addr.to_hash160(),
    'OP_EQUALVERIFY', 'OP_CHECKSIG'])

#Confirm that the P2SH address is the same one to which funds were sent by receating the P2SH from this redeem script
    addr = P2shAddress.from_script(redeem_script).to_string()
    print(f'\nCheck if this is the address with the locked funds:\n{addr} vs what you input above {p2sh_addr}')

#Accept the receiving P2PKH from User
    destination_addr = P2pkhAddress(input('\nPlease enter the address you want to send the locked funds to:\n'))  

#Calculate txn size to estimate fee from inputs only so we subtract it from funds
    tx_test = Transaction(inputs, [], Locktime(absolute_blocks).for_transaction())
    tx_size = tx_test.get_size() 
    # 0.0001 is an appropriate fee per byte so we use that
    est_tx_fee = tx_size / 1000 * 0.0001


#Create a txout transferring total locked funds (minus estimated fees).
    txout = TxOutput(to_satoshis(total_funds - Decimal(est_tx_fee)), destination_addr.to_script_pub_key())


#Create Txn. Passing in the inputs, output, and the future absolute lock time
    tx = Transaction(inputs, [txout], Locktime(absolute_blocks).for_transaction())

#Print the newly created txn
    print(f'\nThe raw unsigned txn is: {tx.serialize()}\n')

#Calulate the Appropriate Transaction Fee According to Txn Size. 
#First, get the fee estimate from network. Useful only for mainnet and testnet.
    def getFee():
        fee = proxy.estimatesmartfee(5,"ECONOMICAL")
        if fee["errors"]:
            print('Network data not enough to calculate fee. Setting default fee: 0.0001 BTC')
            return 0.0001
        else:
            return fee["feerate"]

#Then, calculate the size of our Txn and then multiply it by the per-byte fee
    est_fee = getFee() #per byte
    tx_size = tx.get_size()
    print(f'\nThe transaction size is:\n{tx_size} bytes')
    tx_fee = tx_size / 1000 * est_fee
    print(f'\nThe recommended fee for this transaction is:\n{tx_fee}')

#Need to sign all inputs
    def signInputs():
        input_index = 0
        for input in inputs:
            #Use the Secret Key corresponding to the P2SH to create the signature for the txn/ sign all inputs
            #Redeem script is passed to replace the scriptSig
            inputSig = sk.sign_input(tx, input_index, redeem_script)
            input.script_sig = Script([inputSig, pk.to_hex(), redeem_script.to_hex()])
            ++input_index
    signInputs()

    signed_tx = tx.serialize()

#Print the signed raw txn, ready to be checked for validity
    print(f"\nRaw signed transaction:\n{signed_tx}")
    print(f"\nTransaction ready to be broadcast. Transaction Id: {tx.get_txid()}")

#Test for validity
    isValid = proxy.testmempoolaccept([f'{signed_tx}'])
    print(f'\nTransaction validity check result:\n{isValid}')
    
#Broadcast txn
    #needs signed_tx
    if isValid[0]["allowed"]:
        if input('\nSend transaction to network? Y / N: ') == 'Y':
            sent_tx_id = proxy.sendrawtransaction(f'{signed_tx}')
            print(f'\n***The transaction with id {sent_tx_id} has been sent to the network***')
        else:
            print(f'\nUser decided not to send the funds and exited the program.')
            exit()
    else:
        reason = isValid[0]["reject-reason"]
        print(f'\nThe signed raw transaction is invalid. Reason: {reason}') 


if __name__ == "__main__":
    main()





