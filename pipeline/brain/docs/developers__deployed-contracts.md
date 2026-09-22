> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Configured Testnet Contracts

> Public addresses configured in the reviewed Stellar frontend.

These values come from `mercury-stellar-backend/lib/stellar-utils.ts` in the local source reviewed on **2026-09-12**. They are not a live deployment verification. Runtime Registry configuration and deployed WASM may differ after upgrades or testnet resets.

| Setting            | Value                                 |
| ------------------ | ------------------------------------- |
| Network passphrase | `Test SDF Network ; September 2015`   |
| Soroban RPC        | `https://soroban-testnet.stellar.org` |
| Horizon            | `https://horizon-testnet.stellar.org` |

## Addresses and pool index

`USDC_TOKEN`, `BLEND_USDC`, and `BLEND_USDC_TOKEN` refer to Blend USDC. They do not alias Aquarius or Soroswap USDC. `VUSDC_TOKEN` and `LENDING_PROTOCOL_USDC` are compatibility aliases for the Blend market.

| Frontend constant                | Configured value                                                   |
| -------------------------------- | ------------------------------------------------------------------ |
| `REGISTRY`                       | `CBBQQULN3XZDWDZG7D6VYD4UQKBGYH22DOFQEISKENCMZTYUPQ5LDXUO`         |
| `ORACLE`                         | `CAYHPE4U54GDKULPRHYJZNDMBAJDQ3UNQ446KFYMJ5HABBPORERZCRWB`         |
| `RATE_MODEL`                     | `CBMJ7DD4EUVZWFRPKRPGYK2NADCIGY5OFTPN7PJ7SAOIJI7IQTVHOJT6`         |
| `RISK_ENGINE`                    | `CCSCBA4WSUMVGA4CWC7QKBZXXEL4TO2YCCFPGHX5SJCYKHQLQUKAVUAY`         |
| `ACCOUNT_MANAGER`                | `CAZLR6EHZXQNZJIFNP6F7SIJQC3P64MKHHQNZSSG5BNAEFCYTTGTDZXB`         |
| `TRACKING_TOKEN`                 | `CC4P2DC4J3DTKNL7CQB42S3JSZNIVVHFJEMHZWTSDR233CT6O2KK7ZK2`         |
| `CONTROLLER_FACADE`              | `CB2SEZGDRPS4O56UYQAERQGHM7V6ZDMZZE5AYOGERRGWT5CUGRPVDWEH`         |
| `POOL_DEPLOYER`                  | `CCURFEEXKVGDAKXAGNG4NHEK2RRSOBOVUZDNHI32DFBAF2HWO57JKLIP`         |
| `BLEND_CONTROLLER`               | `CCZVHCPWY47GRWCE2TB7QPX7Y54BMQUYQTTAQ5LJGNJ3GLGO77VVQUS3`         |
| `SOROSWAP_CONTROLLER`            | `CBSUSG7PK2QKYBEA2GPNNTV7QVGKV7DSDUFDB44FFRZYR4L4GB7BKD2M`         |
| `AQUARIUS_CONTROLLER`            | `CBVRH2DWBMASALAMPZ5JUCKZHWO6SA2MD4MBXMO644XNCERWBMKHL2WT`         |
| `VXLM_TOKEN`                     | `CDGYZSMWOOKM55WEKEQ2HEMM7RS2KRA7MYI2DDYXWV5YHGUVUGQZSOCB`         |
| `VBLEND_USDC_TOKEN`              | `CAZWBJQ6V2XASUILI36UVQJ5K2EQXIDVXJZNGZBEONPUVVURKDOP4RX5`         |
| `VAQUARIUS_USDC_TOKEN`           | `CAU5GVAGCWLOIAGFHQFEVBJLDHVS2KH4YPRQ34CIDG2T7RDAWWWODKRV`         |
| `VSOROSWAP_USDC_TOKEN`           | `CAIMEE4EZ3FUMOBTVV7DKGI2TDACWXUWU6Z2RJ3NMP642TDKQHHOEIWG`         |
| `VUSDC_TOKEN`                    | `CAZWBJQ6V2XASUILI36UVQJ5K2EQXIDVXJZNGZBEONPUVVURKDOP4RX5`         |
| `LENDING_PROTOCOL_XLM`           | `CB3LCPDMPRTRXJHO7ZB3OORQDL2AV5FTJPPZOPHTZFOMUPMJY55RHYR3`         |
| `LENDING_PROTOCOL_BLEND_USDC`    | `CCHSDWJPFMEFNDRSZ55A5MLSTASYHZERLPJIJGTAD7MT24KHVLOU3BTI`         |
| `LENDING_PROTOCOL_AQUARIUS_USDC` | `CDKMMD63RUZNROFZZD64QZNEQ2FR5X62R4FE6E3USJ5VN5KY7QM6F2FD`         |
| `LENDING_PROTOCOL_SOROSWAP_USDC` | `CCZQUQQVZVNZMTG2P6MVAGA7V2DRTCII6IGVEQ5YUCYP7MXA7SMLHETP`         |
| `LENDING_PROTOCOL_USDC`          | `CCHSDWJPFMEFNDRSZ55A5MLSTASYHZERLPJIJGTAD7MT24KHVLOU3BTI`         |
| `BLEND_USDC_TOKEN`               | `CAQCFVLOBK5GIULPNZRGATJJMIZL5BSP7X5YJVMGCPTUEPFM4AVSRCJU`         |
| `AQUARIUS_USDC_TOKEN`            | `CAZRY5GSFBFXD7H6GAFBA5YGYQTDXU4QKWKMYFWBAZFUCURN3WKX6LF5`         |
| `SOROSWAP_USDC_TOKEN`            | `CB3TLW74NBIOT3BUWOZ3TUM6RFDF6A4GVIRUQRQZABG5KPOUL4JJOV2F`         |
| `USDC_TOKEN`                     | `CAQCFVLOBK5GIULPNZRGATJJMIZL5BSP7X5YJVMGCPTUEPFM4AVSRCJU`         |
| `BLEND_POOL`                     | `CCEBVDYM32YNYCVNRXQKDFFPISJJCV557CDZEIRBEE4NCV4KHPQ44HGF`         |
| `BLEND_XLM`                      | `CDLZFC3SYJYDZT7K67VZ75HPJVIEUVNIXF47ZG2FB2RMQQVU2HHGCYSC`         |
| `BLEND_USDC`                     | `CAQCFVLOBK5GIULPNZRGATJJMIZL5BSP7X5YJVMGCPTUEPFM4AVSRCJU`         |
| `AQUARIUS_ROUTER`                | `CBCFTQSPDBAIZ6R6PJQKSQWKNKWH2QIV3I4J72SHWBIK3ADRRAM5A6GD`         |
| `AQUARIUS_XLM_USDC_POOL`         | `CD3LFMMLBQ6RBJUD3Z2LFDFE6544WDRMWHEZYPI5YDVESYRSO2TT32BX`         |
| `AQUARIUS_USDC`                  | `CAZRY5GSFBFXD7H6GAFBA5YGYQTDXU4QKWKMYFWBAZFUCURN3WKX6LF5`         |
| `AQUARIUS_POOL_INDEX_HEX`        | `9ac7a9cde23ac2ada11105eeaa42e43c2ea8332ca0aa8f41f58d7160274d718e` |
| `AQUARIUS_XLM_USDT_POOL`         | `CA6DAGOMK5D7GKBNWVCIEAYSTPJXLQUFWFKSZOMNEM6BVOTUBDCTIT5I`         |
| `SOROSWAP_ROUTER`                | `CCJUD55AG6W5HAI5LRVNKAE5WDP5XGZBUDS5WNTIVDU7O264UZZE7BRD`         |
| `SOROSWAP_XLM`                   | `CDLZFC3SYJYDZT7K67VZ75HPJVIEUVNIXF47ZG2FB2RMQQVU2HHGCYSC`         |
| `SOROSWAP_USDC`                  | `CB3TLW74NBIOT3BUWOZ3TUM6RFDF6A4GVIRUQRQZABG5KPOUL4JJOV2F`         |
| `SOROSWAP_XLM_USDC_POOL`         | `CDVAIOYHCD4RUSLQNVFI7RIZBFT2JZMJWM4RTOLQZQXL4QAVXU5RFKDB`         |

## Verify a deployment

Read Registry's protocol configuration, asset metadata, controller mappings, and tracking metadata. Check pool underlying/receipt metadata, origination fees, pause flags, rate coefficients, and AccountManager's live execution gate. Compare deployed contract code before assuming it matches the Rust tree. A SmartAccount address is per trader; discover it through the application rather than reusing another user's address.

## Source reference

* `mercury-stellar-backend/lib/stellar-utils.ts`
* `Protocol_V1_Soroban_testnet/deploy/deploy.sh`
* `Protocol_V1_Soroban_testnet/deploy/verify.sh`
