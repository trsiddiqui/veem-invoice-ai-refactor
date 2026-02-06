import { buildPaymentGraph } from "./graph/graph.js";

async function main() {
  const graph = buildPaymentGraph();

  // POC: run with a simple seed state
  const result = await graph.invoke({
    userMessage: "Pay $50 to Sam for lunch",
  });

  console.log(JSON.stringify(result, null, 2));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
