# Sub2API Releases

此仓库提供 Sub2API 的二进制、Docker 镜像与部署文件。应用源码在独立私有仓库维护，本文档及部署文件不包含应用源码。

## 下载与部署

- [下载正式版本](https://github.com/thornywetsui/sub2api-releases/releases/latest)：Linux AMD64/ARM64、macOS AMD64/ARM64、Windows AMD64，附 `checksums.txt`。
- 镜像：`ghcr.io/thornywetsui/sub2api-releases:latest`，支持 Linux AMD64/ARM64。
- 固定版本格式：`1.0.1-upstream.0.2.4`；对应 Release 标签为 `v1.0.1-upstream.0.2.4`。

推荐 Docker Compose：

```sh
curl -fsSL https://raw.githubusercontent.com/thornywetsui/sub2api-releases/main/deploy/docker-deploy.sh -o docker-deploy.sh
bash docker-deploy.sh
docker compose up -d
```

升级容器：

```sh
docker compose pull sub2api
docker compose up -d sub2api
```

二进制安装：

```sh
curl -fsSL https://raw.githubusercontent.com/thornywetsui/sub2api-releases/main/deploy/install.sh -o install.sh
sudo bash install.sh
```

旧版本若仍使用原更新地址，请先手动更新一次容器镜像或下载本仓库的新二进制。迁移版本起，后台版本检查、二进制自动更新与回滚均查询本公开仓库。

## 日志记录器

在「管理设置 → 网关」配置日志记录器，默认关闭。填写接收端 WebSocket 地址及密钥后启用。密钥只写不回显；采集故障不阻断主 API。

## 发布规则

版本为「修改版本号-upstream.上游版本号」。上游每日检查；只有合并、测试、构建及镜像发布全部成功后才公开正式 Release。冲突或失败等待维护者处理，无更新不发布。

本仓库标签只指向公开部署文件，GitHub 自动生成的 Source code 压缩包不包含应用源码。下载程序请使用 `sub2api_...` 资产。原有版权、许可证及适用的源代码提供义务不因仓库可见性调整而改变；许可证随二进制一起分发。
