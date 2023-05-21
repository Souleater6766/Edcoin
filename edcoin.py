import hashlib
import datetime
import json
import requests
from uuid import uuid4
from flask import Flask, jsonify, request
from urllib.parse import urlparse


class Transaction:
    def __init__(self, sender, recipient, amount, fee):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.fee = fee

    def set_fee(self, fee):
        self.fee = fee

    def to_dict(self):
        return {
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'fee': self.fee
        }


class Block:
    def __init__(self, transactions, previous_hash):
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.timestamp = str(datetime.datetime.now())
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()


class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.pending_transactions = []
        self.transaction_fee = 0.001  # set transaction fee to 0.001 Edcoins
        self.nodes = set()

    def create_genesis_block(self):
        return Block([], "0")

    def add_block(self, new_block):
        new_block.previous_hash = self.get_latest_block().hash
        new_block.hash = new_block.calculate_hash()
        self.chain.append(new_block)

    def add_transaction(self, transaction):
        transaction.set_fee(self.transaction_fee)  # set transaction fee
        self.pending_transactions.append(transaction)

    def mine_pending_transactions(self, miner_address):
        block = Block(self.pending_transactions, self.get_latest_block().hash)
        block.nonce = self.proof_of_work(block)  # mine block
        self.chain.append(block)
        self.pending_transactions = [
            Transaction(None, miner_address, self.transaction_fee)
        ]  # add miner reward transaction
        self.transaction_fee *= 2  # double transaction fee

    def proof_of_work(self, block):
        while True:
            block.nonce += 1
            block_hash = block.calculate_hash()
            if block_hash[:4] == "0000":
                return block.nonce

    def get_latest_block(self):
        return self.chain[-1]

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            if block.previous_hash != block.calculate_hash():
                return False
            if not self.valid_proof(block):
                return False
            previous_block = block
            current_index += 1
        return True

    def valid_proof(self, block):
        block_hash = block.calculate_hash()
        return block_hash[:4] == "0000"

    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f"http://{node}/get_chain")
            if response.status_code == 200:
                length = response.json()["length"]
                chain = response.json()["chain"]
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
       
        return False

    def get_chain(self):
        return self.chain

    def get_pending_transactions(self):
        return [tx.to_dict() for tx in self.pending_transactions]

    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def validate_transaction(self, transaction):
        # Verify transaction signature using public key
        # Check sender's balance and ensure they have enough funds
        # Validate the transaction fee
        pass

    def validate_chain(self, chain):
        # Verify the integrity and validity of the entire blockchain
        pass


app = Flask(__name__)

# Create a unique node identifier
node_identifier = str(uuid4()).replace("-", "")

# Create an instance of the blockchain
blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.get_latest_block()
    last_proof = last_block.nonce
    proof = blockchain.proof_of_work(last_block)
    blockchain.add_transaction(Transaction(None, node_identifier, 1, blockchain.transaction_fee))
    previous_hash = last_block.hash
    block = Block(blockchain.pending_transactions, previous_hash)
    block.nonce = proof
    blockchain.add_block(block)
    blockchain.pending_transactions = []
    response = {
        'message': "New Block Forged",
        'index': block.index,
        'transactions': [tx.to_dict() for tx in block.transactions],
        'proof': block.nonce,
        'previous_hash': block.previous_hash,
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400
    sender = values['sender']
    recipient = values['recipient']
    amount = values['amount']
    fee = values.get('fee', blockchain.transaction_fee)
    transaction = Transaction(sender, recipient, amount, fee)
    blockchain.add_transaction(transaction)
    response = {'message': f'Transaction will be added to Block {blockchain.get_latest_block().index + 1}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def get_chain():
    response = {
        'chain': [block.__dict__ for block in blockchain.get_chain()],
        'length': len(blockchain.get_chain()),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400
    for node in nodes:
        blockchain.register_node(node)
    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.replace_chain()
    if replaced:
        response = {
            'message': 'Our blockchain was replaced',
            'new_chain': [block.__dict__ for block in blockchain.get_chain()]
        }
    else:
        response = {
            'message': 'Our blockchain is authoritative',
            'chain': [block.__dict__ for block in blockchain.get_chain()]
        }
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    def validate_transaction(self, transaction):
        # Verify transaction signature using public key
        # Check sender's balance and ensure they have enough funds
        # Validate the transaction fee
        pass

    def validate_chain(self, chain):
        # Verify the integrity and validity of the entire blockchain
        pass


app = Flask(__name__)

# Create a unique node identifier
node_identifier = str(uuid4()).replace("-", "")

# Create an instance of the blockchain
blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.get_latest_block()
    last_proof = last_block.nonce
    proof = blockchain.proof_of_work(last_block)
    blockchain.add_transaction(Transaction(None, node_identifier, 1, blockchain.transaction_fee))
    previous_hash = last_block.hash
    block = Block(blockchain.pending_transactions, previous_hash)
    block.nonce = proof
    blockchain.add_block(block)
    blockchain.pending_transactions = []
    response = {
        'message': "New Block Forged",
        'index': block.index,
        'transactions': [tx.to_dict() for tx in block.transactions],
        'proof': block.nonce,
        'previous_hash': block.previous_hash,
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400
    sender = values['sender']
    recipient = values['recipient']
    amount = values['amount']
    fee = values.get('fee', blockchain.transaction_fee)
    transaction = Transaction(sender, recipient, amount, fee)
    blockchain.add_transaction(transaction)
    response = {'message': f'Transaction will be added to Block {blockchain.get_latest_block().index + 1}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def get_chain():
    response = {
        'chain': [block.__dict__ for block in blockchain.get_chain()],
        'length': len(blockchain.get_chain()),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400
    for node in nodes:
        blockchain.register_node(node)
    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.replace_chain()
    if replaced:
        response = {
            'message': 'Our blockchain was replaced',
            'new_chain': [block.__dict__ for block in blockchain.get_chain()]
        }
    else:
        response = {
            'message': 'Our blockchain is authoritative',
            'chain': [block.__dict__ for block in blockchain.get_chain()]
        }
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

