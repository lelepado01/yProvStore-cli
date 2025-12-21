// readResource.ts
import { getContract } from './gatewayHelper';
import { TextDecoder } from 'util';

const utf8Decoder = new TextDecoder();

export async function readResource(params: { pid: string }) {
    const { pid } = params;

    if (!pid) {
        throw new Error('Missing PID parameter');
    }

    const { contract, gateway, client } = await getContract();

    try {
        const result = await contract.submitAsync('ReadResource', { arguments: [pid] });
        const status = await result.getStatus();
        if (!status.successful) {
            throw new Error(`Transaction ${status.transactionId} failed with status code ${status.code}`);
        }

        const resource = utf8Decoder.decode(result.getResult());
        return JSON.parse(resource);
    } finally {
        gateway.close();
        client.close();
    }
}

// Only run main() when file is executed directly (not imported)
if (require.main === module) {
    async function main() {
        const pid = process.argv[2];

        if (!pid) {
            console.error(JSON.stringify({ success: false, error: 'Missing PID argument' }));
            process.exit(1);
        }

        try {
            const resource = await readResource({ pid });
            console.log(JSON.stringify({ success: true, resource }));
        } catch (err: any) {
            console.error(JSON.stringify({ success: false, error: err.message }));
            process.exit(1);
        }
    }

    main();
}
