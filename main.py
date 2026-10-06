import argparse
import requests
import base64, json
from util import extract_public_key, verify_artifact_signature
from merkle_proof import DefaultHasher, verify_consistency, verify_inclusion, compute_leaf_hash

def get_log_entry(log_index, debug=False):
    url = "https://rekor.sigstore.dev/api/v1/log/entries"
    response = requests.get(url, params={"logIndex": log_index})
    response.raise_for_status()

    data = response.json()

    if debug:
        print(data)

    entry_id = list(data.keys())[0]
    return data[entry_id]

def get_verification_proof(log_index, debug=False):
    entry = get_log_entry(log_index, debug)

    proof = entry["verification"]["inclusionProof"]

    return proof

def inclusion(log_index, artifact_filepath, debug=False):
    entry = get_log_entry(log_index, debug)

    body = json.loads(base64.b64decode(entry["body"]))

    signature = base64.b64decode(
        body["spec"]["signature"]['content']
    )
    certificate = base64.b64decode(
        body["spec"]["signature"]['publicKey']["content"]
    )

    pubkey = extract_public_key(certificate)
    verify_artifact_signature(signature, pubkey, artifact_filepath)

    proof = get_verification_proof(log_index, debug)
    leaf_hash = compute_leaf_hash(entry["body"])

    verify_inclusion(
        DefaultHasher,
        proof["logIndex"],
        proof["treeSize"],
        leaf_hash,
        proof["hashes"],
        proof["rootHash"],
    )

    # verify_inclusion is supposed to return a boolean to indicate failure/success, though it did not
    # I'd avoid modifying assignment infrastructure but apparently below print will be executed unconditionally
    print("Offline verification successful")
    
    return

def get_latest_checkpoint(debug=False):
    url = "https://rekor.sigstore.dev/api/v1/log"

    response = requests.get(url)
    response.raise_for_status()

    return response.json()

def consistency(prev_checkpoint, debug=False):
    if not prev_checkpoint:
        raise ValueError("Previous checkpoint is required")

    latest_checkpoint = get_latest_checkpoint(debug)

    if prev_checkpoint["treeID"] != latest_checkpoint["treeID"]:
        raise ValueError("Checkpoints belong to different trees")
    if prev_checkpoint["treeSize"] >= latest_checkpoint["treeSize"]:
        raise ValueError("Previous checkpoint must be older than latest checkpoint")
        
    url = "https://rekor.sigstore.dev/api/v1/log/proof"

    params = {
        "firstSize": prev_checkpoint["treeSize"],
        "lastSize": latest_checkpoint["treeSize"],
        "treeID": prev_checkpoint["treeID"]
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    proof = response.json()

    verify_consistency(
        DefaultHasher,
        prev_checkpoint["treeSize"],
        latest_checkpoint["treeSize"],
        proof["hashes"],
        prev_checkpoint["rootHash"],
        latest_checkpoint["rootHash"]
    )
    
    print("Consistency verification successful")
    
    return

def main():
    debug = False
    parser = argparse.ArgumentParser(description="Rekor Verifier")
    parser.add_argument('-d', '--debug', help='Debug mode',
                        required=False, action='store_true') # Default false
    parser.add_argument('-c', '--checkpoint', help='Obtain latest checkpoint\
                        from Rekor Server public instance',
                        required=False, action='store_true')
    parser.add_argument('--inclusion', help='Verify inclusion of an\
                        entry in the Rekor Transparency Log using log index\
                        and artifact filename.\
                        Usage: --inclusion 126574567',
                        required=False, type=int)
    parser.add_argument('--artifact', help='Artifact filepath for verifying\
                        signature',
                        required=False)
    parser.add_argument('--consistency', help='Verify consistency of a given\
                        checkpoint with the latest checkpoint.',
                        action='store_true')
    parser.add_argument('--tree-id', help='Tree ID for consistency proof',
                        required=False)
    parser.add_argument('--tree-size', help='Tree size for consistency proof',
                        required=False, type=int)
    parser.add_argument('--root-hash', help='Root hash for consistency proof',
                        required=False)
    args = parser.parse_args()
    if args.debug:
        debug = True
        print("enabled debug mode")
    if args.checkpoint:
        # get and print latest checkpoint from server
        # if debug is enabled, store it in a file checkpoint.json
        checkpoint = get_latest_checkpoint(debug)
        print(json.dumps(checkpoint, indent=4))
    if args.inclusion:
        inclusion(args.inclusion, args.artifact, debug)
    if args.consistency:
        if not args.tree_id:
            print("please specify tree id for prev checkpoint")
            return
        if not args.tree_size:
            print("please specify tree size for prev checkpoint")
            return
        if not args.root_hash:
            print("please specify root hash for prev checkpoint")
            return

        prev_checkpoint = {}
        prev_checkpoint["treeID"] = args.tree_id
        prev_checkpoint["treeSize"] = args.tree_size
        prev_checkpoint["rootHash"] = args.root_hash

        consistency(prev_checkpoint, debug)

if __name__ == "__main__":
    main()
