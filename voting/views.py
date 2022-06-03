from cgitb import html
import os, json
from django.http import FileResponse
from django.shortcuts import render, HttpResponse, redirect
from django.views.decorators.csrf import csrf_exempt
from solcx import compile_standard, install_solc
from web3 import Web3
from EVM.settings import BASE_DIR


def test(request):
    return HttpResponse("Hello World")

with open(os.path.join(BASE_DIR, "contracts/election.sol"), "r") as file:
            election_sol = file.read()
@csrf_exempt
def candidate_registration(request):
    if request.method == "GET":
            return render(request, "CandidateRegistration.html")
    else:
        candidates = request.POST['candidates']
        private_key = request.POST['private_key']
        address = request.POST['account_address']
        candidates_lst = candidates.split(",")
        # installing compiler
        install_solc("0.7.0")

            # compiling
        compiled_sol = compile_standard(
                        {
                "language": "Solidity",
                 "sources": {"election.sol": {"content": election_sol}},
                "settings": {
                "outputSelection": {
                 "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}

                        }
                    },
                },
        solc_version="0.8.0",
        )

        with open(os.path.join(BASE_DIR, "build/compiled_sol.json") , "w") as file:
            json.dump(compiled_sol, file)
        # return HttpResponse(compiled_sol["contracts"]["election.sol"])
        byte_code = compiled_sol["contracts"]["election.sol"]["Ballot"]["evm"]["bytecode"]["object"]

            # get abi
        abi = compiled_sol["contracts"]["election.sol"]["Ballot"]["abi"]

            # connecting with ganache
        w3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545"))
        chain_id = 1337
            # Creating Contract
        election = w3.eth.contract(abi=abi, bytecode=byte_code)

            # Get Nonce or Latest Count of transactions
        nonce = w3.eth.getTransactionCount(address)

            # 1: Build the transaction
            # 2: Sign a transaction
            # 3: Send a transaction

        transaction = election.constructor(candidates_lst).buildTransaction(
                {
                "chainId": chain_id,
                "from": address,
                "nonce": nonce,
                "gasPrice": w3.eth.gas_price,
                }
            )

        signed_transaction = w3.eth.account.sign_transaction(transaction, private_key)
            # Send Transaction
        tx_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

            # working with contract
        election = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)
        proposals = election.functions.getProposals().call()
        return render(request, "ElectionDetails.html", context={
            "contractAddress":tx_receipt.contractAddress,
            "Proposals":proposals
            }
        )

@csrf_exempt
def authorize_voter(request):
    if request.method == "GET":
        return render(request, "auth.html")
    else:
        contract_address = request.POST['contract_address']
        voter_account_address = request.POST['voter_address']
        admin_private_key = request.POST['private_key']
        admin_address = request.POST['account_address']

        w3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545"))
        chain_id = 1337
        file = open(os.path.join(BASE_DIR, "build/compiled_sol.json") , "r")
        compiled_sol = json.loads(file.read())
        abi = compiled_sol["contracts"]["election.sol"]["Ballot"]["abi"]            
        election = w3.eth.contract(address=contract_address, abi=abi)

        transaction = election.functions.giveRightToVote(voter_account_address).buildTransaction(
            {
                "gasPrice": w3.eth.gas_price, 
                "from":admin_address,
                "chainId": chain_id,
                "nonce": w3.eth.get_transaction_count(account=admin_address)
            }
        )

        signed_transaction = w3.eth.account.sign_transaction(transaction, admin_private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

        return render(request, "auth.html" ,context={'auth':True} )

@csrf_exempt
def go_to_election(request):
    if request.method == "GET":
        return render(request, "election.html")
    elif request.method=="POST":
        contract_address = request.POST['contract_address']
        w3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545"))
        chain_id = 1337
        file = open(os.path.join(BASE_DIR, "build/compiled_sol.json") , "r")
        compiled_sol = json.loads(file.read())
        abi = compiled_sol["contracts"]["election.sol"]["Ballot"]["abi"]            
        election = w3.eth.contract(address=contract_address, abi=abi)

        proposals = election.functions.getProposals().call()
        return render(request, "CastVote.html", context={ "proposals":proposals ,"range":range(len(proposals)), "address":contract_address})


@csrf_exempt
def cast_vote(request):
    if request.method == "GET":
        return render(request, "CastVote.html")
    else:
        contract_address = request.POST["address"]
        candidate = request.POST["candidate"]
        voter_account_address = request.POST["voter_address"]
        voter_private_key = request.POST["voter_private_key"]

        w3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545"))
        chain_id = 1337
        file = open(os.path.join(BASE_DIR, "build/compiled_sol.json") , "r")
        compiled_sol = json.loads(file.read())
        abi = compiled_sol["contracts"]["election.sol"]["Ballot"]["abi"]            
        election = w3.eth.contract(address=contract_address, abi=abi)
        candidate = int(candidate)
        transaction = election.functions.vote(candidate).buildTransaction(
            {
                "gasPrice": w3.eth.gas_price, 
                "from":voter_account_address,
                "chainId": chain_id,
                "nonce": w3.eth.get_transaction_count(account=voter_account_address)
            }
        )

        signed_transaction = w3.eth.account.sign_transaction(transaction, voter_private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

        file = open(os.path.join(BASE_DIR, "receipts/receipt.txt") , "w")
        file.write(str(tx_receipt))
        file.close()
        file = open(os.path.join(BASE_DIR, "receipts/receipt.txt") , "rb")
        return FileResponse(file)


@csrf_exempt
def result(request):
    if request.method == "GET":
        return render(request, "election1.html")
    else:
        contract_address = request.POST['contract_address']
        w3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545"))
        chain_id = 1337
        file = open(os.path.join(BASE_DIR, "build/compiled_sol.json") , "r")
        compiled_sol = json.loads(file.read())
        abi = compiled_sol["contracts"]["election.sol"]["Ballot"]["abi"]            
        election = w3.eth.contract(address=contract_address, abi=abi)

        proposals = election.functions.getProposals().call()
        winner = election.functions.winnerName().call()
        print(winner)
        return render(request, "result.html", context={
            "proposals":proposals,
            "winner":winner,
            "contract":contract_address
            }
        )
        


  
       
    






