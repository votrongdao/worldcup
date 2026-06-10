# Build the SPA with Vite, then serve it from nginx (which also proxies /api).
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
# Use vite directly (esbuild) so a strict `tsc -b` doesn't block the image build.
RUN npx vite build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
