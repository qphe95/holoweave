# Comparison with existing systems

Oct 18, 2026

Every layer of Holoweave exists somewhere, but no production system makes quietly removing one file require most of the network. In existing systems, a single node, provider, gateway or company can usually drop a specific file without anyone else noticing.

## At a glance

| System | Term and payment | Redundancy and placement | What storage nodes see | Private reads | Status |
| --- | --- | --- | --- | --- | --- |
| **Holoweave** | Prepaid fixed term (default 10 years), escrowed per epoch | Outer code plus Clay code (32 of 96); every stripe on its own random holders; 6x | Encrypted, lightly mixed blocks; no identifiable chunk of any file | Yes: fast plain reads by default, PIR over domains when needed | Design |
| [Arweave](https://docs.arweave.org/developers/mining/overview/blacklist) | One-time payment into an endowment, intended as permanent | Replication across miners | Plain data unless the uploader encrypts | No | Production |
| [Filecoin](https://fil.org/blog/announcing-watermelon-nv21-upgrade-extended-sector-commitments-synthetic-porep-fvm-enhancements-and-more) | Fixed-term deals, up to 3.5 years, renewable | Sealed replicas with providers the client chooses | Plain data unless the client encrypts | No | Production |
| [Walrus](https://docs.wal.app/docs/walrus-client/storing-blobs) | Prepaid epochs, up to 2 years | 2D erasure coding (RedStuff), about 4.5x | Public by default; blobs are deletable by their owner unless marked permanent | No | Production |
| [Storj](https://storj.dev/learn) | Ongoing billing through satellites | Erasure coding, for example any 29 of 80 pieces on distinct nodes | Encrypted pieces (on by default) | No | Production |
| Sia | Renewable renter-host contracts | Erasure coding across hosts the renter chooses | Encrypted pieces | No | Production |
| IPFS with pinning | No guarantee; persists while someone pins it | As many copies as are pinned | Plain data | No | Production |
| Freenet (Hyphanet) | Free; unpopular content fades away | Popularity-driven caching | Encrypted blocks | Anonymous routing, not PIR | Production |

## Censorship: what removing one file takes

| System | Who can quietly drop one specific file | How many parties must act | Does anyone notice? |
| --- | --- | --- | --- |
| **Holoweave** | Nobody below the threshold; nodes can't tell which file they store, and on the private path not which file is read | About 55% to 65% of all stake, acting together (a probability bound, not an incentive) | Yes: every refusal becomes a public on-chain challenge, and private-path refusals take down whole domains |
| Arweave | Each miner, through its own content policy (blocklists); gateways can filter too | One miner or gateway at a time; content stays on miners that don't block it | Rarely: per-node policies are quiet by design |
| Filecoin | The few providers holding a deal can stop serving it | The handful of providers the client picked | Only the client, when retrieval fails |
| Walrus | The owner can delete a deletable blob; nodes can see which public blob is requested | A large share of the epoch's committee to block a permanent blob | Not by design: nodes know exactly which blob they refuse |
| Storj | The satellite operator, which controls metadata and accounts | One company | No |
| Sia | The hosts a renter picked can refuse or drop data | A few hosts | Only the renter |
| IPFS with pinning | Gateways (denylists) and pinning services | One provider | No |
| Freenet | Nobody targets content directly, but unrequested content fades | None needed | No |

The pattern: existing systems either let a single party target one file (Arweave miners, gateways, satellites, chosen providers) or let nodes see which file is requested (Walrus, Filecoin, IPFS). Holoweave's distinctive combination is random per-stripe placement across the whole network, content-blind storage, PIR on the private path, and a public refusal log.

## Entanglement-based systems

Holoweave's closest ancestors are not the crypto storage networks above but the censorship-resistant publishing systems that entangled documents so deleting one would damage others. They showed entanglement alone is not enough: with sparse entanglement and public identifiers, a censor can still remove one document cheaply.

| System | How files are entangled | What removing one file costs the censor | Persistence and incentives | Private retrieval | Status |
| --- | --- | --- | --- | --- | --- |
| **Holoweave** | Light XOR mixing (each piece uses 2 randomizer blocks), inside a 32-of-96 code with random holders per stripe | Capturing about 55% to 65% of all stake; on the private path, refusing whole PIR domains | Prepaid fixed term, escrow, audits, immediate repair | Yes (PIR domains) | Design |
| [Tangler (Waldman and Mazières, 2001)](https://www.cs.virginia.edu/~evans/cs588/waldman01tangler.pdf) | Each 16 KB block is combined with 2 random existing blocks by Shamir secret sharing; any 3 of 4 server blocks rebuild it | Deleting the publisher-generated blocks can kill a file with little collateral damage | About 10 to 30 volunteer servers, storage credits, blocks expire unless reinjected (about 7% a day) | No | Research prototype |
| [Dagster (Stubblefield and Wallach, 2001)](https://corpus.lantern.io/papers/2001-stubblefield-dagster/) | Each new block is XORed with 10 older blocks, forming a dependency graph | Deleting a block breaks every later block that links to it, an unknown number of documents | Single server; no payment, so open to filler flooding | No | Research design |
| OFF System (2006) | File blocks XORed with randomizer blocks that are reused across many files, so no stored block belongs to one file | Each block serves several files, but a file's blocks are identifiable from its descriptor | Volunteer nodes, no incentives | No | Unmaintained |
| [Recast (Burihabwa, 2020)](https://libra.unine.ch/bitstreams/2bb81a6f-f37b-4954-8603-b0fb3be971b8/download) | STeP-archival random entanglement plus erasure coding; temporary replicas until a new document is entangled | Tampering with one document disturbs many others and is detected at read time | No economics; stores forever | No | Research prototype |
| Alpha entanglement codes (Estrada-Galiñanes and Felber) | XOR-based entanglement chains across blocks | Designed for durability and cheap repair rather than censorship | Archival storage research | No | Research |

**What the research found.** Aspnes et al. ([Towards a Theory of Data Entanglement](https://www.cs.yale.edu/publications/techreports/tr1277.pdf)) proved that a server running its own decoder can always drop one document while serving the rest, so entanglement can't give all-or-nothing integrity by itself. Perng et al. ([Censorship Resistance Revisited, 2005](https://corpus.lantern.io/findings/2005-perng-censorship__deniability-entanglement-susceptibility-one/)) showed Tangler and Dagster are fully susceptible under cooperative servers: their entanglement graphs are too sparse to make censorship costly, and with public identifiers the protection has to come from hiding the mapping from request to document, at PIR strength.

**How Holoweave answers that.** It follows those conclusions directly: it does not rely on entanglement for resistance. Availability comes from random per-stripe placement, which forces a censor to capture most of the network; non-selectivity comes from PIR on the private path, which hides which record a request is for; and refusals leave public evidence. Mixing is kept light, for deniability only, because heavier mixing (like Dagster's 10 links) gives a censor more blocks to target.

## Where Holoweave is weaker

- **Storage overhead:** 6x, against about 4.5x for Walrus and about 2.8x for Storj's 29-of-80 example.
- **Not built:** every other system here runs in production; Holoweave's guarantees are on paper and its performance figures are estimates.
- **Term:** fixed terms (default 10 years) rather than Arweave's intended permanence; renewal means re-uploading.
- **Private reads are slower:** under a second on CPU hot domains, minutes for cold data, about 100 ms only on optional GPU servers.
- **Complexity:** blind ingest, sealing, PIR, commit-reveal audits and challenges add moving parts the simpler systems don't have.
- **Content policy:** operators can't filter what they store, which is the point but carries legal exposure that Arweave's per-node policies avoid.

**Sources**

- [Arweave content policies for miners](https://docs.arweave.org/developers/mining/overview/blacklist)
- [Filecoin Watermelon upgrade: 3.5-year sector commitments](https://fil.org/blog/announcing-watermelon-nv21-upgrade-extended-sector-commitments-synthetic-porep-fvm-enhancements-and-more)
- [Walrus docs: storing blobs (lifetime, public by default, deletable blobs)](https://docs.wal.app/docs/walrus-client/storing-blobs)
- [Walrus paper: RedStuff, about 4.5x replication factor](https://arxiv.org/html/2505.05370v2)
- [Storj product overview: erasure coding, encryption, satellites](https://storj.dev/learn)

Sia, IPFS, Freenet, OFF System and alpha entanglement code entries are from general knowledge and should be checked before this page is shared.
