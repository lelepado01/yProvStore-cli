// createResource.ts
import { getContract } from './gatewayHelper';
import { TextDecoder } from 'util';

const utf8Decoder = new TextDecoder();

export async function createResource(params: { pid: string, url: string, hash: string, timestamp: string, owners: string[] }) {
    const { pid, url, hash, timestamp, owners } = params;

    if (!pid || !url || !hash || !timestamp || !owners) {
        throw new Error('Missing required parameters');
    }

    const { contract, gateway, client } = await getContract();
    
    try {
        const result = await contract.submitAsync('CreateResource', {
            arguments: [
                pid,
                url,
                hash,
                timestamp,
                JSON.stringify(owners),
            ],
        });

        const status = await result.getStatus();
        if (!status.successful) {
            throw new Error(`Transaction ${status.transactionId} failed with status code ${status.code}`);
        }

        const resource = utf8Decoder.decode(result.getResult());
        return resource;
    } finally {
        gateway.close();
        client.close();
    }
}

// Only run main() when file is executed directly (not imported)
if (require.main === module) {
    async function main() {
        const pid = process.argv[2];
        const url = process.argv[3];
        const hash = process.argv[4];
        const timestamp = process.argv[5];
        if (!pid || !url || !hash || !timestamp || !process.argv[6]) {
            console.error("Missing required arguments.");
            process.exit(1);
        }
        const owners = JSON.parse(process.argv[6]); // Expect JSON stringified list
        
        try {
            const resource = await createResource({ pid, url, hash, timestamp, owners });
            console.log(JSON.stringify({ success: true, resource: resource }));
        } catch (err: any) {
            console.error(JSON.stringify({ success: false,error: err.message }));
            process.exit(1);
        }
    }

    main();
}
