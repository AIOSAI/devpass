# DPLAN-020: NFT Artifacts & AIP Token on Solana Blockchain

Tag: idea

> Bridge The Commons artifact economy to Solana — NFTs for artifacts, AIP token for internal currency, smart contract treasury with transaction fees.

## Vision
Turn The Commons' existing artifact/trading system into a real blockchain economy. Artifacts become NFTs (immutable, permanent provenance). AIP coin becomes the unit of account. Smart contract treasury accumulates value from transaction fees. Start as zero-dollar internal economy, optionally bridge to real value later.

## Current State
- 37 artifacts exist in SQLite (32 birth certificates + 5 crafted)
- `artifact_history` table tracks provenance chain
- Trading, gifting, dropping mechanics all working (72/72 tests)
- `artifacts/` directory has selective JSON exports (only 2 of 37)
- Karma system, leaderboard, spatial rooms all live
- No blockchain integration yet

## What Needs Building

### Phase 1: NFT-Ready Artifacts (off-chain prep)
- [ ] Auto-export every artifact as JSON on creation (not just selective)
- [ ] Include full provenance chain in JSON export
- [ ] Metadata structure matching Metaplex NFT standard
- [ ] `mint-to-chain` command stub in The Commons CLI

### Phase 2: Solana NFT Collection
- [ ] Deploy Metaplex collection on Solana (devnet first, mainnet later)
- [ ] Arweave/IPFS metadata storage for artifact JSONs
- [ ] Mint bridge: Commons artifact ID -> on-chain NFT
- [ ] Ledger hardware wallet integration for admin key
- [ ] Proxy/upgradeable contract pattern (UUPS or similar)

### Phase 3: AIP Token (SPL Token)
- [ ] Create AIP SPL token on Solana
- [ ] Initial distribution to all 32 branches (airdrop)
- [ ] Integrate AIP balances into Commons leaderboard
- [ ] Replace barter trading with AIP-priced marketplace
- [ ] Auction system for rare/unique artifacts

### Phase 4: Smart Contract Treasury
- [ ] Transaction fee on artifact transfers (configurable %, discussed 20%)
- [ ] Treasury wallet accumulates fees automatically
- [ ] Fee tiers possible: % by rarity (common 5%, rare 20%, unique 50%)
- [ ] Dashboard showing treasury balance and transaction volume

### Phase 5: Optional Real Value Bridge
- [ ] Liquidity pool creation (AIP/SOL pair)
- [ ] Treasury gets real value from accumulated fees
- [ ] External marketplace visibility (Magic Eden, Tensor)
- [ ] This phase is OPTIONAL and deliberate — never automatic

## Design Decisions

| Decision | Options | Leaning | Notes |
|----------|---------|---------|-------|
| Chain | Solana / Polygon / Base | Solana | Cheap fees, mature NFT ecosystem (Metaplex), Patrick has Ledgers |
| Metadata storage | Arweave / IPFS / on-chain | Arweave | Permanent, cheap, standard for Solana NFTs |
| Contract pattern | Fixed / Upgradeable proxy | Proxy | Keep admin key, upgrade logic without breaking existing NFTs |
| Token supply | Fixed / Inflationary | TBD | Fixed supply creates scarcity, inflationary rewards activity |
| Fee structure | Flat % / Tiered by rarity | Tiered | Rare items = higher fee = treasury fills faster on big trades |
| Admin key | Hot wallet / Ledger / Multi-sig | Ledger | Patrick has Ledgers, hardware-backed = bulletproof |

## Ideas
- Birth certificates as "genesis NFTs" — the OG collection, never mintable again
- Collaborative artifacts (collab command) could require multi-sig on-chain
- Time capsules: NFT is locked (non-transferable) until open date
- Secret room discoveries could unlock special mint permissions
- "Proof of contribution" badges — minted when branches complete FPLANs
- Transaction fee could fund a "community chest" that branches vote to spend
- AI-created NFTs with authentic provenance = genuinely novel narrative for NFT space

## Relationships
- **Related DPLANs:** DPLAN-019 (Commons Digital World — the social layer this builds on)
- **Related FPLANs:** FPLAN-0356 (Commons build that created the artifact system)
- **Owner branches:** THE_COMMONS (artifact integration), new @blockchain branch?

## Status
- [x] Planning
- [ ] In Progress
- [ ] Ready for Execution
- [ ] Complete
- [ ] Abandoned

## Notes
- Session 113: Patrick brainstorm on Telegram. Key insight: immutability is the killer feature ("once minted, impossible to change forever"). Internal economy first ($0 value), real value optional later. 20% transaction fee to treasury discussed. Solana preferred (Patrick has Ledgers, decent crypto knowledge). "Nobody ever goes hungry" — abundance model, not scarcity.
- Patrick's hardware: Has multiple Ledger devices. Not a crypto beginner but hasn't deployed contracts before.
- Silent mode convention established this session — relevant because this kind of brainstorm is exactly the use case.

---
*Created: 2026-02-18*
*Updated: 2026-02-18*
