# 椤圭洰瀹屾暣鏂囨。绱㈠紩

> 鏈€鍚庢洿鏂? 2025-11-06
> 椤圭洰: vitegame 鈥?Phaser 3 + React 19 + Electron 妗岄潰娓告垙妗嗘灦
> 鏍稿績鐞嗗康: AI 浼樺厛 + arc42/C4 瑙勮寖 + 涓嶅彲鍥為€€鍩哄骇锛圔ase/Overlay 鍒嗙锛?
> FeatureFlags Quickstart: See [Phase-18-Staged-Release-and-Canary-Strategy.md](migration/Phase-18-Staged-Release-and-Canary-Strategy.md)
> Windows Manual Release: See [WINDOWS_MANUAL_RELEASE.md](release/WINDOWS_MANUAL_RELEASE.md)
---

## ADR Index (Godot Migration)

- [ADR-0018: Godot Runtime and Distribution](adr/ADR-0018-godot-runtime-and-distribution.md)
- [ADR-0019: Godot Security Baseline](adr/ADR-0019-godot-security-baseline.md)
- [ADR-0020: Godot Test Strategy (TDD + GdUnit4)](adr/ADR-0020-godot-test-strategy.md)
- [ADR-0021: C# Domain Layer Architecture](adr/ADR-0021-csharp-domain-layer-architecture.md)
- [ADR-0022: Godot Signal System and Contracts](adr/ADR-0022-godot-signal-system-and-contracts.md)

Addenda
- [ADR-0005 Addendum 鈥?Quality Gates for Godot+C#](adr/addenda/ADR-0005-godot-quality-gates-addendum.md)
- [ADR-0006 Addendum 鈥?Data Storage for Godot](adr/addenda/ADR-0006-godot-data-storage-addendum.md)
- [ADR-0015 Addendum 鈥?Performance Budgets for Godot](adr/addenda/ADR-0015-godot-performance-budgets-addendum.md)

## 0. 椤圭洰鏁翠綋璇存槑

### 鏍稿績鎸囧鏂囨。
- [CLAUDE.md](../CLAUDE.md) 鈥?鍗曚竴鐪熺浉锛圫SoT锛夛紝AI 鍔╂墜宸ヤ綔瑙勫垯
  - AI 浼樺厛寮€鍙戞祦绋嬶紱arc42/C4 鏋舵瀯瑙勮寖
  - Base/Overlay 鏂囨。缁撴瀯
  - 4 娈靛紡濂戠害妯℃澘
  - 璐ㄩ噺闂ㄧ瑕佹眰

### AI 鍔╂墜鍗忎綔瑙勮寖
- [AGENTS.md](../AGENTS.md) 鈥?澶氬姪鎵嬪崗浣滄寚鍗?- [ai-assistants.policies.md](ai-assistants.policies.md) 鈥?AI 鍔╂墜琛屼负鍑嗗垯
- [thinking-modes-guide.md](thinking-modes-guide.md) 鈥?鎬濈淮妯″紡浣跨敤鎸囧崡

### 椤圭洰姒傝
- [README.md](../README.md) 鈥?椤圭洰蹇€熷叆闂?- [README.md](README.md) 鈥?鏂囨。瀵艰埅涓績
- [CONTRIBUTING.md](../CONTRIBUTING.md) 鈥?璐＄尞鎸囧崡

---

## 1. ADR锛堟灦鏋勫喅绛栬褰曪級

璇存槑: 浠?`docs/adr/` 鐩綍鐨勫疄闄呮枃浠朵负鍑嗭紙寤鸿鐢?CI 鑷姩缁熻骞舵洿鏂版鑺傝鏁帮級銆傚綋鍓嶄粨搴撹鏁? 15銆?
### 鍩虹鎶€鏈爤锛圓DR-0001 ~ 0010锛?- [ADR-0001-tech-stack.md](adr/ADR-0001-tech-stack.md) 鈥?鎶€鏈爤閫夊瀷锛圧eact 19 / Electron / Phaser 3 / TS / Vite锛?- [ADR-0002-electron-security.md](adr/ADR-0002-electron-security.md) 鈥?Electron 瀹夊叏鍩虹嚎锛圕SP銆乶odeIntegration=false銆乧ontextIsolation=true锛?- [ADR-0003-observability-release-health.md](adr/ADR-0003-observability-release-health.md) 鈥?鍙娴嬫€т笌鍙戝竷鍋ュ悍锛圫entry 闆嗘垚锛屽穿婧冪巼闃堝€?99.5%锛?- [ADR-0004-event-bus-and-contracts.md](adr/ADR-0004-event-bus-and-contracts.md) 鈥?浜嬩欢鎬荤嚎涓庡绾︼紙CloudEvents 1.0锛? 娈靛紡妯℃澘锛?- [ADR-0005-quality-gates.md](adr/ADR-0005-quality-gates.md) 鈥?璐ㄩ噺闂ㄧ锛堣鐩栫巼銆丒SLint銆佹€ц兘銆丅undle 澶у皬锛?- [ADR-0006-data-storage.md](adr/ADR-0006-data-storage.md) 鈥?鏁版嵁瀛樺偍锛圫QLite锛?- [ADR-0007-ports-adapters.md](adr/ADR-0007-ports-adapters.md) 鈥?绔彛閫傞厤鍣ㄦā寮?- [ADR-0008-deployment-release.md](adr/ADR-0008-deployment-release.md) 鈥?閮ㄧ讲涓庡彂甯?- [ADR-0009-cross-platform.md](adr/ADR-0009-cross-platform.md) 鈥?璺ㄥ钩鍙?- [ADR-0010-internationalization.md](adr/ADR-0010-internationalization.md) 鈥?鍥介檯鍖?
### 骞冲彴涓庤川閲忕害鏉燂紙ADR-0011 ~ 0017锛?- [ADR-0011-windows-only-platform-and-ci.md](adr/ADR-0011-windows-only-platform-and-ci.md) 鈥?Windows 骞冲彴绛栫暐
- [ADR-0012-pr-template-conditional-rendering.md](adr/ADR-0012-pr-template-conditional-rendering.md) 鈥?PR 妯℃澘鍔ㄦ€佹覆鏌?- [ADR-0015-performance-budgets-and-gates.md](adr/ADR-0015-performance-budgets-and-gates.md) 鈥?鎬ц兘棰勭畻涓庨棬绂侊紙P95 闃堝€笺€丅undle 闄愬埗銆侀灞忎紭鍖栵級
- [ADR-0016-api-contracts-openapi.md](adr/ADR-0016-api-contracts-openapi.md) 鈥?API 濂戠害锛圤penAPI锛?- [ADR-0017-quality-intelligence-dashboard-and-governance.md](adr/ADR-0017-quality-intelligence-dashboard-and-governance.md) 鈥?璐ㄩ噺鏅鸿兘鐪嬫澘

### ADR 绠＄悊
- [adr/guide.md](adr/guide.md) 鈥?ADR 缂栧啓鎸囧崡

---

## 2. Base-Clean 鏋舵瀯鏂囨。锛坅rc42 12 绔狅級

鐩綍: `docs/architecture/base/` 鈥?鏃?PRD 鐥曡抗鐨勬竻娲佸熀搴?
鏍稿績绔犺妭:
1. [01-introduction-and-goals-v2.md](architecture/base/01-introduction-and-goals-v2.md) 鈥?椤圭洰鐩爣銆佽川閲忕洰鏍囥€佸埄鐩婄浉鍏虫柟锛堝紩: ADR-0001/0002/0003锛?2. [02-security-baseline-electron-v2.md](architecture/base/02-security-baseline-electron-v2.md) 鈥?Electron 瀹夊叏鍩虹嚎锛堝紩: ADR-0002锛?3. [03-observability-sentry-logging-v2.md](architecture/base/03-observability-sentry-logging-v2.md) 鈥?Sentry銆佺粨鏋勫寲鏃ュ織銆丷elease Health锛堝紩: ADR-0003锛?4. [04-system-context-c4-event-flows-v2.md](architecture/base/04-system-context-c4-event-flows-v2.md) 鈥?C4 涓婁笅鏂囥€佷簨浠舵祦銆丆loudEvents锛堝紩: ADR-0004锛?5. [05-data-models-and-storage-ports-v2.md](architecture/base/05-data-models-and-storage-ports-v2.md) 鈥?鏁版嵁妯″瀷銆丼QLite銆佺鍙ｉ€傞厤锛堝紩: ADR-0006/0007锛?6. [06-runtime-view-loops-state-machines-error-paths-v2.md](architecture/base/06-runtime-view-loops-state-machines-error-paths-v2.md) 鈥?杩愯鏃惰鍥撅紙寰幆/鐘舵€佹満/閿欒璺緞锛?7. [07-dev-build-and-gates-v2.md](architecture/base/07-dev-build-and-gates-v2.md) 鈥?鏋勫缓銆丆I/CD銆佽川閲忛棬绂侊紙寮? ADR-0005锛?8. [08-crosscutting-and-feature-slices.base.md](architecture/base/08-crosscutting-and-feature-slices.base.md) 鈥?浠呮ā鏉匡紙鍔熻兘绾靛垏鍦?overlays锛?9. [09-performance-and-capacity-v2.md](architecture/base/09-performance-and-capacity-v2.md) 鈥?鎬ц兘鍩哄噯銆佸閲忋€佸洖褰掗槇鍊硷紙寮? ADR-0015锛?10. [10-i18n-ops-release-v2.md](architecture/base/10-i18n-ops-release-v2.md) 鈥?鍥介檯鍖栥€佽繍缁淬€佸彂甯冿紙寮? ADR-0008/0010锛?11. [11-risks-and-technical-debt-v2.md](architecture/base/11-risks-and-technical-debt-v2.md) 鈥?椋庨櫓涓庢妧鏈€哄姟
12. [12-glossary-v2.md](architecture/base/12-glossary-v2.md) 鈥?鏈琛?
杈呭姪鏂囨。:
- [architecture-completeness-checklist.md](architecture/base/architecture-completeness-checklist.md)
- [csp-policy-analysis.md](architecture/base/csp-policy-analysis.md)
- [front-matter-standardization-example.md](architecture/base/front-matter-standardization-example.md)
- [00-README.md](architecture/base/00-README.md) 鈥?Base 鏂囨。瀵艰埅

---

## 3. PRD 鈫?Tasks 浜у嚭锛堝彲鎵ц閾捐矾锛?
- 浠诲姟娓呭崟锛圱askmaster锛? `.taskmaster/tasks/tasks.json`
- Overlays 鍔熻兘绾靛垏绱㈠紩: `docs/architecture/overlays/PRD-*/08/_index.md`
- 绾︽潫: 08 绔犲彧鍐欏姛鑳界旱鍒囷紱璺ㄥ垏闈㈣鍒欎粛鍦?Base/ADR锛涘叕鍏辩被鍨嬬粺涓€鏀惧湪 `src/shared/contracts/**`銆?- 鍛藉悕瑙勮寖: Overlay 鐩綍浣跨敤鑻辨枃/ASCII 璺緞锛堢ず渚? `PRD-Guild-Manager/08/`锛夛紝鏂囦欢鍚嶄笌閾炬帴淇濇寔涓€鑷达紝閬垮厤 `-enhanced`銆乣-claude` 杩欑被鍚庣紑瀵艰嚧 404锛涙帹鑽愮粺涓€浣跨敤 `-v2.md` 鐗堟湰鍚庣紑銆?
鏈湴鏍￠獙锛圵indows锛屼娇鐢?Node/Python锛?
- 鍒楀嚭 overlays: `node scripts/build-overlay-map.mjs`
- 浠诲姟-鏂囨。鍙嶉摼鏍￠獙: `node scripts/ci/check-adr-refs.mjs`

---

## 4. 宸ヤ綔娴佹竻鍗曪紙.github/workflows锛?
- 涓?CI/CD: `ci.yml` 鈥?鍚?T2 Gate锛圥layable Smoke锛夈€佽川閲忛棬绂併€佹瀯寤轰笌宸ヤ欢褰掓。
- PR 闂ㄧ: `pr-gatekeeper.yml`銆乣pr-performance-check.yml`銆乣pr-performance-lighthouse.yml`銆乣pr-performance-bundle.yml`銆乣pr-security-audit.yml`銆乣pr-template-conditional-render.yml`銆乣pr-template-validation.yml`銆乣pr-metrics.yml`銆乣pr-ai-code-review.yml`銆乣pr-doc-sync.yml`銆乣pr-fast-chain.yml`
- 鍙戝竷涓庡洖婊? `release.yml`銆乣release-prepare.yml`銆乣release-ramp.yml`銆乣release-emergency-rollback.yml`銆乣release-monitor.yml`銆乣release-health-monitor.yml`
- 瀹夊叏/瑙傛祴: `security-unified.yml`銆乣observability-gate.yml`
- 鍏朵粬绠℃帶: `build-and-test.yml`銆乣ai-code-review.yml`銆乣main-deep-chain.yml`銆乣nightly-quality-rollup.yml`銆乣nightly-scene-transition.yml`銆乣staged-release.yml`銆乣soft-gates.yml`銆乣validate-workflows.yml`銆乣branch-protection-encoding-guard.yml`銆乣config-management.yml`銆乣docs-governance.yml`銆乣fetch-run-logs.yml`銆乣tasks-governance.yml`銆乣taskmaster-pr-link.yml`

璇存槑: 涓婅堪涓哄叧閿伐浣滄祦缂栫洰锛屽叿浣撹Е鍙戞潯浠朵笌浜х墿璇峰弬瑙佸悇 yml 鍐呮敞閲娿€?
---

## 5. 璐ㄩ噺闂ㄧ娓呭崟锛堥槇鍊?鑴氭湰/鏈湴澶嶇幇锛?
- 瑕嗙洊鐜囬棬绂侊紙ADR-0005锛?  - 闃堝€? lines 鈮?90%銆乥ranches 鈮?85%
  - 鏈湴: `npm run test:coverage:gate`
  - 鑴氭湰: `scripts/ci/coverage-gate.cjs`
- 鎬ц兘棰勭畻锛圓DR-0015锛?  - 鎸囨爣: P95锛團CP/鍦烘櫙鍒囨崲锛夈€丅undle 澶у皬闄愬埗
  - 鏈湴: `node scripts/ci/bundle-budget-gate.mjs`銆乣node scripts/ci/compare-playwright-perf.mjs`
- Electron 瀹夊叏鍩虹嚎锛圓DR-0002锛?  - 鍩虹嚎: CSP銆乣nodeIntegration=false`銆乣contextIsolation=true`銆侀鍔犺浇鐧藉悕鍗?  - 鏈湴: `node scripts/comprehensive-security-validation.mjs`
- 濂戠害/鏂囨。涓€鑷存€э紙ADR-0004锛?  - 鏈湴: `node scripts/ci/check-adr-refs.mjs`銆乣node scripts/ci/check-contract-docs.mjs`
- TestID 瑕嗙洊鐜?  - 鏈湴: `node scripts/ci/check-testid-coverage.mjs`

鏃ュ織涓庡伐浠? 缁熶竴鍐欏叆 `logs/YYYY-MM-DD/<妯″潡>/...`锛孋I 浼氫互宸ヤ綔娴佸悕涓庣敤渚嬪悕绉板垎鐩綍褰掓。浠ヤ究鎺掗殰銆?
---

## 6. Implementation 涓?Plans锛堢幇瀛樹笌妯℃澘锛?
### 璇ュ姛鑳界殑澶ц嚧鎻忚堪
鏈妭鐢ㄤ簬灏?PRD/Overlay 鐨勪笟鍔＄洰鏍囪惤鍦颁负鈥滃彲鎵ц鐨勫疄鐜拌鍒掆€濓紝骞朵笌 ADR 涓?arc42 鍩哄骇褰㈡垚闂幆銆傚畠寮鸿皟鈥滆鍒掑彲楠岃瘉銆佸疄鐜板彲鍥炴函銆佸け璐ュ彲鍥炴粴鈥濈殑宸ョ▼鍖栫害鏉燂紝纭繚姣忎竴闃舵锛圫tage锛夐兘鏈夋竻鏅扮洰鏍囥€佹祴璇曚笌闂ㄧ銆?
- 瀹氫綅锛氳繛鎺?PRD 鈫?ADR/arc42 鈫?Implementation Plan 鈫?浠ｇ爜/娴嬭瘯 鐨勬墽琛岄摼璺€?- 浜у嚭锛歚docs/implementation-plans/**`锛堥樁娈垫€ц鍒掞級涓?`docs/implementation/**`锛堝疄鏂借褰?杩佺Щ绗旇锛夈€?- 鍏宠仈锛氭瘡涓樁娈靛簲鍦?Front鈥慚atter 鍙嶉摼 ADR锛堣嚦灏?ADR鈥?004/0005锛屽彲鎸夐渶琛ュ厖 ADR鈥?008/0015锛夛紝骞跺紩鐢?Base 绗?01/02/03 绔犲彛寰勮€屼笉澶嶅埗闃堝€笺€?- 璐ㄩ噺锛氫互 `npm run guard:ci` 涓烘渶灏忛棬绂侊紱瑕嗙洊鐜囥€佸鏉傚害銆侀噸澶嶇巼涓庝緷璧栧仴搴峰潎闇€杩囩嚎锛堣瑙?ADR鈥?005锛夈€?- 鏃ュ織锛氭湰鍦颁笌 CI 鐨勬墽琛屼笌鏋勫缓鏃ュ織缁熶竴钀界洏 `logs/YYYY鈥慚M鈥慏D/implementation/<stage>/`锛屼究浜庡洖婧笌瀹¤銆?- 骞冲彴锛歐indows 浼樺厛锛圓DR鈥?011锛夛紱绀轰緥鑴氭湰涓庡懡浠ら』鎻愪緵 Windows 鍏煎鐢ㄦ硶锛岄伩鍏嶄緷璧栫壒瀹?Shell銆?
蹇€熶娇鐢紙Windows锛岀ず渚嬶級
```python
# 澶嶅埗妯℃澘鐢熸垚涓€涓柊鐨勫疄鏂借鍒掓枃浠讹紙闇€ Python 鈮?.9锛?import os, shutil
src = 'docs/implementation-plans/_TEMPLATE.md'
dst = 'docs/implementation-plans/Phase-10-Sample-Implementation-Plan.md'
os.makedirs(os.path.dirname(dst), exist_ok=True)
shutil.copyfile(src, dst)
print(f'Created: {dst}')
```

娉ㄦ剰浜嬮」
- 08 绔犲姛鑳界旱鍒囦粎鍐欏湪 overlays 涓嬶紱鏈妭鍙储寮?鎻忚堪璁″垝涓庡疄鏂斤紝涓嶈惤鍏ュ叿浣撲笟鍔￠槇鍊笺€?- 鑻ヨ鍒掑紩鍏ユ垨璋冩暣璺ㄥ垏闈㈠彛寰勶紙瀹夊叏/鍙娴嬫€?闂ㄧ/鍙戝竷闃堝€硷級锛岄渶鏂板鎴?Supersede 瀵瑰簲 ADR锛屽苟鍦ㄨ鍒掓枃妗ｄ腑鏄庣‘鏍囨敞銆?- 璁″垝鐘舵€佸繀椤讳繚鎸佹渶鏂帮紙Not Started/In Progress/Complete锛夛紝骞跺湪 PR 鎻忚堪涓榻愰獙鏀舵爣鍑嗕笌 Test鈥慠efs銆?
### 鏈珷瀹氫箟涓庡姛鑳斤紙鍩轰簬鐜板瓨鏂囨。锛?鏈珷姹囬泦鈥滆川閲忎笌鍙樻洿宸ヤ綔娴佲€濈殑瀹炴柦璁″垝涓庡疄鏂借褰曪紝涓嶆壙杞藉叿浣撲笟鍔″姛鑳借璁°€傚叾鑱岃矗鏄互 ADR 涓哄彛寰勶紙涓昏寮曠敤 ADR鈥?002/0003/0005/0015/0011锛夛紝灏?PR 鐢熷懡鍛ㄦ湡涓庡彂甯冨悗鍋ュ悍搴︾殑闂ㄧ涓庤嚜鍔ㄥ寲钀藉湴涓哄彲杩愯鐨?CI/CD 涓庡紑鍙戣€呭伐浣滄祦銆?
- 鑼冨洿锛歅R 妯℃澘涓庡害閲忋€佷换鍔″弽閾俱€丄I 瀹℃煡銆佹€ц兘鍥炲綊銆佷緷璧栧畨鍏ㄣ€佸彂甯冨仴搴枫€侀潤鎬佽川閲忛棬绂併€乀2/T3 闂ㄧ瀹炵幇涓庢枃妗ｅ悓姝ョ瓑銆?- 杈撳嚭鐩綍锛歚docs/implementation-plans/**`锛堥樁娈?绯荤粺鎬ц鍒掍笌鎬荤翰锛変笌 `docs/implementation/**`锛堝氨鍦板疄鏂借褰曪級銆?- 闂ㄧ绛栫暐锛氬奖瀛?杞棬绂侊紙PR 鏈熺粰鍑洪璀︼級涓庣‖闂ㄧ锛坢ain 涓婁弗鏍奸樆鏂級骞惰鎺ㄨ繘锛屾墍鏈夋姤鍛婁笌宸ヤ欢缁熶竴钀界洏 `logs/YYYY-MM-DD/ci/**`銆?- 骞冲彴绾︽潫锛歐indows鈥憃nly 杩愯鐜锛圓DR鈥?011锛夛紝宸ヤ綔娴佷笌鑴氭湰鍧囬渶楠岃瘉 Windows 鍏煎銆?
鎵€鍚ā鍧?宸ヤ綔娴侊紙浠ｈ〃鎬ф枃浠讹級
- PR 璐ㄩ噺绯荤粺鎬荤翰锛歚docs/implementation-plans/PR-Quality-System-Overview.md`锛圥hase 1鈥? 鍏ㄦ櫙锛涢樆濉炵瓥鐣ヤ笌闆嗘垚鐐癸級
- 蹇呴€夋鏌ヤ笌椤哄簭锛歚docs/implementation-plans/required-checks.md`锛坙int/typecheck/unit/e2e/coverage/bundle/release health锛?- 闈欐€佽川閲忛棬绂侊細`docs/implementation-plans/static-quality-gates.md`锛堥噸澶嶅害 鈮?%銆佸湀澶嶆潅搴?CC鈮?0/鍧囧€尖墹5锛涘奖瀛?vs 纭棬锛?- 鍙戝竷鍋ュ悍涓庡洖婊氾細`docs/implementation-plans/Phase-6-Release-Health-and-Auto-Rollback.md`锛圫entry Release Health + GitHub Deployments + 鑷姩鍥炴粴锛?- 鎬ц兘鍥炲綊妫€娴嬶細`docs/implementation-plans/Phase-8-Performance-Regression-Implementation-Plan.md`锛圠ighthouse/Bundle/Playwright锛涢槇鍊煎紩鑷?ADR鈥?015锛?- 渚濊禆瀹夊叏瀹¤锛歚docs/implementation-plans/Phase-9-Dependency-Security-Implementation-Plan.md`锛坣pm audit + license-checker锛汫PL/AGPL 绂佹锛涢樆濉炲悎骞讹級
- AI 瀹℃煡宸ヤ綔娴侊細`docs/implementation-plans/Phase-7.2-AI-Developer-Review-Workflow.md`锛堣鑼冨疄鐜帮紱浜や簰寮忔繁搴﹀鏌ワ級锛沗Phase-7-*.md` 涓哄巻鍙?宸插簾寮冭鏄?- 浠诲姟鍙嶉摼涓?Schema锛歚docs/implementation-plans/taskmaster-pr-backlinking.md`銆乣taskmaster-pr-schema.md`锛圥R 鈫?Task 鍙嶉摼濂戠害锛?- T2/T3 闂ㄧ瀹炵幇锛歚docs/implementation/T2-T3-quality-gates-implementation.md`锛堝彲鐜╁害鍐掔儫涓庘€滃繀椤诲寘鍚祴璇曞彉鏇粹€濓級
- 闆嗘垚鐐归獙璇侊細`docs/implementation-plans/Integration-Points-Verification-Summary.md`锛圥hase 7/8/9 鐨?PR 闆嗘垚涓?shouldBlock 璁＄畻锛?- 鍏跺畠闃舵鎬ф枃妗ｏ細`P0鈥慞2鈥慶onsolidated鈥憄lan.md`銆侀樁娈垫€荤粨涓庡紑鍙戣€呮寚鍗楋紙Phase鈥? Developer Guide/鏉′欢妯℃澘娓叉煋璁″垝绛夛級

涓€鑷存€т笌鐘舵€?- Phase 7 浠モ€?.2 宸ヤ綔娴佲€濅负褰撳墠鍙ｅ緞锛沗Phase-7-AI-Code-Review-Implementation-Plan.md` 鏍囨敞涓哄凡搴熷純锛屼粎渚涘弬鑰冦€?- 鎵€鏈夐槇鍊间笌绛栫暐浠?ADR 涓哄噯锛涘疄鏂借鍒掍笉寰楀鍒堕槇鍊硷紝搴斿紩鐢?ADR鈥?002/0003/0005/0015 鐨勬潯娆剧紪鍙枫€?- 鎶ュ憡涓庡伐浠惰矾寰勫簲涓庤鍒掍竴鑷达紙缁熶竴 `logs/YYYY-MM-DD/ci/<module>/`锛夛紝閬垮厤鍙ｅ緞婕傜Щ銆?
### 瀹炵幇瑙勫垝鏂囨。锛堟ā鏉匡級
- 寤鸿鏂板 `docs/implementation-plans/_TEMPLATE.md`锛屾帹鑽愮粨鏋?
  ```markdown
  ## Stage N: [Name]
  **Goal**: [Specific deliverable]
  **Success Criteria**: [Testable outcomes]
  **Tests**: [Specific test cases]
  **Risks/Mitigations**: [Known risks + rollback]
  **Status**: [Not Started|In Progress|Complete]
  ```

### 鐜板瓨瀹炵幇涓庤鍒掞紙瀹為檯鏂囨。锛?- `docs/implementation/T2-T3-quality-gates-implementation.md`
- `docs/implementation-plans/Phase-8-Performance-Regression-Implementation-Plan.md`
- `docs/implementation-plans/Phase-7-AI-Code-Review-Implementation-Plan.md`
- `docs/implementation-plans/Phase-9-Dependency-Security-Implementation-Plan.md`
- `docs/implementation-plans/Phase-6-Implementation-Summary.md`

### 鍘嗗彶鏂囨。锛堝彧璇诲弬鑰冿級
`docs/architecture/back/` 鈥?鏃╂湡鏋舵瀯鏂囨。锛堝凡琚?Base 鏇夸唬锛夛紝涓嶅缓璁户缁淮鎶ゃ€?
### 瀹炵幇鏂囨。
- [automation-guides.md](automation-guides.md) 鈥?鑷姩鍖栨寚寮?- [VERTICAL_SLICE.md](../VERTICAL_SLICE.md) 鈥?鍨傜洿鍒囩墖寮€鍙戞寚寮?
---

## 7. 鏈」鐩嫭鐗瑰姛鑳戒笌妗嗘灦

### AI 浼樺厛寮€鍙戞鏋?- CLAUDE.md 瑙勫垯寮曟搸: AI 鍔╂墜琛屼负鍑嗗垯涓庡伐浣滄祦
- SuperClaude 妗嗘灦: FLAGS.md / PRINCIPLES.md / RULES.md / MODE_*.md

### Base/Overlay 鏋舵瀯妯″紡
- Base锛堟竻娲佸熀搴э級: 鏃?PRD 鐥曡抗锛屽崰浣嶇 `${DOMAIN_*}`銆乣${PRODUCT_*}`
- Overlay锛堜笟鍔″彔鍔狅級: 鍖呭惈 PRD-ID锛屽叿浣撲笟鍔￠€昏緫
- 08 绔犲垎宸? Base 浠呮ā鏉匡紱Overlay 瀛樺偍鍔熻兘绾靛垏
  
 鏂囨。鐘舵€佹爣璇嗭紙寤鸿锛? `Active`锛堝綋鍓嶅彛寰勶級 / `Design`锛堣璁′腑锛?/ `Template`锛堟ā鏉?鍗犱綅锛夈€傜储寮曞簲鍙皢 `Active` 浣滀负榛樿闃呰鍏ュ彛锛屽叾浣欐爣娉ㄧ姸鎬侀伩鍏嶈鑰呮贩娣嗐€?
### 濂戠害椹卞姩寮€鍙?- 4 娈靛紡濂戠害妯℃澘: 澹版槑 / 绫诲瀷 / 宸ュ巶 / 娴嬭瘯
- CloudEvents 1.0: `app.<entity>.<action>` 鍛藉悕瑙勮寖
- 濂戠害鍚堣鏍￠獙: `node scripts/ci/check-contract-docs.mjs`

### 涓嶅彲鍥為€€鍩哄骇璁捐
- ADR 椹卞姩: 鎵€鏈夋灦鏋勫喅绛栧繀椤诲紩鐢?鈮? 涓?ADR
- 鍙嶅悜閾炬帴楠岃瘉: Task 鈫?ADR/CH 鏍￠獙锛圓jv锛?- Base Clean 妫€鏌? 鑷姩鍖栬剼鏈獙璇佸熀搴ф竻娲佸害

### 澶?AI 鍔╂墜鍗忎綔
- AGENTS.md: 澶氬姪鎵嬪崗浣滆鑼?- Zen MCP: 澶氭ā鍨嬮獙璇?- Taskmaster: PRD 鈫?Task 鑷姩鍖?- Serena MCP: 绗﹀彿绾ч噸鏋勪笌 TDD 缂栬緫

### 璐ㄩ噺鏅鸿兘鐪嬫澘锛圓DR-0017锛?- 鎸囨爣: 瑕嗙洊鐜囥€佸鏉傚害銆侀噸澶嶇巼
- 鑳藉姏: 瓒嬪娍鍒嗘瀽銆侀棬绂佺姸鎬佺粺涓€闈㈡澘

### Windows 骞冲彴浼樺厛锛圓DR-0011锛?- 鍗曞钩鍙扮瓥鐣? 闄嶄綆璺ㄥ钩鍙板鏉傚害
- CI 浼樺寲: Windows 缂撳瓨涓庝紭鍏堢骇
- 鑴氭湰鍏煎: 浼樺厛 Node.js/锛堝彲閫夛級Python锛涢伩鍏嶄緷璧栫壒瀹?Shell

### 娓愯繘鍙戝竷涓庡洖婊氾紙ADR-0008锛?- 鍒嗛樁娈靛彂甯? Canary/Beta/Stable
- 鑷姩鍥炴粴: Release Health 浣庝簬闃堝€艰嚜鍔ㄥ洖婊?- 绱ф€ュ洖婊氬伐浣滄祦: `release-emergency-rollback.yml`

---

## 8. 闄勫姞璧勬簮

### 寮€鍙戝伐鍏烽厤缃?- [ZEN_SETUP_GUIDE.md](../ZEN_SETUP_GUIDE.md) 鈥?Zen MCP 璁剧疆鎸囧崡
- [ZEN_USAGE.md](../ZEN_USAGE.md) 鈥?Zen MCP 浣跨敤璇存槑
- [mcpsetup.md](../mcpsetup.md) 鈥?MCP 鏈嶅姟鍣ㄩ厤缃?
### 娴嬭瘯涓庤皟璇?- [playwright-config-analysis.md](playwright-config-analysis.md) 鈥?Playwright 閰嶇疆鍒嗘瀽
- [e2e-test-failure-root-cause-analysis.md](e2e-test-failure-root-cause-analysis.md) 鈥?E2E 澶辫触鏍瑰洜鍒嗘瀽
- [individual-test-results.md](individual-test-results.md) 鈥?鐙珛娴嬭瘯缁撴灉

### AI 鍔╂墜绱㈠紩锛堣嚜鍔ㄦ洿鏂颁笌鏍￠獙锛?- 鏈湴鑷姩瑙﹀彂锛圚usky锛?  - 姝ｅ父 `git commit` 鏃朵細鎵ц `.husky/pre-commit`锛屽叾涓寘鍚?`node scripts/ci/update-ai-index.mjs --write || true`锛堥潪闃绘柇锛夈€?  - 濡傛湭鐢熸晥锛岃鍏堟墽琛屼竴娆?`npm run prepare` 纭繚 Husky 瀹夎銆?- CI 瑙﹀彂
  - 鎺ㄩ€佸埌 PR 鎴?`main` 鍚庯紝Build & Test 宸ヤ綔娴佷細鍦ㄦ瀯寤洪樁娈垫墽琛?鈥淯pdate AI assistants index (non-blocking)鈥濄€?- 鏃ュ織宸ヤ欢
  - 宸ヤ欢鍚? `docs-encoding-and-ai-index-logs`锛堝寘鍚?`logs/**/ai-index/**`锛夈€?  - 缁撴灉鏂囦欢闅忓伐浣滃尯浜х墿鍙笅杞姐€?- 鏍￠獙鏂瑰紡
  - 鏈湴: `git diff docs/ai-assistants.index.md docs/ai-assistants.state.json`銆?  - CI: 鏌ョ湅宸ヤ欢 `docs-encoding-and-ai-index-logs`锛屾垨鐩存帴鏌ョ湅鏋勫缓浜х墿涓殑涓婅堪鏂囦欢銆?
### 闂鎺掓煡
- [test-failure-analysis.md](test-failure-analysis.md) 鈥?娴嬭瘯澶辫触鍒嗘瀽
- [fix-verification-results.md](fix-verification-results.md) 鈥?淇楠岃瘉缁撴灉

### 缂栫爜涓庢枃鏈竻娲侊紙UTF-8锛?- 妫€鏌?BOM/闈?ASCII: `node scripts/ci/check-bom.mjs`銆乣node scripts/ci/clean-non-ascii.mjs`
- 鎶ュ憡杈撳嚭鐩綍: `logs/YYYY-MM-DD/encoding/`

### 鍙樻洿鏃ュ織涓庡彂甯?- [CHANGELOG.md](../CHANGELOG.md) 鈥?鍙樻洿鏃ュ織
- [RELEASE_NOTES.md](../RELEASE_NOTES.md) 鈥?鍙戝竷璇存槑

### 璐ㄩ噺鎶ュ憡
- [QUALITY_REPORT.md](../QUALITY_REPORT.md) 鈥?璐ㄩ噺鎶ュ憡
- [quality-check-report.md](../quality-check-report.md) 鈥?璐ㄩ噺妫€鏌ユ姤鍛?
---

## 9. 鏂囨。绱㈠紩涓庡鑸?
### 绱㈠紩鏂囦欢
- `architecture_base.index` 鈥?Base 鏂囨。绱㈠紩锛堝鏈敓鎴愶紝鍙敤 `node scripts/rebuild_architecture_index.mjs` 鐢熸垚锛?- `prd_chunks.index` 鈥?PRD 鍒嗙墖绱㈠紩锛堝鏈敓鎴愶紝鍙敤 `node scripts/rebuild_indexes.mjs` 鐢熸垚锛?- `@shards/flattened-prd.xml` 鈥?PRD 鎵佸钩鍖?XML锛堝閮ㄨ緭鍏ワ紝鍕挎墜鏀癸級
- `@shards/flattened-adr.xml` 鈥?ADR 鎵佸钩鍖?XML锛堝閮ㄨ緭鍏ワ紝鍕挎墜鏀癸級

### 瀵艰埅鍏ュ彛
- [README.md](README.md) 鈥?鏂囨。瀵艰埅涓績
- [architecture/base/00-README.md](architecture/base/00-README.md) 鈥?Base 鏂囨。瀵艰埅

### 蹇€熸煡鎵撅紙Windows锛屼娇鐢?Node/Python锛?```bash
# 鍒楀嚭 ADR
node -e "require('fs').readdirSync('docs/adr').filter(f=>f.startsWith('ADR-')).forEach(f=>console.log(f))"

# 鍒楀嚭 Base 鏂囨。
node -e "require('fs').readdirSync('docs/architecture/base').forEach(f=>console.log(f))"

# 鍒楀嚭宸ヤ綔娴?node -e "require('fs').readdirSync('.github/workflows').forEach(f=>console.log(f))"

# 鍒楀嚭 CI 鑴氭湰
node -e "require('fs').readdirSync('scripts/ci').forEach(f=>console.log(f))"
```

---

## 10. 浣跨敤寤鸿

### 鏂版墜鍏ラ棬
1. 闃呰 [CLAUDE.md](../CLAUDE.md) 浜嗚В鏁翠綋妗嗘灦
2. 鏌ョ湅 [README.md](../README.md) 蹇€熷惎鍔ㄩ」鐩?3. 瀛︿範 [ADR-0001](adr/ADR-0001-tech-stack.md)銆乕ADR-0005](adr/ADR-0005-quality-gates.md) 鏍稿績鍐崇瓥

### 鏋舵瀯鐞嗚В
1. 闃呰 [docs/architecture/base/](architecture/base/) 12 绔?arc42 鏂囨。
2. 鐞嗚В Base/Overlay 鍒嗙妯″紡
3. 瀛︿範 [ADR-0004](adr/ADR-0004-event-bus-and-contracts.md) 濂戠害椹卞姩寮€鍙?
### AI 鍗忎綔寮€鍙?1. 閰嶇疆 [AGENTS.md](../AGENTS.md) 瑙勮寖鐨?AI 鍔╂墜
2. 浣跨敤 Taskmaster锛坄.taskmaster/`锛夌鐞嗕换鍔′笌鍙嶉摼
3. 閬靛惊 [CLAUDE.md](../CLAUDE.md) 4 娈靛紡濂戠害妯℃澘

### 璐ㄩ噺淇濋殰
1. 鏈湴杩愯 `npm run guard:ci` 杩涜璐ㄩ噺闂ㄧ妫€鏌?2. 纭繚 ADR 鍙嶅悜閾炬帴: `node scripts/ci/check-adr-refs.mjs`
3. 楠岃瘉 Base 娓呮磥搴? `node scripts/verify_base_clean.mjs`
4. 閾炬帴涓庡懡鍚嶈嚜妫€: 纭绱㈠紩涓殑鏂囦欢鍚嶄笌浠撳簱鐪熷疄鏂囦欢涓€鑷达紙缁熶竴 `-v2.md` 鍚庣紑锛涢伩鍏?`-enhanced`銆乣-claude` 绛夊巻鍙插懡鍚嶏級锛孫verlay 涓?GDD 鏂囨。浣跨敤鑻辨枃/ASCII 璺緞锛岄伩鍏嶄腑鏂囪矾寰勫湪 GitHub 涓婃棤娉曠洿寮€銆?
---

## 鏇存柊鍘嗗彶

- 2025-11-06: 鍒濆鐗堟湰鏁寸悊锛屽幓閲嶅苟娓呯悊鏃у彛寰勶紱淇 ADR 鏁伴噺鍙ｅ緞锛涜ˉ鍏呭伐浣滄祦涓庤川閲忛棬绂佹竻鍗曪紱鐩撮摼 Implementation/Plans锛涚粺涓€ UTF-8 涓枃琛ㄨ堪锛涙柊澧?AI 鍔╂墜绱㈠紩璇存槑

## UI 模板用法（60 秒）

- 运行主场景：`"$env:GODOT_BIN" --path . --scene "res://Game.Godot/Scenes/Main.tscn"`
- 设置面板：音量/语言/图形质量即时生效并持久化；Theme 自动应用样式/字体（存在字体时）
- 新建 Screen：`./scripts/scaffold/new_screen.ps1 -Name MyScreen`，在 Main 中实例化并导航
- 示例 UI：默认关闭，设置 `TEMPLATE_DEMO=1` 后启用示例测试与场景（位于 `Game.Godot/Examples/**`）


## 运行/导出/测试（命令速览）

- 运行主场景：
  - `"$env:GODOT_BIN" --path . --scene "res://Game.Godot/Scenes/Main.tscn"`
- 运行 GdUnit 测试（示例默认关闭）：
  - `./scripts/ci/run_gdunit_tests.ps1 -GodotBin "$env:GODOT_BIN"`
  - 开启示例测试：`$env:TEMPLATE_DEMO=1`
- 导出 Windows EXE：
  - `./scripts/ci/export_windows.ps1 -GodotBin "$env:GODOT_BIN" -Output build\Game.exe`


- Phase 8 场景设计：`docs/migration/Phase-8-Scene-Design.md`（ScreenRoot/Overlays/导航/过渡/模板）

## 冒烟与导出（命令速览）

- Headless Smoke：`./scripts/ci/smoke_headless.ps1 -GodotBin "$env:GODOT_BIN"`
- Export EXE：`./scripts/ci/export_windows.ps1 -GodotBin "$env:GODOT_BIN" -Output build\Game.exe`
- EXE Smoke：`./scripts/ci/smoke_exe.ps1 -ExePath build\Game.exe`

## 可观测性（日志与占位）

- 本地日志目录（Windows）：
  - 安全基线：`%APPDATA%\Godot\app_userdata\<项目名>\logs\security\security-audit.jsonl`
  - HTTP 审计（示例）：`...\logs\security\audit-http.jsonl`
  - 事件占位（SentryClient）：`...\logs\sentry\events-YYYYMMDD.jsonl`
  - 性能指标：`...\logs\perf\perf.json`（控制台含 `[PERF] ... p95_ms=...` 标记）
- 调用示例：
  - `SentryClient.CaptureMessage("info", "user clicked start", {})`
  - `SecurityHttpClient.Validate(method, url, contentType, bodyBytes)` 通过后再发 HTTPRequest

## 3 分钟从 0 到导出 / 3‑Minute From Zero to Export

1) 准备 Godot 二进制（.NET/mono 版）并设置环境：
   - `setx GODOT_BIN C:\Godot\Godot_v4.5.1-stable_mono_win64.exe`
2) 运行最小测试与冒烟（可选示例）：
   - `./scripts/test.ps1 -GodotBin "$env:GODOT_BIN"`（默认不含示例；`-IncludeDemo` 可启用）
   - `./scripts/ci/smoke_headless.ps1 -GodotBin "$env:GODOT_BIN"`
3) 在编辑器安装 Export Templates（Windows Desktop）。
4) 导出与运行 EXE：
   - `./scripts/ci/export_windows.ps1 -GodotBin "$env:GODOT_BIN" -Output build\Game.exe`
   - `./scripts/ci/smoke_exe.ps1 -ExePath build\Game.exe`
