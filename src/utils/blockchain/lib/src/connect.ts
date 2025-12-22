/*
 * Copyright IBM Corp. All Rights Reserved.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import * as grpc from '@grpc/grpc-js';
import {  Identity,  Signer, signers } from '@hyperledger/fabric-gateway';
import * as crypto from 'crypto';
import { promises as fs } from 'fs';
/*import * as path from 'path';

const msp_id = 'Org1MSP';
let basepath=__dirname;
basepath="/home/nicola/hlf-events/node-app/src"
// Path to crypto materials.
const crypto_path1 = path.resolve(
    basepath, 
    '..', 
    '..', 
    'network', 
    'organizations', 
    'peerOrganizations', 
    'org1.testbed.local'
);
const crypto_path2 = path.resolve(
    basepath, 
    '..', 
    '..', 
    'network', 
    'organizations', 
    'peerOrganizations', 
    'org2.testbed.local'
);

// Path to user private key directory.
const key_path = path.resolve(
    crypto_path1, 
    'users', 
    'User1@org1.testbed.local', 
    'msp', 
    'keystore',
    'priv_sk'
);

// Path to user certificate.
const cert_path = path.resolve(
    crypto_path1, 
    'users', 
    'User1@org1.testbed.local', 
    'msp', 
    'signcerts',
    'User1@org1.testbed.local-cert.pem'
);

// Path to peer tls certificate.
const tls_cert_path = path.resolve(
    crypto_path2, 
    'peers', 
    'peer0.org2.testbed.local', 
    'tls', 
    'ca.crt'
);

// Gateway peer endpoint and hostname.
const peer_endpoint = 'localhost:8051';
const peer_hostname = 'peer0.org2.testbed.local';
*/

const tls_cert_path=process.env.CONNECTOR_PEER_TLSCERT_PATH
const key_path=process.env.CONNECTOR_USR_PKEY_PATH
const peer_endpoint=process.env.CONNECTOR_PEER_ENDPOINT
const peer_hostname=process.env.CONNECTOR_PEER_HOSTNAME || peer_endpoint
const cert_path=process.env.CONNECTOR_USR_CERT_PATH
const msp_id= process.env.CONNECTOR_PEER_MSP_ID


export async function newGrpcConnection(): Promise<grpc.Client> {
    if (!tls_cert_path || !peer_endpoint) {
        console.error("Missing required arguments. Set CONNECTOR_PEER_TLSCERT_PATH and CONNECTOR_PEER_ENDPOINT");
        process.exit(1);
    }
    const tls_root_cert = await fs.readFile(tls_cert_path);
    const tls_credentials = grpc.credentials.createSsl(tls_root_cert);
    return new grpc.Client(peer_endpoint, tls_credentials, {
        'grpc.ssl_target_name_override': peer_hostname,
    });
}

export async function newIdentity(): Promise<Identity> {
    if (!cert_path || !msp_id) {
        console.error("Missing required arguments. Set CONNECTOR_USR_CERT_PATH and CONNECTOR_MSP_ID");
        process.exit(1);
    }
    const credentials = await fs.readFile(cert_path);
    return { 
        mspId: msp_id, 
        credentials: credentials 
    };
}

export async function newSigner(): Promise<Signer> {
    if (!key_path) {
        console.error("Missing required arguments. Set CONNECTOR_USR_PKEY_PATH");
        process.exit(1);
    }
    const pkey_pem = await fs.readFile(key_path);
    const pkey = crypto.createPrivateKey(pkey_pem);
    return signers.newPrivateKeySigner(pkey);
}

