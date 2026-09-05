FROM node:20-bookworm-slim
ENV npm_config_update_notifier=false
RUN apt-get update && apt-get install --no-install-recommends -y git poppler-utils unzip tar ca-certificates python3 python3-pip && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts
ARG OPENCODE_VERSION=1.18.25
RUN npm install --global "opencode-ai@${OPENCODE_VERSION}"
ARG CODEX_VERSION=0.153.4
RUN npm install --global "@openai/codex@${CODEX_VERSION}"
RUN npm install --global @dptech-corp/bohr-cli && python3 -m pip install --break-system-packages huggingface_hub
COPY . .
RUN npm run build && chmod +x dist/cli.js docker/acceptance.sh
ENTRYPOINT ["bash", "docker/acceptance.sh"]
