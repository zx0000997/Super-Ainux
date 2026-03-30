# M0 部署与验收指南（相对仓库实现）

本文对应规格书 **M0**：基线主机、单节点编排、密钥与配置分仓。实现代码位于仓库 [`m0/`](../m0/) 目录。

## 前置条件

- 一台 **x86_64** 虚拟机或迷你主机，建议 **Debian 12**（bookworm）最小化安装。
- 可 `sudo` 的管理员账户。
- 仓库已克隆到本机（用于首次安装时 `rsync` 到 `/opt/super-ainux/m0`）。

## 一、从空 VM 到基线 + 编排就绪

1. 安装 Debian 12，启用 OpenSSH，完成安全更新。
2. （可选）使用 [`m0/baseline/cloud-init.yaml`](../m0/baseline/cloud-init.yaml) 在云厂商上初始化。
3. 克隆本仓库并进入部署脚本目录：

   ```bash
   git clone https://github.com/zx0000997/Super-Ainux.git
   cd Super-Ainux/m0/deploy
   sudo bash install.sh
   ```

4. `install.sh` 将：
   - 按 [`m0/baseline/packages-debian12.txt`](../m0/baseline/packages-debian12.txt) 安装依赖（含 Podman、Python3、`python3-jsonschema`、`nftables` 等）；
   - 把 `m0/` 同步到 `/opt/super-ainux/m0`；
   - 构建并启动 Compose 中的 **m0-health**（仅 `/health` 占位服务）；
   - 注册 `sas-m0-compose.service`（开机自启）。

5. 在本机验证健康检查（默认仅监听 **127.0.0.1:18080**）：

   ```bash
   curl -sf http://127.0.0.1:18080/health
   # 期望输出: ok
   ```

## 二、防火墙与健康检查（验收项 2）

1. **应用 nftables 模板**（默认放行 **22/tcp** 与回环/已建立连接，其余入站丢弃）：

   ```bash
   sudo /opt/super-ainux/m0/firewall/apply-firewall.sh
   ```

2. **注意**：在仅 SSH 的会话中应用防火墙前，请确认 22 端口规则无误，避免被锁在外面。

3. 再次执行 `curl -sf http://127.0.0.1:18080/health`（经 `127.0.0.1` 不受 WAN 入站规则影响）。

## 三、假密钥全链路注入（验收项 3、4）

1. 准备**非机密**运行时配置（可复制示例后编辑）：

   ```bash
   sudo install -d -m 0750 /etc/super-ainux
   sudo cp /opt/super-ainux/m0/config/sas-runtime.example.json /etc/super-ainux/sas-runtime.json
   sudo nano /etc/super-ainux/sas-runtime.json
   ```

   保持 `operator.provider_id` 与 `supervisor.provider_id` **不相同**（异源双脑约束）。

2. 从示例生成**两个独立**密钥文件（**假密钥**即可），权限 `600`：

   ```bash
   sudo cp /opt/super-ainux/m0/secrets/operator.env.example /etc/super-ainux/operator.env
   sudo cp /opt/super-ainux/m0/secrets/supervisor.env.example /etc/super-ainux/supervisor.env
   sudo sed -i 's/replace-with-fake-or-real-key/fake-operator-key-demo/g' /etc/super-ainux/operator.env
   sudo sed -i 's/replace-with-fake-or-real-key/fake-supervisor-key-demo/g' /etc/super-ainux/supervisor.env
   sudo chmod 600 /etc/super-ainux/operator.env /etc/super-ainux/supervisor.env
   ```

3. 运行校验脚本（不打印密钥内容）：

   ```bash
   python3 /opt/super-ainux/m0/config/validate_config.py \
     --runtime /etc/super-ainux/sas-runtime.json \
     --operator-env /etc/super-ainux/operator.env \
     --supervisor-env /etc/super-ainux/supervisor.env
   ```

   期望输出包含：`OK: runtime schema valid...`

4. **禁止**将含真实密钥的 `.env` 提交到 Git；仓库内仅保留 `*.env.example`。详见 [`m0/secrets/README.md`](../m0/secrets/README.md)。

## 四、版本钉扎（基线回滚）

安装完成后在目标机上生成一次软件包快照，便于与 Git 标签对应：

```bash
dpkg-query -W -f='${Package} ${Version}\n' | sort > ~/installed-packages.snapshot.txt
```

将策略与快照路径记入你的发布说明；回滚时重装同版 Debian + 使用 [`m0/baseline/packages-debian12.txt`](../m0/baseline/packages-debian12.txt) 再执行 `install.sh`。

## 五、备份占位（可选）

见 [`m0/backup/README.md`](../m0/backup/README.md) 中的 systemd timer 空壳说明。

## 六、Ubuntu / 旧版 Podman 说明

- 若 `podman compose` 不可用，可安装 `podman-compose`（例如 `pip install podman-compose`）或升级 Podman；`sas-m0-compose.service` 内已包含 `podman compose` 与 `podman-compose` 的回退尝试。
- Ubuntu 需启用 **universe** 等源以安装 Podman，具体以发行版文档为准。

## M0 完成检查清单

- [ ] `install.sh` 执行成功，`curl` `/health` 返回 `ok`
- [ ] `nftables` 规则已加载且 SSH 仍可用
- [ ] `validate_config.py` 对「运行时 JSON + 分文件假密钥」校验通过
- [ ] Git 中无真实 `.env` 密钥

M1 及以后将在此基座上增加任务表、Audit、LLM 适配层等，不在 M0 范围。
