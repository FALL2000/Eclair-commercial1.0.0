# ÉTAPE 1 : Build de l'application Angular
FROM node:24-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci --ignore-scripts
COPY . .
RUN npm run build -- --configuration=production

# ÉTAPE 2 : Serveur Nginx non-root
FROM nginxinc/nginx-unprivileged:stable-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html

# Le port par défaut de cette image est 8080 au lieu de 80
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
