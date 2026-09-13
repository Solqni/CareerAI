# ============================================================
# CareerAI 前端镜像：多阶段构建（Node 构建 + Nginx 托管）
# ============================================================

# ---------- Stage 1: 构建静态资源 ----------
FROM node:20-alpine AS builder

WORKDIR /app

# 国内服务器构建可通过 --build-arg NPM_REGISTRY=https://registry.npmmirror.com 加速
ARG NPM_REGISTRY=https://registry.npmjs.org

# 先拷依赖清单，利用 Docker 层缓存
COPY package.json package-lock.json ./
RUN npm config set registry ${NPM_REGISTRY} \
    && npm ci

# 拷贝源码并构建（Vite 默认输出到 dist/）
COPY . .

# 前端通过相对路径 /api/v1 访问后端，由 Nginx 反向代理；
# 如需直连其它 API 地址，构建时传入 --build-arg VITE_API_BASE_URL=https://xxx/api/v1
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

# ---------- Stage 2: Nginx 托管 ----------
FROM nginx:1.27-alpine

# 替换默认站点配置（SPA history 路由 + /api 反向代理）
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 拷贝构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
