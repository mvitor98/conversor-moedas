FROM nginx:alpine

# Copia a configuração customizada do Nginx com Reverse Proxy
COPY default.conf /etc/nginx/conf.d/default.conf

# Copia os arquivos estáticos do frontend
COPY . /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
