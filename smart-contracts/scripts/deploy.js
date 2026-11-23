// Deploys MessageIntegrity and writes deployments/localhost.json (address + ABI) for the FastAPI backend / Web3.py.
const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const factory = await hre.ethers.getContractFactory("MessageIntegrity");
  const contract = await factory.deploy();
  await contract.waitForDeployment();
  const address = await contract.getAddress();
  const artifact = await hre.artifacts.readArtifact("MessageIntegrity");
  const out = path.join(__dirname, "..", "deployments", `${hre.network.name}.json`);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, JSON.stringify({
    contract: "MessageIntegrity", address, abi: artifact.abi,
    network: hre.network.name, chainId: Number((await hre.ethers.provider.getNetwork()).chainId),
    deployedAt: new Date().toISOString(),
  }, null, 2));
  console.log("MessageIntegrity deployed to", address);
  console.log("Deployment info written to", out);
}

main().catch((e) => { console.error(e); process.exitCode = 1; });

