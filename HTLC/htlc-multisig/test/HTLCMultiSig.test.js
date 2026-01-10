const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("HTLCMultiSig", function () {
  let htlc;
  let buyer;
  let seller;
  let arbiter;
  let other;

  const tradeId = ethers.id("trade1");
  const preimage = ethers.id("secret-preimage");
  const hashLock = ethers.sha256(preimage);
  const lockTime = 3600; // 1 hour
  const amount = ethers.parseEther("1.0");

  beforeEach(async function () {
    [buyer, seller, arbiter, other] = await ethers.getSigners();
    const HTLCMultiSigFactory = await ethers.getContractFactory("HTLCMultiSig");
    htlc = await HTLCMultiSigFactory.deploy();
  });

  describe("Locking", function () {
    it("Should lock funds correctly", async function () {
      await htlc.connect(buyer).lock(tradeId, seller.address, arbiter.address, hashLock, lockTime, { value: amount });
      const trade = await htlc.trades(tradeId);
      expect(trade.buyer).to.equal(buyer.address);
      expect(trade.amount).to.equal(amount);
      expect(trade.status).to.equal(1n); // Locked
    });
  });

  describe("Path A: Withdraw with Preimage and Multi-Sig", function () {
    it("Should allow withdrawal with preimage and 2-of-2 (buyer+seller) signatures", async function () {
      await htlc.connect(buyer).lock(tradeId, seller.address, arbiter.address, hashLock, lockTime, { value: amount });

      const messageHash = ethers.solidityPackedKeccak256(["bytes32", "bytes32"], [tradeId, preimage]);
      const sigBuyer = await buyer.signMessage(ethers.toBeArray(messageHash));
      const sigSeller = await seller.signMessage(ethers.toBeArray(messageHash));

      await expect(htlc.withdrawWithPreimage(tradeId, preimage, sigBuyer, sigSeller))
        .to.emit(htlc, "Withdrawn")
        .withArgs(tradeId, seller.address, "Preimage + MultiSig");

      expect(await ethers.provider.getBalance(await htlc.getAddress())).to.equal(0n);
    });
  });

  describe("Path B: Arbitration", function () {
    it("Should allow arbitration with 2-of-3 signatures (buyer+arbiter)", async function () {
      await htlc.connect(buyer).lock(tradeId, seller.address, arbiter.address, hashLock, lockTime, { value: amount });

      const recipient = buyer.address; // Refund to buyer via arbitration
      const messageHash = ethers.solidityPackedKeccak256(["bytes32", "address"], [tradeId, recipient]);
      const sigBuyer = await buyer.signMessage(ethers.toBeArray(messageHash));
      const sigArbiter = await arbiter.signMessage(ethers.toBeArray(messageHash));

      await expect(htlc.resolveDispute(tradeId, recipient, sigBuyer, sigArbiter))
        .to.emit(htlc, "Withdrawn")
        .withArgs(tradeId, recipient, "Arbitration");
    });
  });

  describe("Refund", function () {
    it("Should allow refund after timelock", async function () {
      await htlc.connect(buyer).lock(tradeId, seller.address, arbiter.address, hashLock, lockTime, { value: amount });

      await ethers.provider.send("evm_increaseTime", [lockTime + 1]);
      await ethers.provider.send("evm_mine", []);

      await expect(htlc.refund(tradeId))
        .to.emit(htlc, "Refunded")
        .withArgs(tradeId, buyer.address);
    });
  });
});
