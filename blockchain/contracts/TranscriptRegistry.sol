// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TranscriptRegistry {

    event TranscriptIssued(string indexed hash, address indexed issuer, uint256 timestamp);

    struct Transcript {
        string documentHash;
        address issuer;
        uint256 timestamp;
    }

    mapping(string => Transcript) public transcripts;
    string[] private _allHashes;

    function issueTranscript(string memory hash) public {
        require(transcripts[hash].timestamp == 0, "Transcript already issued");
        transcripts[hash] = Transcript(
            hash,
            msg.sender,
            block.timestamp
        );
        _allHashes.push(hash);
        emit TranscriptIssued(hash, msg.sender, block.timestamp);
    }

    function verifyTranscript(string memory hash)
        public
        view
        returns (bool)
    {
        return transcripts[hash].timestamp != 0;
    }

    function getTotalCount() public view returns (uint256) {
        return _allHashes.length;
    }

    function getHashes(uint256 offset, uint256 limit) public view returns (string[] memory) {
        uint256 total = _allHashes.length;
        if (offset >= total) {
            return new string[](0);
        }
        uint256 end = offset + limit;
        if (end > total) {
            end = total;
        }
        uint256 count = end - offset;
        string[] memory result = new string[](count);
        for (uint256 i = 0; i < count; i++) {
            result[i] = _allHashes[offset + i];
        }
        return result;
    }
}