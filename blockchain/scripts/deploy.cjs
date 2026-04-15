const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const Contract = await hre.ethers.getContractFactory("TranscriptRegistry");

  const contract = await Contract.deploy();
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log("Contract deployed to:", address);

  const configPath = path.join(__dirname, "..", "backend", "contract-config.json");
  const config = {
    contract_address: address,
    network: hre.network.name,
    deployed_at: new Date().toISOString()
  };
  
  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  console.log("Contract address saved to:", configPath);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});