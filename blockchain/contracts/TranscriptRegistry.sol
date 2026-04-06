// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TranscriptRegistry {

    struct Transcript {
        string documentHash;
        address issuer;
        uint256 timestamp;
    }

    mapping(string => Transcript) public transcripts;

    function issueTranscript(string memory hash) public {
        require(transcripts[hash].timestamp == 0, "Transcript already issued");
        transcripts[hash] = Transcript(
            hash,
            msg.sender,
            block.timestamp
        );
    }

    function verifyTranscript(string memory hash)
        public
        view
        returns (bool)
    {
        return transcripts[hash].timestamp != 0;
    }
}