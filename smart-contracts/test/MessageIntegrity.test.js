const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("MessageIntegrity", () => {
  let c;
  const h = ethers.sha256(ethers.toUtf8Bytes("v1|1|2|nonce|cipher"));
  beforeEach(async () => { c = await (await ethers.getContractFactory("MessageIntegrity")).deploy(); });

  it("records and returns a hash with timestamp", async () => {
    await c.recordMessage(42, h);
    const [hash, ts, , exists] = await c.getRecord(42);
    expect(hash).to.equal(h); expect(exists).to.equal(true); expect(ts).to.be.gt(0);
    expect(await c.totalRecords()).to.equal(1);
  });
  it("verifies matching hash and rejects a different one", async () => {
    await c.recordMessage(1, h);
    expect(await c.verifyMessage(1, h)).to.equal(true);
    expect(await c.verifyMessage(1, ethers.sha256("0x00"))).to.equal(false);
  });
  it("is write-once per message id", async () => {
    await c.recordMessage(7, h);
    await expect(c.recordMessage(7, ethers.sha256("0x01"))).to.be.revertedWith("MessageIntegrity: already recorded");
  });
  it("reports unknown ids as not existing and rejects empty hash", async () => {
    expect((await c.getRecord(999))[3]).to.equal(false);
    await expect(c.recordMessage(5, ethers.ZeroHash)).to.be.revertedWith("MessageIntegrity: empty hash");
  });
  it("emits MessageRecorded", async () => {
    await expect(c.recordMessage(9, h)).to.emit(c, "MessageRecorded");
  });
});
