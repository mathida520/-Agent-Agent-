const { ethers } = require("hardhat");

async function main() {
  console.log("Deploying HTLCMultiSig...");

  const HTLCMultiSig = await ethers.getContractFactory("HTLCMultiSig");
  const htlc = await HTLCMultiSig.deploy();

  await htlc.waitForDeployment();

  console.log("HTLCMultiSig deployed to:", await htlc.getAddress());
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
