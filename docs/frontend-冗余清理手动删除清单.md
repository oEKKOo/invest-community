# 前端冗余清理手动删除清单

## 1. 文档目的

本清单用于指导 `frontend` 的冗余文件手动删除。  
本次策略：**助手不直接删除文件**，仅提供可验证的候选项、删除顺序与回归步骤。

## 2. 扫描范围与方法

- 扫描范围：`d:/invest/frontend/src`
- 判定依据：
  - 路由映射检查：`router/index.ts` 与 `views/` 对照
  - 全局引用检查：`import` / 动态 `import()` / 组件标签关键字检索
  - 联动依赖检查：候选文件之间的互相引用关系

## 3. 手动删除候选清单

| 序号 | 文件路径 | 引用证据 | 风险等级 | 建议 |
|---|---|---|---|---|
| 1 | `d:/invest/frontend/src/components/market/QuoteMini.vue` | 全局无 `QuoteMini` 引用，仅文件自身存在 | 低 | 手动删除 |
| 2 | `d:/invest/frontend/src/components/market/AssetChip.vue` | 全局无上游引用，仅内部依赖 `QuoteTag.vue` | 中 | 手动删除（需联动） |
| 3 | `d:/invest/frontend/src/components/market/QuoteTag.vue` | 仅被 `AssetChip.vue` 引用 | 中 | 随 `AssetChip.vue` 联动删除 |

## 4. 建议删除顺序（手动）

1. 删除 `QuoteMini.vue`
2. 删除 `AssetChip.vue`
3. 删除 `QuoteTag.vue`

## 5. 每步删除后的验证命令

在 `d:/invest/frontend` 目录依次执行：

```bash
npm run build
```

如需额外校验可执行：

```bash
npm run lint
```

## 6. 关键页面回归建议

- 登录页：`/login`
- 首页：`/`
- 行情列表：`/market`
- 个股详情：`/assets/:assetId`
- 社区页：`/community`
- 个人页：`/profile`

## 7. 回滚方式

若某一步删除后验证失败，使用 git 恢复该文件并重新验证：

```bash
git restore --source=HEAD -- "frontend/src/components/market/<文件名>"
```

> 说明：建议一删一验，避免多文件同时删除导致定位困难。

## 8. 第二轮扫描补充结论

- 本轮对 `views/`、`components/`、`api/` 再次做引用扫描后，未发现新的高置信“文件级孤儿模块”。
- 继续保留当前候选删除清单（第 3 节），不新增文件级删除项。
- 本轮主要落地为代码块级瘦身（路由跳转修复、抽屉重复逻辑收敛、字体加载收敛、构建分包微调）。
