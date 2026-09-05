FROM node:20-bookworm-slim
ENV npm_config_update_notifier=false
RUN apt-get update && apt-get install --no-install-recommends -y git poppler-utils unzip tar ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts
ARG OPENCODE_VERSION=1.18.25
RUN npm install --global "opencode-ai@${OPENCODE_VERSION}"
COPY . .
RUN npm run build && chmod +x dist/cli.js docker/acceptance.sh
ENTRYPOINT ["bash", "docker/acceptance.sh"]
