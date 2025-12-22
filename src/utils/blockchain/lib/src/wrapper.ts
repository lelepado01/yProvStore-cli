// expects a JSON object on stdin: { method: "method1", params: { ... } }
// writes JSON to stdout: { ok: true, result: ... } or { ok: false, error: { message, stack } }

// load your methods
const methods = {
  readResource: require('./readResource').readResource,
  createResource: require('./createResource').createResource,
  getResourcesByInterval: require('./getAll').getResourcesByInterval
};

function readStdin(): Promise<string> {
  return new Promise((resolve, reject) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', chunk => data += chunk);
    process.stdin.on('end', () => resolve(data));
    process.stdin.on('error', reject);
  });
}

async function main() {
  try {
    const raw = await readStdin();
    const input = raw ? JSON.parse(raw) : {};
    const method = input.method as string | undefined;
    const params = input.params;

    if (!method || !methods[method as keyof typeof methods]) {
      throw new Error('Unknown method: ' + method);
    }

    // call method; allow it to be async
    const result = await methods[method as keyof typeof methods](params);
    process.stdout.write(JSON.stringify({ ok: true, result }));
  } catch (err) {
    const error = err instanceof Error ? err : new Error(String(err));
    process.stdout.write(JSON.stringify({ ok: false, error: { message: error.message, stack: error.stack } }));
    process.exitCode = 1;
  }
}

main();