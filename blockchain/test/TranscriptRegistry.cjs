const { loadFixture } = require("@nomicfoundation/hardhat-toolbox/network-helpers");
const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("TranscriptRegistry", function () {
  async function deployContract() {
    const Contract = await ethers.getContractFactory("TranscriptRegistry");
    const contract = await Contract.deploy();
    return contract;
  }

  describe("issueTranscript", function () {
    it("should store a transcript hash with issuer and timestamp", async function () {
      const contract = await loadFixture(deployContract);
      const testHash = "a".repeat(64);

      await contract.issueTranscript(testHash);

      const transcript = await contract.transcripts(testHash);
      expect(transcript.documentHash).to.equal(testHash);
      expect(transcript.issuer).to.not.equal(ethers.ZeroAddress);
      expect(transcript.timestamp).to.be.greaterThan(0);
    });

    it("should revert when issuing a duplicate transcript hash", async function () {
      const contract = await loadFixture(deployContract);
      const testHash = "b".repeat(64);

      await contract.issueTranscript(testHash);

      await expect(contract.issueTranscript(testHash))
        .to.be.revertedWith("Transcript already issued");
    });

    it("should allow different hashes to be issued by different issuers", async function () {
      const contract = await loadFixture(deployContract);
      const hash1 = "c".repeat(64);
      const hash2 = "d".repeat(64);

      const [issuer1, issuer2] = await ethers.getSigners();

      await contract.connect(issuer1).issueTranscript(hash1);
      await contract.connect(issuer2).issueTranscript(hash2);

      const transcript1 = await contract.transcripts(hash1);
      const transcript2 = await contract.transcripts(hash2);

      expect(transcript1.issuer).to.equal(issuer1.address);
      expect(transcript2.issuer).to.equal(issuer2.address);
    });
  });

  describe("verifyTranscript", function () {
    it("should return true for an issued transcript", async function () {
      const contract = await loadFixture(deployContract);
      const testHash = "e".repeat(64);

      await contract.issueTranscript(testHash);

      const result = await contract.verifyTranscript(testHash);
      expect(result).to.be.true;
    });

    it("should return false for a non-issued transcript", async function () {
      const contract = await loadFixture(deployContract);
      const testHash = "f".repeat(64);

      const result = await contract.verifyTranscript(testHash);
      expect(result).to.be.false;
    });
  });
});
