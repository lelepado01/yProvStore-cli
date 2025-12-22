// createResource.ts
import { getContract } from './gatewayHelper';
import { TextDecoder } from 'util';

const utf8Decoder = new TextDecoder();

export async function getResourcesByInterval(params: { startTime: string, endTime: string }) {
    const { startTime, endTime } = params;

    if (!startTime || !endTime) {
        throw new Error('Missing required parameters');
    }

    const { contract, gateway, client } = await getContract();
    
    try {
        const result = await contract.submitAsync('GetResourcesByTimestamp', {
            arguments: [
                startTime,
                endTime
            ]
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
        const startTime = process.argv[2];
        const endTime = process.argv[3];
        if (!startTime || !endTime) {
            console.error("Missing required arguments.");
            process.exit(1);
        }
        
        try {
            const resource = await getResourcesByInterval({ startTime, endTime });
            console.log(JSON.stringify({ success: true, resource: resource }));
        } catch (err: any) {
            console.error(JSON.stringify({ success: false, error: err.message }));
            process.exit(1);
        }
    }

    main();
}
