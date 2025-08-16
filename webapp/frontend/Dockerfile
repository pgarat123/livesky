# ARM-compatible node image
FROM node:20 AS build-stage

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:stable-alpine

COPY --from=build-stage /app/dist /usr/share/nginx/html

# Port 80
EXPOSE 80
