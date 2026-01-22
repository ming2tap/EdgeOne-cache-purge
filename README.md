# EdgeOne 缓存清除工具

一个基于 Docker Compose 部署的 EdgeOne 缓存清除 Web 工具，支持配置管理和批量缓存清除。

## ✨ 功能特性

- 🔐 **密码登录保护** - 安全的访问控制
- ⚙️ **配置管理** - 保存和管理多个 EdgeOne 站点配置
- 🌍 **多区域支持** - 支持国内版和国际版
- 🗑️ **多种清除方式** - 支持按 URL、目录、主机名、缓存标签或全部清除
- 🔄 **两种清除方法** - 标记过期（推荐）或直接删除
- 📦 **一键部署** - Docker Compose 快速启动

## 🚀 快速开始

### 前置要求

- Docker
- Docker Compose

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/ming2tap/EdgeOne-cache-purge.git
   cd edgeone-cache-purge
   ```

2. **启动服务**
   ```bash
   docker compose up -d
   ```

3. **访问应用**
   
   打开浏览器访问：http://localhost:5000
   
   - 默认用户名：`admin`
   - 默认密码：`docker-compose.yml` 文件中的 `ADMIN_PASSWORD`（默认为 `admin123`）
   - 测试使用可以使用默认密码 正式部署建议修改

## 📖 使用说明

### 配置管理

1. 登录后进入"配置管理"标签页
2. 点击"添加配置"按钮
3. 填写以下信息：
   - **配置名称**：便于识别的名称（可选）
   - **SecretId**：腾讯云 API 密钥 ID
   - **SecretKey**：腾讯云 API 密钥 Key
   - **站点ID (ZoneId)**：EdgeOne 站点 ID
   - **区域**：选择"国内版"或"国际版"
4. 点击"保存"

### 清除缓存

1. 进入"缓存清除"标签页
2. 选择已保存的配置
3. 选择清除类型：
   - **清除所有缓存** - 清除站点所有缓存
   - **按URL清除** - 输入完整 URL（每行一个）
   - **按目录清除** - 输入目录路径（每行一个）
   - **按主机名清除** - 输入主机名（每行一个）
   - **按缓存标签清除** - 输入缓存标签（每行一个）
4. 选择清除方法：
   - **标记过期**（推荐）- 回源校验，仅当源站有更新时才拉取，对源站带宽影响较小
   - **直接删除** - 直接删除缓存，立即从源站拉取，可能对源站造成压力
5. 点击"提交清除任务"

## ⚙️ 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `SECRET_KEY` | Flask session 加密密钥 | `change-this-secret-key-in-production` |
| `ADMIN_PASSWORD` | 管理员密码 | `admin123` |

 - 测试使用可以使用默认密码 正式部署建议修改

### 数据持久化

数据库文件存储在 `./data` 目录中，通过 Docker volume 挂载实现数据持久化。

## 📝 常用命令

```bash
# 启动服务
docker compose up -d

# 停止服务
docker compose down

# 查看日志
docker compose logs -f

# 重启服务
docker compose restart

# 查看服务状态
docker compose ps
```

## 🔒 安全建议

1. **修改默认密码** - 首次使用请修改管理员密码
2. **使用强密钥** - 生产环境请使用强随机字符串作为 `SECRET_KEY`
3. **配置 HTTPS** - 建议使用反向代理（如 Nginx）配置 HTTPS
4. **限制访问** - 使用防火墙限制访问 IP

## 🛠️ 技术栈

- **后端**: Flask (Python)
- **前端**: HTML + CSS + JavaScript
- **数据库**: SQLite
- **部署**: Docker Compose

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！


