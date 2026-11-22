// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title MessageIntegrity
/// @notice Append-only registry of SHA-256 hashes of ENCRYPTED message payloads.
///         It never receives plaintext or key material - only a 32-byte hash and an opaque message id.
contract MessageIntegrity {
    struct Record {
        bytes32 payloadHash;
        uint256 timestamp;   // block timestamp at recording time
        address recorder;
        bool exists;
    }

    mapping(uint256 => Record) private records;
    uint256 public totalRecords;

    event MessageRecorded(uint256 indexed messageId, bytes32 payloadHash, uint256 timestamp, address indexed recorder);

    /// @notice Record the hash for a message id. Each id can be written exactly once (immutability).
    function recordMessage(uint256 messageId, bytes32 payloadHash) external {
        require(!records[messageId].exists, "MessageIntegrity: already recorded");
        require(payloadHash != bytes32(0), "MessageIntegrity: empty hash");
        records[messageId] = Record(payloadHash, block.timestamp, msg.sender, true);
        totalRecords += 1;
        emit MessageRecorded(messageId, payloadHash, block.timestamp, msg.sender);
    }

    function getRecord(uint256 messageId)
        external view returns (bytes32 payloadHash, uint256 timestamp, address recorder, bool exists)
    {
        Record storage r = records[messageId];
        return (r.payloadHash, r.timestamp, r.recorder, r.exists);
    }

    /// @notice True only if the id was recorded AND the supplied hash equals the recorded one.
    function verifyMessage(uint256 messageId, bytes32 payloadHash) external view returns (bool) {
        Record storage r = records[messageId];
        return r.exists && r.payloadHash == payloadHash;
    }
}
