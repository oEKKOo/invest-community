# backend 冗余清理手动删除清单（资源与数据层）

> 目标：聚焦资源与数据层的冗余（缓存、日志、测试产物、本地导出）。  
> 适用范围：`background/`。  
> 说明：本清单仅给出“手动删除建议”，不直接删文件。

## 一、本轮扫描结论（重点）

- 发现大量 Python 运行缓存：`155` 个 `*.pyc`，`28` 个 `__pycache__/` 目录。
- 发现开发日志：`background/django.log`（约 `5.57MB`）。
- 未发现长期保留的 SQL 导出文件（`*.sql`）。
- 未发现本地数据库文件（`*.sqlite` / `*.sqlite3` / `*.db`）。
- 未发现 `background/media/`、`background/uploads/` 等上传目录落库数据。
- 未发现股票/基金原始导入文件（`csv/xlsx/parquet/pkl`）进入 `background/`。

## 二、可手动删除（高置信）

| 路径 | 类型 | 删除理由 | 影响评估 | 回滚建议 |
| --- | --- | --- | --- | --- |
| `background/**/__pycache__/` | Python 缓存 | 解释器自动生成，非源码 | 无运行影响 | 再次运行服务会自动生成 |
| `background/**/*.pyc` | Python 缓存 | 编译产物，不应入库 | 无运行影响 | 再次运行服务会自动生成 |
| `background/django.log` | 运行日志 | 开发日志持续膨胀，影响仓库体积 | 无代码影响 | 运行后会自动再生成 |
| `background/staticfiles/`（若存在） | collectstatic 产物 | 可由部署流程再生成 | 部署前需重新生成 | 执行 `python manage.py collectstatic` |
| `background/media/` 中测试上传文件（若后续出现） | 测试资源 | 对生产代码无必要 | 仅影响被删测试文件访问 | 删除前打包备份 |

## 三、建议确认后删除（中置信）

| 路径 | 类型 | 删除理由 | 风险 | 建议 |
| --- | --- | --- | --- | --- |
| `background/accounts/seed_realistic.py` | 大体量种子脚本 | 偏开发演示用途，非生产运行必要 | 可能影响演示初始化 | 若保留“最小必要样本”，可迁移到 `scripts/archive/` 后再删 |
| `background/accounts/management/commands/seed_realistic.py` | 管理命令种子脚本 | 与上项功能重叠，长期维护成本高 | 可能影响快速造数 | 合并为一个最小样本命令后删除冗余版本 |

## 四、你关心项的专项结论

| 检查项 | 结果 | 建议 |
| --- | --- | --- |
| 股票/基金原始导入文件 | 本轮未发现入仓 | 后续统一放 `data-archive/`（仓库外） |
| 测试图片/附件/报告文件 | 本轮未发现上传目录落库 | 明确 `media/`、`uploads/` 永久忽略 |
| 本地 K 线缓存文件 | 本轮未发现文件缓存 | 继续使用 DB/Redis，不落本地文件 |
| 数据库导出 SQL | 本轮未发现 | 导出放到仓库外备份目录 |
| 演示假数据 JSON | 未发现独立 JSON 假数据包 | 保留“最小必要样本”，其余迁移归档 |

## 五、手动删除顺序建议

1. 先删缓存和日志：`__pycache__/`、`*.pyc`、`django.log`。
2. 再处理运行产物：`staticfiles/`、`media/` 测试文件（如有）。
3. 最后评估种子脚本，按“最小必要样本”策略归档/精简。

## 六、删除后最小验证

1. `python manage.py check`
2. `python manage.py migrate --check`
3. 冒烟核心接口：登录、帖子流、行情、组合、通知、管理员审核
4. 部署前执行 `python manage.py collectstatic`

