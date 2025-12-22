// gatewayHelper.ts
import * as grpc from '@grpc/grpc-js';
import { connect, Contract, Gateway, hash } from '@hyperledger/fabric-gateway';
import { newGrpcConnection, newIdentity, newSigner } from './connect';

const channel_name = 'mychannel';
const chaincode_name = 'cc-test';

export async function getContract(): Promise<{ contract: Contract; gateway: Gateway; client: grpc.Client }> {
    const client = await newGrpcConnection();
    const gateway = await connect({
        client,
        identity: await newIdentity(),
        signer: await newSigner(),
        hash: hash.sha256,
        evaluateOptions: () => ({ deadline: Date.now() + 5000 }),
        endorseOptions: () => ({ deadline: Date.now() + 15000 }),
        submitOptions: () => ({ deadline: Date.now() + 5000 }),
        commitStatusOptions: () => ({ deadline: Date.now() + 60000 }),
    });

    const network = gateway.getNetwork(channel_name);
    const contract = network.getContract(chaincode_name);
    return { contract, gateway, client };
}
